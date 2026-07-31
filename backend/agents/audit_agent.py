import os
import csv
import json
from datetime import datetime

class AuditAgent:
    """
    Step 11: Audit Agent
    Maintains structured audit logs (audit_log.csv and audit_log.json).
    Stores: Source URL, Processing Status, Processing Time (s), Confidence, Document Category, Worker ID, Errors, Timestamp.
    """
    def __init__(self, log_csv_path: str = "audit_log.csv", log_json_path: str = "audit_log.json"):
        self.log_csv_path = log_csv_path
        self.log_json_path = log_json_path
        self.logs = []
        self._init_csv()

    def _init_csv(self):
        if not os.path.exists(self.log_csv_path):
            with open(self.log_csv_path, "w", newline="", encoding="utf-8") as f:
                writer = csv.writer(f)
                writer.writerow([
                    "Timestamp", "RowIndex", "SourceURL", "Category", 
                    "Confidence", "Status", "ProcessingTimeSec", "WorkerID", "Error"
                ])

    def log_event(self, row_index: int, source_url: str, category: str, confidence: float, status: str, duration_sec: float, worker_id: str = "Worker-1", error: str = ""):
        timestamp = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")
        entry = {
            "timestamp": timestamp,
            "rowIndex": row_index,
            "sourceUrl": source_url,
            "category": category,
            "confidence": confidence,
            "status": status,
            "durationSec": round(duration_sec, 2),
            "workerId": worker_id,
            "error": error
        }
        self.logs.append(entry)

        # Write to CSV
        with open(self.log_csv_path, "a", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow([
                timestamp, row_index, source_url, category, 
                confidence, status, round(duration_sec, 2), worker_id, error
            ])

        # Write to JSON
        with open(self.log_json_path, "w", encoding="utf-8") as f:
            json.dump(self.logs, f, indent=2)
