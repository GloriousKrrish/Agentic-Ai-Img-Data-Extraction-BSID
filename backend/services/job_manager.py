import os
import io
import json
import uuid
import sqlite3
import threading
import time
from datetime import datetime
from pathlib import Path
import backend.config as config
from backend.config import BASE_DIR, PROJECT_ENGINE_DIR
from backend.services.file_parser import parse_file_content
from backend.services.image_preprocessor import preprocess_image
from backend.services.schema_generator import generate_dynamic_schema
from backend.services.universal_extractor import extract_universal_document
from backend.services.dynamic_exporter import generate_dynamic_excel, generate_dynamic_csv
from backend.services.pipeline_router import determine_pipeline_type

import tempfile

IS_VERCEL = bool(os.getenv("VERCEL") or os.getenv("VERCEL_ENV"))

if IS_VERCEL:
    DB_PATH = Path(tempfile.gettempdir()) / "jobs.sqlite3"
    UPLOADS_DIR = Path(tempfile.gettempdir()) / "uploads"
else:
    try:
        test_file = BASE_DIR / ".write_test"
        test_file.touch()
        test_file.unlink()
        DB_PATH = BASE_DIR / "jobs.sqlite3"
        UPLOADS_DIR = BASE_DIR / "uploads"
    except Exception:
        DB_PATH = Path(tempfile.gettempdir()) / "jobs.sqlite3"
        UPLOADS_DIR = Path(tempfile.gettempdir()) / "uploads"

UPLOADS_DIR.mkdir(parents=True, exist_ok=True)

def normalize_job_status(status: str) -> str:
    s = (status or "").upper().strip()
    if s in ["COMPLETED", "SUCCESS", "DONE"]:
        return "Completed"
    if s in ["FAILED", "ERROR"]:
        return "Failed"
    if s in ["WAITING_FOR_HUMAN_REVIEW", "WAITINGFORREVIEW", "WAITING_FOR_REVIEW", "HITL_REQUIRED"]:
        return "WaitingForReview"
    if s in ["ANALYZING"]:
        return "Analyzing"
    if s in ["EXTRACTING"]:
        return "Extracting"
    if s in ["PREPARING"]:
        return "Preparing"
    if s in ["PREPROCESSING"]:
        return "Preprocessing"
    return status.title() if status else "Analyzing"

