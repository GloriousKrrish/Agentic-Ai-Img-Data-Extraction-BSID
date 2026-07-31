import os
import io
import json
import uuid
import sqlite3
import threading
import time
from datetime import datetime
from pathlib import Path
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
                error TEXT
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
            conn.commit()

    def create_job(self, filename: str, file_bytes: bytes, mime_type: str = "") -> dict:
        job_id = f"job-{uuid.uuid4().hex[:8]}"
        created_at = datetime.utcnow().isoformat() + "Z"
        
        # Determine pipeline route automatically (Single Document vs Batch Dataset)
        routing_info = determine_pipeline_type(file_bytes, filename, mime_type)
        pipeline_type = routing_info["pipeline_type"]
        category = routing_info["category"]
        
        # Save file to disk
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
                current_worker, progress, created_at, document_category, schema_json, rows_json
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                job_id, filename, mime_type or "unknown", str(saved_file_path),
                "Analyzing", initial_stage, worker_label,
                0.0, created_at, category, json.dumps([]), json.dumps([])
            ))
            conn.commit()

        self.add_log(job_id, "INFO", f"Pipeline Router: Assigned to {pipeline_type} ({routing_info['reason']})")

        if pipeline_type == "SINGLE_DOCUMENT" or IS_VERCEL:
            # Single documents execute directly via single document pipeline (NO legacy batch queue, NO worker script, NO row 991)
            self._run_job_pipeline(job_id)
        else:
            # Multi-row batch datasets start asynchronous background processing
            thread = threading.Thread(target=self._run_job_pipeline, args=(job_id,), daemon=True)
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
        updates = ["status = ?", "current_stage = ?", "progress = ?"]
        params = [status, stage, progress]

        if status == "Analyzing" or status == "Extracting":
            if "started_at" not in kwargs:
                kwargs["started_at"] = datetime.utcnow().isoformat() + "Z"

        if status == "Completed" or status == "Failed":
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

        self.add_log(job_id, "INFO" if status != "Failed" else "ERROR", f"[{status}] Stage: {stage} ({progress:.0f}%)")

    def get_job(self, job_id: str) -> dict:
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM jobs WHERE job_id = ?", (job_id,))
            row = cursor.fetchone()
            if not row:
                return None
            
            job = dict(row)
            job["schema"] = json.loads(job["schema_json"]) if job.get("schema_json") else []
            job["rows"] = json.loads(job["rows_json"]) if job.get("rows_json") else []
            
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

    def _run_job_pipeline(self, job_id: str):
        job = self.get_job(job_id)
        if not job:
            return

        file_path = Path(job["file_path"])
        filename = job["filename"]

        try:
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
                
                supervisor = SupervisorAgent(max_workers=10)
                master_schema = {"documentCategory": "Enterprise Invoice Batch", "fields": PRIORITY_COLUMNS}
                
                all_extracted_rows = []
                completed_count = 0
                total_urls = len(excel_urls)
                
                import concurrent.futures
                def process_url_task(task_item):
                    u = task_item["url"]
                    r_idx = task_item.get("rowIndex", 1)
                    return supervisor.process_single_task({"url": u, "rowIndex": r_idx}, master_schema, f"Worker-{(r_idx % 10) + 1}")
                
                with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
                    futures = [executor.submit(process_url_task, item) for item in excel_urls]
                    for future in concurrent.futures.as_completed(futures):
                        completed_count += 1
                        pct = 40.0 + (completed_count / float(total_urls)) * 50.0
                        self.update_job_progress(job_id, "Extracting", f"Processed {completed_count}/{total_urls} invoices ({pct:.0f}%)", pct)
                        try:
                            res = future.result()
                            if res["success"]:
                                res_fields = res["fields"]
                                res_fields["invoiceImageLink"] = res["url"]
                                all_extracted_rows.append({
                                    "rowIndex": res["rowIndex"],
                                    "fields": res_fields,
                                    "status": res.get("status", "COMPLETED"),
                                    "confidence": res.get("confidence", 95.0)
                                })
                        except Exception as ex:
                            print(f"Error processing invoice row: {ex}")

                schema = PRIORITY_COLUMNS
                rows = sorted(all_extracted_rows, key=lambda x: x["rowIndex"]) if all_extracted_rows else [{"rowIndex": 1, "fields": {"invoiceImageLink": "No valid documents processed"}, "status": "FAILED"}]
                doc_category = "Enterprise Invoice Batch"
                doc_title = f"Cognitive AI Invoice Batch from {filename}"
            else:
                # Standard single document processing
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

            # 5. Writing Excel
            self.update_job_progress(
                job_id, "Writing Excel", "Generating dynamic Excel and CSV outputs", 90.0,
                document_category=doc_category,
                document_title=doc_title,
                schema_json=schema,
                rows_json=rows
            )
            
            time.sleep(0.5) # Brief pause for state sync

            # 6. Completed
            self.update_job_progress(
                job_id, "Completed", "Job processing completed successfully", 100.0,
                document_category=doc_category,
                document_title=doc_title,
                schema_json=schema,
                rows_json=rows
            )
            self.add_log(job_id, "SUCCESS", f"Extraction completed. {len(schema)} columns, {len(rows)} rows.")

        except Exception as e:
            err_msg = str(e)
            print(f"Job {job_id} failed: {err_msg}")
            self.update_job_progress(job_id, "Failed", f"Extraction failed: {err_msg}", 100.0, error=err_msg)

job_manager = JobManager()
