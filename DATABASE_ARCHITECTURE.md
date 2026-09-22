# Database Architecture & Migration Strategy (v4.1)

## Architecture Layout

```
Development / Local:
SQLite WAL Mode (jobs.sqlite3) with 30s timeout & thread local connections

Production:
PostgreSQL Transactional Relational Database Cluster (PostgreSQL 15+)
```

---

## Migration & Version Control Strategy

All schema changes use versioned SQL scripts or Alembic migrations:

* `001_initial_schema.sql`: Initial `jobs`, `job_logs`, `system_settings` tables.
* `002_add_v41_user_and_recovery_columns.sql`: `ALTER TABLE jobs ADD COLUMN user_id`, `attempt_count`, `failed_at`, `error_code`.

---

## Transaction & Atomic Commit Strategy

Job updates execute atomically within single database transactions:

```python
with self._get_connection() as conn:
    cursor = conn.cursor()
    cursor.execute("UPDATE jobs SET status = ?, rows_json = ? WHERE job_id = ?", (status, rows, job_id))
    conn.commit()
```

If an exception occurs, changes roll back cleanly (`ROLLBACK`), preventing partial results or state corruption.
