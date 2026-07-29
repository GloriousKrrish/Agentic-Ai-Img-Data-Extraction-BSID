import asyncio
from fastapi import FastAPI, UploadFile, File, WebSocket, WebSocketDisconnect, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import os

from backend.config import GEMINI_API_KEY, MODELS_PRIORITY, PROJECT_ENGINE_DIR
from backend.services.excel_service import read_excel_rows, get_excel_kpis
from backend.services.gemini_service import extract_invoice_from_bytes
from backend.services.ps_runner import get_queue_status, start_parallel_batch, get_realtime_logs
from backend.services.ws_manager import ws_manager

app = FastAPI(
    title="Bridgestone Agentic AI Data Extraction API",
    description="Enterprise Document Intelligence Platform Backend",
    version="2.0.0"
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
    modelsPriority: list[str] = MODELS_PRIORITY

@app.get("/")
def read_root():
    return {
        "platform": "Bridgestone Agentic AI Data Extraction Engine",
        "version": "2.0.0",
        "status": "ONLINE"
    }

@app.get("/api/status")
def get_system_status():
    kpis = get_excel_kpis()
    q_status = get_queue_status()
    return {
        "kpis": kpis,
        "queue": q_status
    }

@app.get("/api/excel-rows")
def get_excel_rows_endpoint():
    return read_excel_rows()

@app.post("/api/extract/single")
async def extract_single_invoice(file: UploadFile = File(...)):
    try:
        content = await file.read()
        mime = file.content_type or "image/jpeg"
        if "pdf" in file.filename.lower():
            mime = "application/pdf"
        result = extract_invoice_from_bytes(content, mime)
        result["fileName"] = file.filename
        
        # Append row into Invoice_data_capture.xlsx
        try:
            import openpyxl
            from backend.config import EXCEL_PATH
            wb = openpyxl.load_workbook(EXCEL_PATH)
            sheet = wb.active
            sheet.append([
                file.filename,
                result.get("customerName", ""),
                result.get("customerMobile", ""),
                result.get("vehicleNumber", ""),
                result.get("size", ""),
                result.get("pattern", ""),
                result.get("dot", ""),
                result.get("cost", ""),
                result.get("totalCost", ""),
                result.get("dealerName", "")
            ])
            wb.save(EXCEL_PATH)
            wb.close()
        except Exception as ex:
            print("Excel append note:", ex)
            
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/batch/start")
def trigger_batch(req: BatchStartRequest):
    return start_parallel_batch(req.numWorkers, req.delaySeconds, req.fileName)

@app.get("/api/logs")
def get_logs():
    return get_realtime_logs()

@app.get("/api/settings")
def get_settings():
    return {
        "geminiApiKey": GEMINI_API_KEY,
        "modelsPriority": MODELS_PRIORITY,
        "engineDir": str(PROJECT_ENGINE_DIR)
    }

@app.post("/api/settings")
def update_settings(req: SettingsUpdateRequest):
    env_path = PROJECT_ENGINE_DIR / ".env"
    with open(env_path, "w", encoding="utf-8") as f:
        f.write(f"GEMINI_API_KEY={req.geminiApiKey.strip()}\n")
    return {"status": "SUCCESS", "message": "Settings saved successfully."}

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await ws_manager.connect(websocket)
    try:
        while True:
            kpis = get_excel_kpis()
            q_status = get_queue_status()
            rows = read_excel_rows()
            logs = get_realtime_logs()
            
            await websocket.send_json({
                "type": "SYNC_UPDATE",
                "kpis": kpis,
                "queue": q_status,
                "recentRows": rows[:10],
                "logs": logs[:10]
            })
            await asyncio.sleep(1.5)
    except WebSocketDisconnect:
        ws_manager.disconnect(websocket)
    except Exception:
        ws_manager.disconnect(websocket)
