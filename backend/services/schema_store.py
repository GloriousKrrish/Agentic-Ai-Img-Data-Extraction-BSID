"""
Phase 4: Schema Store — SQLite-backed versioned schema persistence.
Stores ExtractionSchema objects in the existing jobs.sqlite3 database (new tables).
"""
from __future__ import annotations
import json
import os
import sqlite3
import time
from typing import Any, Dict, List, Optional

from backend.agents.schema_models import ExtractionSchema, SchemaVersion

# Reuse the same DB file as the job manager
_DB_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "jobs.sqlite3")


def _get_conn() -> sqlite3.Connection:
    conn = sqlite3.connect(_DB_PATH, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn


def _ensure_tables():
    conn = _get_conn()
    with conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS extraction_schemas (
                schema_id   TEXT PRIMARY KEY,
                name        TEXT NOT NULL,
                version     TEXT NOT NULL DEFAULT '1.0.0',
                domain      TEXT NOT NULL DEFAULT 'custom',
                description TEXT DEFAULT '',
                data        TEXT NOT NULL,
                created_at  TEXT NOT NULL,
                updated_at  TEXT NOT NULL,
                created_by  TEXT DEFAULT 'user',
                tags        TEXT DEFAULT '[]'
            )
        """)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS schema_versions (
                version_id      TEXT PRIMARY KEY,
                schema_id       TEXT NOT NULL,
                version         TEXT NOT NULL,
                diff_summary    TEXT DEFAULT '',
                fields_added    TEXT DEFAULT '[]',
                fields_removed  TEXT DEFAULT '[]',
                fields_modified TEXT DEFAULT '[]',
                snapshot        TEXT NOT NULL,
                created_at      TEXT NOT NULL,
                FOREIGN KEY (schema_id) REFERENCES extraction_schemas(schema_id)
            )
        """)
    conn.close()


# Ensure tables exist at import time
try:
    _ensure_tables()
except Exception as e:
    print(f"SchemaStore: Could not ensure tables: {e}")