class JobManager:
    def __init__(self, db_path: Path = DB_PATH):
        self.db_path = str(db_path)
        self._init_db()

    def _get_connection(self):
        conn = sqlite3.connect(self.db_path, timeout=30.0)
        conn.row_factory = sqlite3.Row
        return conn

    def _init_db(self):
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
            CREATE TABLE IF NOT EXISTS jobs (
                job_id TEXT PRIMARY KEY,
                filename TEXT NOT NULL,
                file_type TEXT NOT NULL,
                file_path TEXT NOT NULL,
                status TEXT NOT NULL,
                current_stage TEXT NOT NULL,
                current_worker TEXT,
                progress REAL NOT NULL DEFAULT 0.0,
                created_at TEXT NOT NULL,
                started_at TEXT,
                completed_at TEXT,
                document_category TEXT,
                document_title TEXT,
                schema_json TEXT,
                rows_json TEXT,
                error TEXT,
                user_schema_id TEXT,
                schema_validation_json TEXT
            )
            """)

            cursor.execute("""
            CREATE TABLE IF NOT EXISTS job_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                job_id TEXT NOT NULL,
                timestamp TEXT NOT NULL,
                level TEXT NOT NULL,
                message TEXT NOT NULL,
                FOREIGN KEY(job_id) REFERENCES jobs(job_id) ON DELETE CASCADE
            )
            """)

            cursor.execute("""
            CREATE TABLE IF NOT EXISTS system_settings (
                key TEXT PRIMARY KEY,
                value TEXT NOT NULL
            )
            """)

            # Phase 4 & v4.1: Add new columns if they don't exist (safe for existing DBs)
            try:
                cursor.execute("ALTER TABLE jobs ADD COLUMN user_schema_id TEXT")
            except Exception:
                pass  # Column already exists
            try:
                cursor.execute("ALTER TABLE jobs ADD COLUMN schema_validation_json TEXT")
            except Exception:
                pass  # Column already exists
            try:
                cursor.execute("ALTER TABLE jobs ADD COLUMN confidence REAL DEFAULT 95.0")
            except Exception:
                pass  # Column already exists
            try:
                cursor.execute("ALTER TABLE jobs ADD COLUMN user_id TEXT DEFAULT 'user_default'")
            except Exception:
                pass  # Column already exists
            try:
                cursor.execute("ALTER TABLE jobs ADD COLUMN attempt_count INTEGER DEFAULT 1")
            except Exception:
                pass  # Column already exists
            try:
                cursor.execute("ALTER TABLE jobs ADD COLUMN failed_at TEXT")
            except Exception:
                pass  # Column already exists
            try:
                cursor.execute("ALTER TABLE jobs ADD COLUMN error_code TEXT")
            except Exception:
                pass  # Column already exists

            conn.commit()

    def get_setting(self, key: str, default: str = "") -> str:
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT value FROM system_settings WHERE key = ?", (key,))
                row = cursor.fetchone()
                if row is not None:
                    return row["value"]
        except Exception:
            pass
        return default

    def set_setting(self, key: str, value: str):
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(
                    "INSERT INTO system_settings (key, value) VALUES (?, ?) ON CONFLICT(key) DO UPDATE SET value = ?",
                    (key, value, value)
                )
                conn.commit()
        except Exception as e:
            print(f"Error setting system setting {key}: {e}")

    def get_api_key(self) -> str:
        # Check SQLite system_settings first if explicitly saved
        db_key = self.get_setting("gemini_api_key", None)
        if db_key is not None:
            return db_key.strip()
        key = (getattr(config, "GEMINI_API_KEY", "") or "").strip()
        if not key:
            key = os.getenv("GEMINI_API_KEY", "").strip()
        return key


    def create_job(self, filename: str, file_bytes: bytes, mime_type: str = "",
                   user_schema_id: str = "", user_schema_json: dict = None,
                   user_id: str = "user_default") -> dict:
        """
        Creates a new extraction job bound to user_id.
        Phase 4: accepts optional user_schema_id (load from store) or user_schema_json (inline).
        v4.1: stores user_id for multi-tenant isolation.
        """
        job_id = f"job-{uuid.uuid4().hex[:8]}"
        created_at = datetime.utcnow().isoformat() + "Z"

        # Phase 4: resolve user_schema
        resolved_schema = None
        resolved_schema_id = user_schema_id or ""
        if user_schema_json:
            try:
                from backend.services.schema_intelligence_engine import schema_intelligence_engine
                resolved_schema = schema_intelligence_engine.parse_schema(user_schema_json, source="inline")
                resolved_schema_id = resolved_schema.schema_id
            except Exception as e:
                print(f"JobManager: Failed to parse inline user_schema_json: {e}")
        elif user_schema_id:
            try:
                from backend.services.schema_store import schema_store
                resolved_schema = schema_store.get_schema(user_schema_id)
            except Exception as e:
                print(f"JobManager: Failed to load schema {user_schema_id}: {e}")

        
        # Determine pipeline route automatically (Single Document vs Batch Dataset)
        routing_info = determine_pipeline_type(file_bytes, filename, mime_type)
        pipeline_type = routing_info["pipeline_type"]
        category = routing_info["category"]
        
        # Save file to disk safely
        file_ext = Path(filename).suffix
        safe_filename = f"{job_id}{file_ext}"
        saved_file_path = UPLOADS_DIR / safe_filename
        with open(saved_file_path, "wb") as f:
            f.write(file_bytes)

        initial_stage = "Ingesting single document" if pipeline_type == "SINGLE_DOCUMENT" else "Enqueued in batch dataset queue"
        worker_label = "Single Doc Engine" if pipeline_type == "SINGLE_DOCUMENT" else "Batch Worker Pool"

        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
            INSERT INTO jobs (
                job_id, filename, file_type, file_path, status, current_stage, 
                current_worker, progress, created_at, document_category, schema_json, rows_json, user_schema_id, user_id
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                job_id, filename, mime_type or "unknown", str(saved_file_path),
                "Analyzing", initial_stage, worker_label,
                0.0, created_at, category, json.dumps([]), json.dumps([]), resolved_schema_id or None, user_id or "user_default"
            ))
            conn.commit()

        if resolved_schema:
            self.add_log(job_id, "INFO", f"Phase 4: Schema-constrained extraction with schema '{resolved_schema.name}' ({len(resolved_schema.fields)} fields)")

        if IS_VERCEL:
            # On Vercel serverless platform, execute synchronously
            self._run_job_pipeline(job_id, user_schema=resolved_schema)
        else:
            # Always execute asynchronously in background thread to avoid blocking API responses
            thread = threading.Thread(target=self._run_job_pipeline, args=(job_id,), kwargs={"user_schema": resolved_schema}, daemon=True)
            thread.start()

        return self.get_job(job_id)

    def add_log(self, job_id: str, level: str, message: str):
        timestamp = datetime.utcnow().strftime("%H:%M:%S")
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(
                    "INSERT INTO job_logs (job_id, timestamp, level, message) VALUES (?, ?, ?, ?)",
                    (job_id, timestamp, level, message)
                )
                conn.commit()
        except Exception as e:
            print(f"Error adding log for {job_id}: {e}")

    def update_job_progress(self, job_id: str, status: str, stage: str, progress: float, **kwargs):
        norm_status = normalize_job_status(status)
        updates = ["status = ?", "current_stage = ?", "progress = ?"]
        params = [norm_status, stage, progress]

        if norm_status in ["Analyzing", "Extracting", "Preparing", "Preprocessing"]:
            if "started_at" not in kwargs:
                kwargs["started_at"] = datetime.utcnow().isoformat() + "Z"

        if norm_status in ["Completed", "Failed", "WaitingForReview"]:
            kwargs["completed_at"] = datetime.utcnow().isoformat() + "Z"

        for key, val in kwargs.items():
            updates.append(f"{key} = ?")
            if isinstance(val, (dict, list)):
                params.append(json.dumps(val))
            else:
                params.append(val)

        params.append(job_id)
        sql = f"UPDATE jobs SET {', '.join(updates)} WHERE job_id = ?"

        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(sql, params)
            conn.commit()

        self.add_log(job_id, "INFO" if norm_status != "Failed" else "ERROR", f"[{norm_status}] Stage: {stage} ({progress:.0f}%)")

    def get_job(self, job_id: str) -> dict:
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM jobs WHERE job_id = ?", (job_id,))
            row = cursor.fetchone()
            if not row:
                return None

            job = dict(row)
            job["status"] = normalize_job_status(job.get("status"))
            job["schema"] = json.loads(job["schema_json"]) if job.get("schema_json") else []
            job["rows"] = json.loads(job["rows_json"]) if job.get("rows_json") else []

            # Phase 4: include schema validation report and user schema ID
            sv_raw = job.get("schema_validation_json")
            job["schemaValidation"] = json.loads(sv_raw) if sv_raw else {}
            job["userSchemaId"] = job.get("user_schema_id") or ""

            cursor.execute("SELECT timestamp, level, message FROM job_logs WHERE job_id = ? ORDER BY id ASC", (job_id,))
            job["logs"] = [dict(log_row) for log_row in cursor.fetchall()]

            return job

    def get_all_jobs(self, limit: int = 50) -> list[dict]:
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM jobs ORDER BY created_at DESC LIMIT ?", (limit,))
            rows = cursor.fetchall()
            result = []
            for r in rows:
                j = dict(r)
                j["status"] = normalize_job_status(j.get("status"))
                j["schema"] = json.loads(j["schema_json"]) if j.get("schema_json") else []
                j["rows"] = json.loads(j["rows_json"]) if j.get("rows_json") else []
                result.append(j)
            return result

    def get_active_jobs(self) -> list[dict]:
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM jobs WHERE status NOT IN ('Completed', 'Failed', 'Cancelled') ORDER BY created_at DESC")
            rows = cursor.fetchall()
            result = []
            for r in rows:
                j = dict(r)
                j["status"] = normalize_job_status(j.get("status"))
                j["schema"] = json.loads(j["schema_json"]) if j.get("schema_json") else []
                j["rows"] = json.loads(j["rows_json"]) if j.get("rows_json") else []
                result.append(j)
            return result

    def delete_job(self, job_id: str) -> bool:
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM job_logs WHERE job_id = ?", (job_id,))
            cursor.execute("DELETE FROM jobs WHERE job_id = ?", (job_id,))
            conn.commit()
            return True

    def clear_all_jobs(self) -> bool:
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM job_logs")
            cursor.execute("DELETE FROM jobs")
            conn.commit()
            return True

    def update_job_row(self, job_id: str, row_index: int, updated_fields: dict) -> dict:
        """
        Updates extracted fields for a specific row in a job (Human-in-the-Loop review).
        Performs in-place modification of SQLite rows JSON payload.
        """
        job = self.get_job(job_id)
        if not job:
            return None

        rows = job.get("rows", [])
        found = False
        for r in rows:
            r_idx = r.get("rowIndex") or r.get("row_index") or 1
            if r_idx == row_index:
                r["fields"] = updated_fields
                r["status"] = "HUMAN_VERIFIED"
                found = True
                break

        if not found and rows:
            # Fallback update first row if index missing
            rows[0]["fields"] = updated_fields
            rows[0]["status"] = "HUMAN_VERIFIED"

        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("UPDATE jobs SET rows_json = ? WHERE job_id = ?", (json.dumps(rows), job_id))
            conn.commit()

        self.add_log(job_id, "INFO", f"Human-in-the-loop: Row {row_index} updated and marked HUMAN_VERIFIED.")
        return self.get_job(job_id)

    def dispatch_webhook(self, job_id: str):
        """Dispatches job completion payload to configured webhook URL if set."""
        webhook_url = self.get_setting("webhook_url", "").strip()
        if not webhook_url:
            return

        job = self.get_job(job_id)
        if not job:
            return

        try:
            import requests
            payload = {
                "event": "job.completed",
                "jobId": job["job_id"],
                "status": job["status"],
                "filename": job["filename"],
                "category": job.get("document_category"),
                "rowsCount": len(job.get("rows", [])),
                "timestamp": datetime.utcnow().isoformat() + "Z"
            }
            res = requests.post(webhook_url, json=payload, timeout=5)
            self.add_log(job_id, "INFO", f"Webhook dispatched to {webhook_url} (HTTP {res.status_code})")
        except Exception as e:
            self.add_log(job_id, "ERROR", f"Webhook delivery error: {e}")


    def _run_job_pipeline(self, job_id: str, user_schema=None):
        job = self.get_job(job_id)
        if not job:
            return

        file_path = Path(job["file_path"])
        filename = job["filename"]

        try:
            if not self.get_api_key():
                raise ValueError("GEMINI_API_KEY is not configured. Please set your Gemini API key in Settings.")

            # 1. Preparing
            self.update_job_progress(job_id, "Preparing", "Ingesting file & detecting format", 10.0)
            if not file_path.exists():
                raise FileNotFoundError(f"Saved file {file_path} not found.")

            with open(file_path, "rb") as f:
                content_bytes = f.read()

            # 2. Preprocessing
            self.update_job_progress(job_id, "Preprocessing", "Parsing file content & deskewing", 25.0)
            parsed = parse_file_content(content_bytes, filename, job.get("file_type", ""))
            
            bytes_to_use = content_bytes
            if parsed.get("file_type") == "image":
                bytes_to_use, _ = preprocess_image(content_bytes)

            # Check if Excel/CSV file contains image URLs
            excel_urls = []
            if parsed.get("file_type") in ["xlsx", "csv"]:
                from backend.services.invoice_engine import detect_url_column_in_excel, process_invoice_document, INVOICE_SEMANTIC_PROMPT_SCHEMA
                excel_urls = detect_url_column_in_excel(content_bytes, filename)

            if excel_urls:
                self.update_job_progress(job_id, "Extracting URLs", f"Found {len(excel_urls)} document links in Excel. Launching Parallel Cognitive AI Employee Pool...", 40.0)
                from backend.agents.supervisor import SupervisorAgent
                from backend.agents.excel_writer_agent import PRIORITY_COLUMNS
                import concurrent.futures
                import threading

                batch_workers = getattr(config, "MAX_WORKERS", 15)
                supervisor = SupervisorAgent(max_workers=batch_workers)
                master_schema = {"documentCategory": "Enterprise Invoice Batch", "fields": PRIORITY_COLUMNS}
                lock = threading.Lock()

                all_extracted_rows = []
                completed_count = 0
                total_urls = len(excel_urls)

                def process_url_task(task_item_tuple):
                    task_idx, task_item = task_item_tuple
                    return supervisor.process_single_task(
                        task=task_item,
                        total_rows=total_urls,
                        task_num=task_idx,
                        schema_info=master_schema,
                        lock=lock,
                        workbook_name=filename
                    )

                with concurrent.futures.ThreadPoolExecutor(max_workers=batch_workers) as executor:
                    futures = [executor.submit(process_url_task, (i + 1, item)) for i, item in enumerate(excel_urls)]
                    for future in concurrent.futures.as_completed(futures):
                        completed_count += 1
                        pct = 40.0 + (completed_count / float(total_urls)) * 50.0
                        self.update_job_progress(job_id, "Extracting", f"Processed {completed_count}/{total_urls} invoices ({pct:.0f}%)", pct)
                        try:
                            res_ctx = future.result()
                            ext_fields = res_ctx.get("extracted_fields", {})
                            r_idx = res_ctx.get("original_row_number", completed_count)
                            task_ser = res_ctx.get("ser_no", completed_count)
                            orig_url = res_ctx.get("original_url", "")
                            ext_fields["serNo"] = task_ser
                            ext_fields["invoiceImageLink"] = orig_url
                            status_str = "COMPLETED" if res_ctx.get("status") in ["SUCCESS", "PARTIAL", "COMPLETED"] else "COMPLETED"
                            all_extracted_rows.append({
                                "rowIndex": r_idx,
                                "fields": ext_fields,
                                "status": status_str,
                                "confidence": res_ctx.get("confidence", 85.0)
                            })
                        except Exception as ex:
                            print(f"Error processing invoice row: {ex}")

                schema = PRIORITY_COLUMNS
                rows = sorted(all_extracted_rows, key=lambda x: x["rowIndex"]) if all_extracted_rows else [{"rowIndex": 1, "fields": {"invoiceImageLink": "No valid documents processed"}, "status": "FAILED"}]
                doc_category = "Enterprise Invoice Batch"
                doc_title = f"Cognitive AI Invoice Batch from {filename}"
            else:
                # Standard single document processing via Agentic Execution Engine (Analyze -> Plan -> Execute -> Validate -> Replan)
                try:
                    self.update_job_progress(job_id, "Agentic Execution", "Analyzing input, generating extraction plan & running agents", 50.0)
                    from backend.services.agentic_engine import agentic_execution_engine
                    
                    def log_cb(level: str, msg: str):
                        self.add_log(job_id, level, msg)

                    agentic_res = agentic_execution_engine.execute_agentic_workflow(
                        bytes_to_use,
                        filename,
                        job.get("file_type", ""),
                        log_callback=log_cb,
                        user_schema=user_schema
                    )

                    schema = agentic_res.get("schema", [])
                    rows = agentic_res.get("rows", [])
                    doc_category = agentic_res.get("documentCategory", "General Document")
                    doc_title = agentic_res.get("documentTitle", "Extracted Document")
                    job_final_status = agentic_res.get("status", "Completed")
                    job_confidence = agentic_res.get("confidence", 95.0)

                    # Phase 4: persist schema validation report if present
                    schema_val = agentic_res.get("schemaValidation", {})
                    if schema_val:
                        try:
                            with self._get_connection() as conn2:
                                conn2.execute(
                                    "UPDATE jobs SET schema_validation_json = ? WHERE job_id = ?",
                                    (json.dumps(schema_val), job_id)
                                )
                                conn2.commit()
                        except Exception:
                            pass

                except Exception as agentic_err:
                    self.add_log(job_id, "WARNING", f"Agentic Planner fallback triggered: {agentic_err}")
                    self.update_job_progress(job_id, "Generating Schema", "Inferring dynamic AI schema with Gemini", 50.0)
                    schema_info = generate_dynamic_schema(
                        bytes_to_use, 
                        job.get("file_type", ""), 
                        text_content=parsed.get("text_content", "")
                    )

                    self.update_job_progress(job_id, "Extracting", "Universal schema-guided data extraction", 75.0)
                    extracted_res = extract_universal_document(
                        bytes_to_use, 
                        schema_info, 
                        job.get("file_type", ""), 
                        text_content=parsed.get("text_content", "")
                    )

                    schema = extracted_res.get("schema", [])
                    rows = extracted_res.get("rows", [])
                    doc_category = extracted_res.get("documentCategory") or schema_info.get("documentCategory", "General Document")
                    doc_title = extracted_res.get("documentTitle") or schema_info.get("documentTitle", "Extracted Document")
                    job_final_status = "Completed"
                    job_confidence = extracted_res.get("confidence", 95.0)

            # 5. Validate extraction output before completing
            has_valid_data = False
            if rows and isinstance(rows, list):
                for r in rows:
                    f = r.get("fields") or {}
                    if any(str(v).strip() for v in f.values() if v and not str(v).startswith("Key Missing")):
                        has_valid_data = True
                        break

            if not has_valid_data or not schema:
                job_final_status = "Failed"
                failure_msg = "Extraction completed but returned 0 valid data fields."
                self.update_job_progress(
                    job_id, "Failed", failure_msg, 100.0,
                    document_category=doc_category,
                    document_title=doc_title,
                    schema_json=schema,
                    rows_json=rows,
                    confidence=0.0,
                    error=failure_msg
                )
                self.add_log(job_id, "ERROR", failure_msg)
            else:
                # 6. Completed or Waiting for Human Review
                self.update_job_progress(
                    job_id, job_final_status, f"Job processing finalized with status: {job_final_status}", 100.0,
                    document_category=doc_category,
                    document_title=doc_title,
                    schema_json=schema,
                    rows_json=rows,
                    confidence=job_confidence
                )
                self.add_log(job_id, "SUCCESS", f"Extraction completed. {len(schema)} columns, {len(rows)} rows.")
                self.dispatch_webhook(job_id)

        except Exception as e:
            err_msg = str(e)
            print(f"Job {job_id} failed: {err_msg}")
            self.update_job_progress(job_id, "Failed", f"Extraction failed: {err_msg}", 100.0, error=err_msg)

    def recover_orphaned_jobs(self) -> int:
        """
        v4.1 Crash Recovery: Recovers jobs left in progress (Analyzing/Extracting) upon server restart.
        """
        recovered_count = 0
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT job_id, status FROM jobs WHERE status IN ('Analyzing', 'Extracting', 'Processing')")
                orphaned = cursor.fetchall()
                for row in orphaned:
                    j_id = row["job_id"]
                    cursor.execute("""
                    UPDATE jobs SET status = 'WaitingForReview', current_stage = 'Process restarted during execution — marked for review', error_code = 'PROCESS_RESTART'
                    WHERE job_id = ?
                    """, (j_id,))
                    recovered_count += 1
                conn.commit()
        except Exception as e:
            print(f"Error during orphaned job recovery: {e}")
        return recovered_count

job_manager = JobManager()
