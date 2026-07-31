import time
import concurrent.futures
from pathlib import Path
import backend.config as config

from backend.agents.workbook_agent import WorkbookAgent
from backend.agents.downloader_agent import DownloaderAgent
from backend.agents.image_quality_agent import ImageQualityAgent
from backend.agents.image_enhancer_agent import ImageEnhancerAgent
from backend.agents.ocr_agent import OCRAgent
from backend.agents.vision_ai_agent import VisionAIAgent
from backend.agents.entity_resolver_agent import BusinessEntityResolverAgent
from backend.agents.validation_agent import ValidationAgent
from backend.agents.reflection_agent import ReflectionAgent
from backend.agents.excel_writer_agent import ExcelWriterAgent, PRIORITY_COLUMNS
from backend.agents.audit_agent import AuditAgent
from backend.services.cache_service import cache_service

class SupervisorAgent:
    """
    Supervisor Agent (Master Cognitive Orchestrator)
    
    Orchestrates the cognitive multi-pass pipeline:
    - Pass 1: Image Quality Assessment & Adaptive Flags
    - Pass 2: Dual Printed & Handwritten OCR Extraction
    - Pass 3: Layout Analysis & Business Entity Resolution
    - Pass 4: Format Normalization
    - Pass 5: Validation & Math Sanity Review
    - Pass 6: Reflection Review Agent (Human Operator Lens)
    - Pass 7: Ordered Resilient Excel Output Writer
    
    Uses pipelined parallel execution, smart caching, and strict row order preservation.
    """
    def __init__(self, max_workers: int = None):
        self.max_workers = max_workers or config.MAX_WORKERS
        self.workbook_agent = WorkbookAgent()
        self.downloader_agent = DownloaderAgent()
        self.quality_agent = ImageQualityAgent()
        self.enhancer_agent = ImageEnhancerAgent()
        self.ocr_agent = OCRAgent()
        self.vision_agent = VisionAIAgent()
        self.resolver_agent = BusinessEntityResolverAgent()
        self.validation_agent = ValidationAgent()
        self.reflection_agent = ReflectionAgent()

    def process_single_task(self, task: dict, schema_info: dict, worker_id: str) -> dict:
        t0 = time.time()
        url = task["url"]
        row_idx = task["rowIndex"]

        # 1. Download Document Image (with Smart Cache)
        cached_dl = cache_service.get_download(url)
        if cached_dl:
            f_res = cached_dl
        else:
            f_res = self.downloader_agent.fetch(url, max_retries=config.RETRY_COUNT)
            if f_res["success"]:
                cache_service.set_download(url, f_res["bytes"], f_res["mime_type"])

        if not f_res.get("success"):
            return {
                "rowIndex": row_idx,
                "url": url,
                "success": False,
                "error": f_res.get("error", "Download failed"),
                "duration": time.time() - t0,
                "worker_id": worker_id
            }

        doc_bytes = f_res["bytes"]
        mime_type = f_res["mime_type"]

        # Pass 1: Image Quality Assessment & Adaptive Preprocessing
        quality_metrics = self.quality_agent.analyze_image_quality(doc_bytes, mime_type)
        enhanced_bytes = self.enhancer_agent.enhance(doc_bytes, mime_type)

        # Pass 2: Dual Printed & Handwritten OCR Extraction
        ocr_res = self.ocr_agent.extract_text(enhanced_bytes, f"doc_{row_idx}", mime_type)
        raw_ocr_text = ocr_res.get("text_content", "")

        # Pass 3: Layout Section Analysis & Business Entity Resolution
        doc_category = self.resolver_agent.classify_document(raw_ocr_text)

        # Check AI Response Cache
        cached_ai = cache_service.get_ai_response(raw_ocr_text[:100], enhanced_bytes)
        if cached_ai:
            vision_res = cached_ai
        else:
            vision_res = self.vision_agent.extract_with_vision(enhanced_bytes, schema_info, mime_type, text_content=raw_ocr_text)
            cache_service.set_ai_response(raw_ocr_text[:100], enhanced_bytes, vision_res)

        raw_extracted = vision_res.get("extractedFields", {})
        if not raw_extracted and vision_res.get("rows"):
            raw_extracted = vision_res["rows"][0].get("fields", {})

        # Pass 4 & 5: Business Entity Resolution & Validation
        resolved_fields = self.resolver_agent.resolve_entities(raw_ocr_text, raw_extracted)
        resolved_fields["invoiceImageLink"] = url

        val_res = self.validation_agent.validate_record(resolved_fields)

        # Pass 6: Reflection Review Agent (Human Operator Lens)
        ref_res = self.reflection_agent.reflect_and_review(val_res.get("fields", resolved_fields), confidence=val_res["confidence"])
        final_fields = ref_res.get("fields", resolved_fields)
        final_confidence = ref_res["confidence"]

        # Compute Status
        if final_confidence >= 85.0:
            status = "COMPLETED"
        elif final_confidence >= 70.0:
            status = "REVIEW_REQUIRED"
        else:
            status = "LOW_CONFIDENCE"

        return {
            "rowIndex": row_idx,
            "url": url,
            "success": True,
            "category": doc_category,
            "confidence": final_confidence,
            "status": status,
            "warnings": val_res.get("warnings", []) + ref_res.get("reflection_logs", []),
            "fields": final_fields,
            "duration": time.time() - t0,
            "worker_id": worker_id
        }

    def execute_pipeline(self, input_path: str, output_path: str) -> dict:
        print("\n=========================================================================")
        print(">>> ENTERPRISE COGNITIVE MULTI-PASS AI DATA ENTRY EMPLOYEE PIPELINE")
        print("=========================================================================\n")

        input_file = Path(input_path)
        if not input_file.exists():
            print(f"[FAIL] Input file '{input_path}' does not exist!")
            return {"success": False, "error": "File not found"}

        excel_writer = ExcelWriterAgent(output_path)
        audit_agent = AuditAgent()

        # STEP 1: Workbook Agent
        print(f"[STEP 1] Workbook Agent: Loading & analyzing '{input_file.name}'...")
        file_bytes = input_file.read_bytes()
        analysis = self.workbook_agent.analyze_workbook(file_bytes, input_file.name)
        tasks = analysis["tasks"]

        if not tasks:
            print(f"  [!] Direct single document file execution...")
            f_res = {"bytes": file_bytes, "mime_type": "image/jpeg" if input_file.suffix.lower() in ['.png', '.jpg', '.jpeg'] else "application/pdf"}
            enhanced_bytes = self.enhancer_agent.enhance(file_bytes, f_res["mime_type"])
            ocr_res = self.ocr_agent.extract_text(enhanced_bytes, input_file.name, f_res["mime_type"])
            
            schema_info = {"documentCategory": "Invoice Document", "fields": PRIORITY_COLUMNS}
            vision_res = self.vision_agent.extract_with_vision(enhanced_bytes, schema_info, f_res["mime_type"], text_content=ocr_res["text_content"])
            raw_extracted = vision_res.get("extractedFields", {}) or (vision_res["rows"][0].get("fields", {}) if vision_res.get("rows") else {})
            
            resolved_fields = self.resolver_agent.resolve_entities(ocr_res["text_content"], raw_extracted)
            val_res = self.validation_agent.validate_record(resolved_fields)
            ref_res = self.reflection_agent.reflect_and_review(val_res["fields"], val_res["confidence"])
            
            excel_writer.write_row_incremental(PRIORITY_COLUMNS, 1, ref_res["fields"], confidence=ref_res["confidence"], status="COMPLETED")
            audit_agent.log_event(1, input_file.name, "Single Invoice", ref_res["confidence"], "SUCCESS", 1.5, "Worker-1")
            return {"success": True, "processed": 1}

        print(f"  -> Discovered URL column '{analysis['url_column']}' with {len(tasks)} document tasks.\n")

        master_schema = {"documentCategory": "Enterprise Invoice Batch", "fields": PRIORITY_COLUMNS}
        excel_writer.init_workbook(PRIORITY_COLUMNS)

        # Parallel Pipelined Worker Pool Execution (Row Order Preserved)
        print(f"[EXECUTING] Launching {self.max_workers} Cognitive Workers with Pipelined Concurrency...")
        print("-------------------------------------------------------------------------")

        total_tasks = len(tasks)
        results_map = {}

        with concurrent.futures.ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            future_to_task = {
                executor.submit(self.process_single_task, task, master_schema, f"Worker-{(idx % self.max_workers) + 1}"): task 
                for idx, task in enumerate(tasks)
            }

            for completed_count, future in enumerate(concurrent.futures.as_completed(future_to_task), start=1):
                task = future_to_task[future]
                row_idx = task["rowIndex"]
                pct = (completed_count / float(total_tasks)) * 100.0

                try:
                    res = future.result()
                    results_map[row_idx] = res
                    if res["success"]:
                        audit_agent.log_event(row_idx, res["url"], res["category"], res["confidence"], res["status"], res["duration"], res["worker_id"])
                        print(f"[{completed_count}/{total_tasks}] ({pct:5.1f}%) Row #{row_idx}: [{res['status']}] Conf: {res['confidence']}% | Worker: {res['worker_id']}")
                    else:
                        excel_writer.record_failed_row(row_idx, res["url"], res.get("error", "Unknown Error"))
                        audit_agent.log_event(row_idx, res["url"], "Unknown", 0.0, "FAILED", res["duration"], res["worker_id"], res.get("error", ""))
                        print(f"[{completed_count}/{total_tasks}] ({pct:5.1f}%) Row #{row_idx}: [FAILED] {res.get('error')} | Worker: {res['worker_id']}")

                except Exception as e:
                    err_msg = str(e)
                    excel_writer.record_failed_row(row_idx, task["url"], err_msg)
                    audit_agent.log_event(row_idx, task["url"], "Unknown", 0.0, "FAILED", 0.0, "Worker-1", err_msg)
                    print(f"[{completed_count}/{total_tasks}] ({pct:5.1f}%) Row #{row_idx}: [EXCEPT] {err_msg}")

        # Write rows in EXACT input workbook row order
        print("\n[WRITING EXCEL] Writing output rows in exact input row order...")
        for task in tasks:
            row_idx = task["rowIndex"]
            res = results_map.get(row_idx)
            if res and res.get("success"):
                excel_writer.write_row_incremental(
                    PRIORITY_COLUMNS, 
                    row_idx, 
                    res["fields"], 
                    confidence=res["confidence"], 
                    status=res["status"]
                )

        print("-------------------------------------------------------------------------")
        print(f"[COMPLETED] Output Excel workbook saved -> '{excel_writer.output_path}'")
        return {"success": True, "processed": len(results_map)}
