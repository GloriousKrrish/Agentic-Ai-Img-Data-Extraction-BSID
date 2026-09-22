import uuid
import time
from typing import Dict, Any, List

class BatchManager:
    """
    v4.2 Batch Processing & Aggregation Engine.
    Models high-volume batch ingestion, status tracking, pause/resume controls, and result aggregation.
    """
    def __init__(self):
        self.batches: Dict[str, Dict[str, Any]] = {}

    def create_batch(self, tenant_id: str, document_files: List[dict]) -> dict:
        batch_id = f"batch-{uuid.uuid4().hex[:8]}"
        batch_record = {
            "batch_id": batch_id,
            "tenant_id": tenant_id,
            "total_documents": len(document_files),
            "completed": 0,
            "failed": 0,
            "waiting_for_review": 0,
            "processing": len(document_files),
            "status": "PROCESSING",
            "created_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            "documents": document_files
        }
        self.batches[batch_id] = batch_record
        return batch_record

    def update_batch_progress(self, batch_id: str, job_status: str):
        if batch_id not in self.batches:
            return
        b = self.batches[batch_id]
        if job_status == "Completed":
            b["completed"] += 1
        elif job_status == "Failed":
            b["failed"] += 1
        elif job_status == "WaitingForReview":
            b["waiting_for_review"] += 1

        b["processing"] = max(0, b["total_documents"] - (b["completed"] + b["failed"] + b["waiting_for_review"]))
        if b["processing"] == 0:
            b["status"] = "COMPLETED" if b["failed"] == 0 else "COMPLETED_WITH_ERRORS"

    def get_batch(self, batch_id: str) -> dict:
        return self.batches.get(batch_id, {})

    def pause_batch(self, batch_id: str) -> bool:
        if batch_id in self.batches:
            self.batches[batch_id]["status"] = "PAUSED"
            return True
        return False

    def resume_batch(self, batch_id: str) -> bool:
        if batch_id in self.batches:
            self.batches[batch_id]["status"] = "PROCESSING"
            return True
        return False

batch_manager = BatchManager()
