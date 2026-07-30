import asyncio
from fastapi import FastAPI, UploadFile, File, WebSocket, WebSocketDisconnect, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import os

import backend.config as config
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
    primaryModel: str = "gemini-3.5-flash"
    modelsPriority: list[str] = ["gemini-3.5-flash", "gemini-2.5-flash", "gemini-2.5-flash-lite", "gemini-3.1-flash-lite", "gemini-1.5-flash"]


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

from fastapi.responses import Response
from backend.services.file_parser import parse_file_content
from backend.services.image_preprocessor import preprocess_image
from backend.services.schema_generator import generate_dynamic_schema
from backend.services.universal_extractor import extract_universal_document
from backend.services.dynamic_exporter import generate_dynamic_excel, generate_dynamic_csv

@app.post("/api/extract/universal")
async def extract_universal(file: UploadFile = File(...)):
    try:
        content = await file.read()
        mime = file.content_type or "application/octet-stream"
        file_name = file.filename or "uploaded_document"
        
        # 1. Parse File Content
        parsed = parse_file_content(content, file_name, mime)
        
        # 2. Image Preprocessing (if applicable)
        file_bytes_to_use = content
        if parsed.get("file_type") == "image":
            file_bytes_to_use, _ = preprocess_image(content)
            
        # 3. Dynamic Schema Inference via Gemini AI
        schema_info = generate_dynamic_schema(
            file_bytes_to_use, 
            mime, 
            text_content=parsed.get("text_content", "")
        )
        
        # 4. Universal Schema-Guided Extraction
        extracted_result = extract_universal_document(
            file_bytes_to_use, 
            schema_info, 
            mime, 
            text_content=parsed.get("text_content", "")
        )
        extracted_result["fileName"] = file_name
        extracted_result["fileType"] = parsed.get("file_type", "unknown")
        
        return extracted_result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

class DynamicExportRequest(BaseModel):
    items: list[dict]
    format: str = "excel" # excel | csv | json

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
        else: # Excel default
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
            kpis = get_excel_kpis()
            q_status = get_queue_status()
            excel_data = read_excel_rows()
            await websocket.send_json({
                "type": "SYNC_UPDATE",
                "kpis": kpis,
                "queue": q_status,
                "excelData": excel_data,
                "recentRows": excel_data.get("rows", [])[:10],
                "logs": logs[:10]
            })
            await asyncio.sleep(1.5)

    except WebSocketDisconnect:
        ws_manager.disconnect(websocket)
    except Exception:
        ws_manager.disconnect(websocket)