class SchemaStore:
    """Persistent SQLite-backed store for ExtractionSchema objects."""

    def __init__(self, db_path: Optional[Any] = None):
        self.db_path = str(db_path) if db_path else _DB_PATH
        self._ensure_tables()

    def _get_conn(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path, check_same_thread=False)
        conn.row_factory = sqlite3.Row
        return conn

    def _ensure_tables(self):
        conn = self._get_conn()
        with conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS extraction_schemas (
                    schema_id   TEXT PRIMARY KEY,
                    name        TEXT NOT NULL,
                    version     TEXT NOT NULL DEFAULT '1.0.0',
                    domain      TEXT NOT NULL DEFAULT 'custom',
                    description TEXT DEFAULT '',
                    data        TEXT NOT NULL,
                    created_at  TEXT NOT NULL,
                    updated_at  TEXT NOT NULL,
                    created_by  TEXT DEFAULT 'user',
                    tags        TEXT DEFAULT '[]'
                )
            """)
            conn.execute("""
                CREATE TABLE IF NOT EXISTS schema_versions (
                    version_id      TEXT PRIMARY KEY,
                    schema_id       TEXT NOT NULL,
                    version         TEXT NOT NULL,
                    diff_summary    TEXT DEFAULT '',
                    fields_added    TEXT DEFAULT '[]',
                    fields_removed  TEXT DEFAULT '[]',
                    fields_modified TEXT DEFAULT '[]',
                    snapshot        TEXT NOT NULL,
                    created_at      TEXT NOT NULL,
                    FOREIGN KEY (schema_id) REFERENCES extraction_schemas(schema_id)
                )
            """)
        conn.close()

    # ------------------------------------------------------------------
    # CRUD
    # ------------------------------------------------------------------
    def save_schema(self, schema: ExtractionSchema) -> ExtractionSchema:
        """
        Insert or replace an ExtractionSchema.
        Also writes a SchemaVersion snapshot on every save.
        """
        now = time.strftime("%Y-%m-%dT%H:%M:%SZ")
        schema = schema.model_copy(update={"updated_at": now})
        data_json = schema.model_dump_json()

        conn = self._get_conn()
        with conn:
            conn.execute("""
                INSERT INTO extraction_schemas
                    (schema_id, name, version, domain, description, data, created_at, updated_at, created_by, tags)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(schema_id) DO UPDATE SET
                    name=excluded.name,
                    version=excluded.version,
                    domain=excluded.domain,
                    description=excluded.description,
                    data=excluded.data,
                    updated_at=excluded.updated_at,
                    created_by=excluded.created_by,
                    tags=excluded.tags
            """, (
                schema.schema_id,
                schema.name,
                schema.version,
                schema.domain,
                schema.description,
                data_json,
                schema.created_at,
                now,
                schema.created_by,
                json.dumps(schema.tags)
            ))

            # Record version snapshot
            from backend.agents.schema_models import SchemaVersion as SV
            import uuid
            conn.execute("""
                INSERT INTO schema_versions
                    (version_id, schema_id, version, diff_summary, fields_added, fields_removed, fields_modified, snapshot, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                f"ver-{uuid.uuid4().hex[:6]}",
                schema.schema_id,
                schema.version,
                "Schema saved",
                "[]",
                "[]",
                "[]",
                data_json,
                now
            ))
        conn.close()
        return schema

    def get_schema(self, schema_id: str) -> Optional[ExtractionSchema]:
        """Retrieve schema by ID. Returns None if not found."""
        conn = self._get_conn()
        row = conn.execute(
            "SELECT data FROM extraction_schemas WHERE schema_id = ?", (schema_id,)
        ).fetchone()
        conn.close()
        if not row:
            return None
        return ExtractionSchema.model_validate_json(row["data"])

    def list_schemas(self) -> List[Dict[str, Any]]:
        """Return summary list of all schemas (without full field data)."""
        conn = self._get_conn()
        rows = conn.execute(
            "SELECT schema_id, name, version, domain, description, created_at, updated_at, created_by, tags FROM extraction_schemas ORDER BY updated_at DESC"
        ).fetchall()
        conn.close()
        result = []
        for row in rows:
            result.append({
                "schema_id": row["schema_id"],
                "name": row["name"],
                "version": row["version"],
                "domain": row["domain"],
                "description": row["description"],
                "created_at": row["created_at"],
                "updated_at": row["updated_at"],
                "created_by": row["created_by"],
                "tags": json.loads(row["tags"] or "[]")
            })
        return result

    def update_schema(self, schema_id: str, updates: Dict[str, Any], previous_schema: Optional[ExtractionSchema] = None) -> Optional[ExtractionSchema]:
        """
        Update a schema and record the diff as a new version entry.
        """
        existing = self.get_schema(schema_id)
        if not existing:
            return None

        # Bump version
        try:
            parts = existing.version.split(".")
            parts[-1] = str(int(parts[-1]) + 1)
            new_version = ".".join(parts)
        except Exception:
            new_version = existing.version + ".1"

        updated = existing.model_copy(update={**updates, "version": new_version})

        # Compute diff
        if previous_schema:
            from backend.services.schema_intelligence_engine import schema_intelligence_engine
            diff = schema_intelligence_engine.schema_diff(previous_schema, updated)
        else:
            diff = SchemaVersion(schema_id=schema_id, version=new_version, diff_summary="Schema updated")

        now = time.strftime("%Y-%m-%dT%H:%M:%SZ")
        data_json = updated.model_dump_json()

        conn = self._get_conn()
        with conn:
            conn.execute("""
                UPDATE extraction_schemas
                SET name=?, version=?, domain=?, description=?, data=?, updated_at=?, tags=?
                WHERE schema_id=?
            """, (
                updated.name, updated.version, updated.domain,
                updated.description, data_json, now,
                json.dumps(updated.tags), schema_id
            ))
            conn.execute("""
                INSERT INTO schema_versions
                    (version_id, schema_id, version, diff_summary, fields_added, fields_removed, fields_modified, snapshot, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                diff.version_id, diff.schema_id, diff.version,
                diff.diff_summary,
                json.dumps(diff.fields_added),
                json.dumps(diff.fields_removed),
                json.dumps(diff.fields_modified),
                data_json, now
            ))
        conn.close()
        return updated

    def delete_schema(self, schema_id: str) -> bool:
        """Delete schema and all its versions. Returns True if deleted."""
        conn = self._get_conn()
        cursor = conn.execute("DELETE FROM extraction_schemas WHERE schema_id = ?", (schema_id,))
        conn.execute("DELETE FROM schema_versions WHERE schema_id = ?", (schema_id,))
        conn.commit()
        deleted = cursor.rowcount > 0
        conn.close()
        return deleted

    # ------------------------------------------------------------------
    # Version history
    # ------------------------------------------------------------------
    def get_schema_versions(self, schema_id: str) -> List[Dict[str, Any]]:
        """Returns version history for a schema."""
        conn = self._get_conn()
        rows = conn.execute(
            "SELECT version_id, schema_id, version, diff_summary, fields_added, fields_removed, fields_modified, created_at FROM schema_versions WHERE schema_id = ? ORDER BY created_at DESC",
            (schema_id,)
        ).fetchall()
        conn.close()
        result = []
        for row in rows:
            result.append({
                "version_id": row["version_id"],
                "schema_id": row["schema_id"],
                "version": row["version"],
                "diff_summary": row["diff_summary"],
                "fields_added": json.loads(row["fields_added"] or "[]"),
                "fields_removed": json.loads(row["fields_removed"] or "[]"),
                "fields_modified": json.loads(row["fields_modified"] or "[]"),
                "created_at": row["created_at"]
            })
        return result

    def get_schema_version_snapshot(self, schema_id: str, version_id: str) -> Optional[ExtractionSchema]:
        """Retrieve a specific version snapshot."""
        conn = self._get_conn()
        row = conn.execute(
            "SELECT snapshot FROM schema_versions WHERE schema_id = ? AND version_id = ?",
            (schema_id, version_id)
        ).fetchone()
        conn.close()
        if not row:
            return None
        return ExtractionSchema.model_validate_json(row["snapshot"])

    # ------------------------------------------------------------------
    # Stats
    # ------------------------------------------------------------------
    def get_schema_stats(self, schema_id: str) -> Dict[str, Any]:
        """Return usage statistics for a schema."""
        conn = self._get_conn()
        version_count = conn.execute(
            "SELECT COUNT(*) as cnt FROM schema_versions WHERE schema_id = ?", (schema_id,)
        ).fetchone()["cnt"]
        conn.close()
        return {
            "schema_id": schema_id,
            "version_count": version_count,
        }


# Singleton
schema_store = SchemaStore()
