import asyncio
import time
import json
from fastapi import FastAPI, UploadFile, File, WebSocket, WebSocketDisconnect, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import Response
from pydantic import BaseModel
import os

import backend.config as config
from backend.services.excel_service import read_excel_rows, get_excel_kpis
from backend.services.gemini_service import extract_invoice_from_bytes
from backend.services.ps_runner import get_queue_status, start_parallel_batch, get_realtime_logs
from backend.services.ws_manager import ws_manager
from backend.services.file_parser import parse_file_content
from backend.services.image_preprocessor import preprocess_image
from backend.services.schema_generator import generate_dynamic_schema
from backend.services.universal_extractor import extract_universal_document
from backend.services.dynamic_exporter import generate_dynamic_excel, generate_dynamic_csv
from backend.services.job_manager import job_manager

app = FastAPI(
    title="Universal AI Document Intelligence Platform Backend",
    description="Enterprise Persistent Job Manager & Document Intelligence Engine",
    version="3.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class BatchStartRequest(BaseModel):
    numWorkers: int = 3
    delaySeconds: int = 8
    fileName: str = "Invoice_data_capture.xlsx"

class SettingsUpdateRequest(BaseModel):
    geminiApiKey: str
    primaryModel: str = "gemini-3.1-flash-lite"
    modelsPriority: list[str] = ["gemini-3.1-flash-lite", "gemini-flash-latest", "gemini-3.5-flash"]

@app.get("/")
def read_root():
    return {
        "platform": "Universal AI Document Intelligence Engine",
        "architecture": "Backend-Owned Persistent Job Manager",
        "version": "3.0.0",
        "status": "ONLINE"
    }

@app.get("/health")
def health_check():
    return {
        "status": "ONLINE",
        "version": "3.0.0",
        "gemini_key_set": bool(config.GEMINI_API_KEY),
        "models_priority": config.MODELS_PRIORITY
    }

@app.post("/api/test-key")
def test_api_key(req: dict):
    """Test a Gemini API key and return its status"""
    import requests as req_lib
    key = req.get("apiKey", "").strip()
    model = req.get("model", "gemini-3.1-flash-lite")
    if not key:
        return {"status": "INVALID", "message": "No API key provided"}
    try:
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={key}"
        res = req_lib.post(url, json={"contents": [{"parts": [{"text": "ping"}]}]}, timeout=15)
        if res.status_code == 200:
            return {"status": "OK", "message": f"Key valid, model {model} responded successfully"}
        elif res.status_code == 429:
            data = res.json()
            msg = data.get("error", {}).get("message", "Quota exhausted")
            return {"status": "QUOTA_EXCEEDED", "message": msg[:300]}
        else:
            data = res.json()
            msg = data.get("error", {}).get("message", res.text)
            return {"status": "INVALID", "message": msg[:300]}
    except Exception as e:
        return {"status": "ERROR", "message": str(e)}

def compute_user_kpis():
    all_jobs = job_manager.get_all_jobs(limit=500)
    total = len(all_jobs)
    processed = sum(1 for j in all_jobs if j.get("status") == "Completed")
    pending = sum(1 for j in all_jobs if j.get("status") in ["Queued", "Analyzing", "Extracting", "Preprocessing", "Preparing"])
    rate = round((processed / total * 100), 1) if total > 0 else 0.0
    return {
        "totalDocuments": total,
        "processedDocuments": processed,
        "pendingDocuments": pending,
        "successRate": rate
    }

def compute_user_dataset():
    all_jobs = job_manager.get_all_jobs(limit=100)
    if not all_jobs:
        return {"schema": [], "rows": []}
    
    schema = []
    rows = []
    seen_keys = set()
    
    for job in all_jobs:
        job_schema = job.get("schema", [])
        job_rows = job.get("rows", [])
        for col in job_schema:
            k = col.get("key")
            if k and k not in seen_keys:
                seen_keys.add(k)
                schema.append({"key": k, "label": col.get("label", k)})
        for r in job_rows:
            rows.append(r)
            
    return {"schema": schema, "rows": rows}

@app.get("/api/status")
def get_system_status():
    active_jobs = job_manager.get_active_jobs()
    return {
        "kpis": compute_user_kpis(),
        "queue": {
            "pendingTasks": len(active_jobs),
            "activeLocks": 0,
            "pendingResults": 0,
            "workers": []
        },
        "activeJobs": active_jobs
    }

@app.get("/api/excel-rows")
def get_excel_rows_endpoint():
    return compute_user_dataset()

@app.post("/api/reset")
def reset_system_state():
    """Clears all jobs, resetting system state to 0 (Queue = 0, Results = 0, Workers = Idle)."""
    job_manager.clear_all_jobs()
    return {"status": "SUCCESS", "message": "System state reset. Queue = 0, Results = 0."}

# =========================================================
# JOB MANAGER REST APIs (PERSISTENT & BACKEND-OWNED)
# =========================================================

@app.post("/api/jobs", status_code=201)
async def create_job_endpoint(file: UploadFile = File(...)):
    """
    Creates a new persistent processing job.
    Returns job_id and status in <50ms while processing executes asynchronously on background worker threads.
    """
    try:
        content = await file.read()
        mime = file.content_type or "application/octet-stream"
        filename = file.filename or "uploaded_document"
        
        job = job_manager.create_job(filename, content, mime)
        return {
            "status": "SUCCESS",
            "jobId": job["job_id"],
            "job": job,
            "message": "Job created and enqueued for background processing."
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/jobs")
def get_all_jobs_endpoint():
    """Returns all past and current persistent jobs."""
    return job_manager.get_all_jobs()

@app.get("/api/jobs/active")
def get_active_jobs_endpoint():
    """Returns all currently running or queued jobs."""
    return job_manager.get_active_jobs()

@app.get("/api/jobs/{job_id}")
def get_job_details_endpoint(job_id: str):
    """Returns full details, progress, stage, schema, rows, and logs for a specific job."""
    job = job_manager.get_job(job_id)
    if not job:
        raise HTTPException(status_code=404, detail=f"Job {job_id} not found.")
    return job

@app.get("/api/jobs/{job_id}/logs")
def get_job_logs_endpoint(job_id: str):
    """Returns live execution logs for a specific job."""
    job = job_manager.get_job(job_id)
    if not job:
        raise HTTPException(status_code=404, detail=f"Job {job_id} not found.")
    return job.get("logs", [])

@app.delete("/api/jobs/{job_id}")
def delete_job_endpoint(job_id: str):
    """Cancels or deletes a job record."""
    success = job_manager.delete_job(job_id)
    if not success:
        raise HTTPException(status_code=404, detail=f"Job {job_id} not found.")
    return {"status": "SUCCESS", "message": f"Job {job_id} deleted."}

@app.get("/api/jobs/{job_id}/download/{export_format}")
def download_job_result_endpoint(job_id: str, export_format: str = "excel"):
    """Downloads extracted output files (Excel, CSV, or JSON) for a job."""
    job = job_manager.get_job(job_id)
    if not job:
        raise HTTPException(status_code=404, detail=f"Job {job_id} not found.")
    
    rows = job.get("rows", [])
    if export_format == "csv":
        csv_data = generate_dynamic_csv(rows)
        return Response(
            content=csv_data,
            media_type="text/csv",
            headers={"Content-Disposition": f"attachment; filename={job['job_id']}_results.csv"}
        )
    elif export_format == "json":
        return Response(
            content=json.dumps(job, indent=2),
            media_type="application/json",
            headers={"Content-Disposition": f"attachment; filename={job['job_id']}_results.json"}
        )
    else: # Excel default
        excel_bytes = generate_dynamic_excel(rows)
        return Response(
            content=excel_bytes,
            media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            headers={"Content-Disposition": f"attachment; filename={job['job_id']}_results.xlsx"}
        )

# Direct Universal Extraction Endpoint (Compatibility)
@app.post("/api/extract/universal")
async def extract_universal(file: UploadFile = File(...)):
    content = await file.read()
    mime = file.content_type or "application/octet-stream"
    filename = file.filename or "uploaded_document"
    
    job = job_manager.create_job(filename, content, mime)
    max_wait = 45 # seconds
    start_t = time.time()
    while time.time() - start_t < max_wait:
        j = job_manager.get_job(job["job_id"])
        if j["status"] in ["Completed", "Failed"]:
            return j
        await asyncio.sleep(0.5)
        
    return job_manager.get_job(job["job_id"])

class DynamicExportRequest(BaseModel):
    items: list[dict]
    format: str = "excel"

@app.post("/api/export/dynamic")
def export_dynamic(req: DynamicExportRequest):
    try:
        if req.format == "csv":
            csv_data = generate_dynamic_csv(req.items)
            return Response(
                content=csv_data,
                media_type="text/csv",
                headers={"Content-Disposition": "attachment; filename=extracted_data.csv"}
            )
        elif req.format == "json":
            return req.items
        else:
            excel_bytes = generate_dynamic_excel(req.items)
            return Response(
                content=excel_bytes,
                media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                headers={"Content-Disposition": "attachment; filename=extracted_data.xlsx"}
            )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/extract/single")
async def extract_single_invoice(file: UploadFile = File(...)):
    return await extract_universal(file)

@app.post("/api/batch/start")
def trigger_batch(req: BatchStartRequest):
    return start_parallel_batch(req.numWorkers, req.delaySeconds, req.fileName)

@app.get("/api/logs")
def get_logs():
    return get_realtime_logs()

@app.get("/api/settings")
def get_settings():
    return {
        "geminiApiKey": config.GEMINI_API_KEY,
        "primaryModel": config.GEMINI_PRIMARY_MODEL,
        "modelsPriority": config.MODELS_PRIORITY,
        "engineDir": str(config.PROJECT_ENGINE_DIR)
    }

@app.post("/api/settings")
def update_settings(req: SettingsUpdateRequest):
    env_path = config.PROJECT_ENGINE_DIR / ".env"
    priority_list = req.modelsPriority if req.modelsPriority else config.MODELS_PRIORITY
    primary = req.primaryModel.strip() if req.primaryModel else priority_list[0]
    
    if primary not in priority_list:
        priority_list.insert(0, primary)
    
    priority_str = ",".join(priority_list)
    
    with open(env_path, "w", encoding="utf-8") as f:
        f.write(f"GEMINI_API_KEY={req.geminiApiKey.strip()}\n")
        f.write(f"GEMINI_PRIMARY_MODEL={primary}\n")
        f.write(f"MODELS_PRIORITY={priority_str}\n")
        
    config.load_config_vars()
    return {"status": "SUCCESS", "message": "Settings saved successfully."}

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await ws_manager.connect(websocket)
    try:
        while True:
            kpis = compute_user_kpis()
            excel_data = compute_user_dataset()
            all_jobs = job_manager.get_all_jobs(limit=10)
            active_jobs = job_manager.get_active_jobs()
            
            await websocket.send_json({
                "type": "SYNC_UPDATE",
                "kpis": kpis,
                "queue": {
                    "pendingTasks": len(active_jobs),
                    "activeLocks": 0,
                    "pendingResults": 0,
                    "workers": []
                },
                "excelData": excel_data,
                "jobs": all_jobs,
                "activeJobs": active_jobs,
                "logs": get_realtime_logs()[:10]
            })
            await asyncio.sleep(1.0)

    except WebSocketDisconnect:
        ws_manager.disconnect(websocket)
    except Exception:
        ws_manager.disconnect(websocket)
