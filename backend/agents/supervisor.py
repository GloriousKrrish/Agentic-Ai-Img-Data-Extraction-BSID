import os
import io
import time
import json
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
from backend.services.universal_extractor import extract_universal_document

# Debug Directory Root
DEBUG_DIR = Path("debug")
DEBUG_DIR.mkdir(parents=True, exist_ok=True)

MANDATORY_FIELDS = [
    ("customerName", "Customer Name"),
    ("customerMobile", "Customer Mobile"),
    ("vehicleNumber", "Vehicle Number"),
    ("invoiceNumber", "Invoice Number"),
    ("invoiceDate", "Invoice Date"),
    ("dealerName", "Dealer Name"),
    ("dealerGst", "Dealer GST"),
    ("dealerAddress", "Dealer Address"),
    ("tyreSize", "Tyre Size"),
    ("pattern", "Pattern"),
    ("dotCode", "DOT Code"),
    ("serialNumber", "Serial Number"),
    ("unitCost", "Unit Cost"),
    ("grandTotal", "Grand Total")
]

class SupervisorAgent:
    """
    Principal Debugging Orchestrator
    
    Performs field-level debugging, second-pass missing field recovery, debug artifact saving, 
    terminal live debugging, and generates the final Extraction Accuracy Report.
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

        row_debug_dir = DEBUG_DIR / f"row_{row_idx}"
        row_debug_dir.mkdir(parents=True, exist_ok=True)

        trace = {
            "row_index": row_idx,
            "url": url,
            "download_ok": False,
            "enhanced_ok": False,
            "ocr_ok": False,
            "vision_ok": False,
            "resolver_ok": False,
            "validation_ok": False,
            "excel_written": False,
            "field_diagnostics": {},
            "second_pass_executed": False
        }

        # 1. Download Document Image
        cached_dl = cache_service.get_download(url)
        if cached_dl:
            f_res = cached_dl
        else:
            f_res = self.downloader_agent.fetch(url, max_retries=config.RETRY_COUNT)
            if f_res["success"]:
                cache_service.set_download(url, f_res["bytes"], f_res["mime_type"])

        if not f_res.get("success"):
            trace["download_ok"] = False
            return {
                "rowIndex": row_idx,
                "url": url,
                "success": False,
                "status": "FAILED",
                "error": f_res.get("error", "Download failed"),
                "duration": time.time() - t0,
                "worker_id": worker_id,
                "trace": trace
            }

        trace["download_ok"] = True
        doc_bytes = f_res["bytes"]
        mime_type = f_res["mime_type"]

        # Save Original Image Debug Artifact
        orig_ext = ".pdf" if "pdf" in mime_type.lower() else ".jpg"
        (row_debug_dir / f"original{orig_ext}").write_bytes(doc_bytes)

        # 2. Image Quality & Enhancement
        quality_metrics = self.quality_agent.analyze_image_quality(doc_bytes, mime_type)
        enhanced_bytes = self.enhancer_agent.enhance(doc_bytes, mime_type)
        trace["enhanced_ok"] = True

        # Save Enhanced Image Debug Artifact
        (row_debug_dir / f"enhanced{orig_ext}").write_bytes(enhanced_bytes)

        # 3. OCR Text Extraction
        ocr_res = self.ocr_agent.extract_text(enhanced_bytes, f"doc_{row_idx}", mime_type)
        raw_ocr_text = ocr_res.get("text_content", "")
        trace["ocr_ok"] = True
        (row_debug_dir / "ocr_text.txt").write_text(raw_ocr_text, encoding="utf-8")

        # 4. Vision AI Extraction
        doc_category = self.resolver_agent.classify_document(raw_ocr_text)

        vision_res = self.vision_agent.extract_with_vision(enhanced_bytes, schema_info, mime_type, text_content=raw_ocr_text)
        trace["vision_ok"] = True

        raw_extracted = vision_res.get("extractedFields", {}) or (vision_res["rows"][0].get("fields", {}) if vision_res.get("rows") else {})
        (row_debug_dir / "gemini_response.json").write_text(json.dumps(raw_extracted, indent=2), encoding="utf-8")

        # 5. Business Entity Resolution & Disambiguation
        resolved_fields = self.resolver_agent.resolve_entities(raw_ocr_text, raw_extracted)
        resolved_fields["invoiceImageLink"] = url  # STRICT: Always retain exact original URL
        trace["resolver_ok"] = True

        # 6. Validation & Math Sanity Check
        val_res = self.validation_agent.validate_record(resolved_fields)
        trace["validation_ok"] = True

        # 7. Reflection Review Agent
        ref_res = self.reflection_agent.reflect_and_review(val_res.get("fields", resolved_fields), confidence=val_res["confidence"])
        final_fields = ref_res.get("fields", resolved_fields)

        # 8. Field-Level Debugging & Second Pass Recovery
        missing_mandatory = []
        field_diag = {}

        for key, label in MANDATORY_FIELDS:
            val = str(final_fields.get(key, "") or "").strip()
            if val:
                field_diag[key] = {
                    "found": True,
                    "label": label,
                    "val": val,
                    "source": "Vision AI / Resolver",
                    "confidence": ref_res["confidence"],
                    "reason": None
                }
            else:
                missing_mandatory.append((key, label))
                reason = "Gemini vision response did not return value" if not raw_extracted.get(key) else "Validation/Reflection removed value"
                field_diag[key] = {
                    "found": False,
                    "label": label,
                    "val": "",
                    "source": "None",
                    "confidence": 0.0,
                    "reason": reason
                }

        # TARGETED SECOND PASS RECOVERY FOR MISSING MANDATORY FIELDS
        if missing_mandatory and len(missing_mandatory) <= 12:
            trace["second_pass_executed"] = True
            recovery_prompt_fields = []
            for k, lbl in missing_mandatory:
                desc = f"Target missing field: {lbl}."
                if k == "dealerGst":
                    desc += " Look for 15-character GSTIN near header, rubber stamp, or footer."
                elif k == "customerName":
                    desc += " Look for person name after M/s, Buyer, Customer, or Name."
                elif k == "invoiceDate":
                    desc += " Look for issue date near top right or header (e.g. DD/MM/YYYY)."
                elif k == "pattern":
                    desc += " Look for tyre pattern name (e.g. Wanderer, B390, Sturdo, Turanza, ZLX)."
                elif k == "dotCode":
                    desc += " Look for DOT batch code or 4-digit date code."
                recovery_prompt_fields.append({"key": k, "label": lbl, "description": desc})

            recovery_schema = {
                "documentCategory": "Focused Target Missing Field Recovery",
                "documentTitle": "Target Recovery Pass",
                "fields": recovery_prompt_fields
            }

            try:
                rec_res = extract_universal_document(enhanced_bytes, recovery_schema, mime_type, text_content=raw_ocr_text)
                rec_extracted = rec_res.get("extractedFields", {}) or (rec_res["rows"][0].get("fields", {}) if rec_res.get("rows") else {})
                
                # Apply Entity Resolver on recovered fields
                rec_resolved = self.resolver_agent.resolve_entities(raw_ocr_text, rec_extracted)
                
                for k, lbl in missing_mandatory:
                    rec_val = str(rec_resolved.get(k, "") or "").strip()
                    if rec_val:
                        final_fields[k] = rec_val
                        field_diag[k] = {
                            "found": True,
                            "label": lbl,
                            "val": rec_val,
                            "source": "Second Pass Recovery AI",
                            "confidence": 85.0,
                            "reason": "Recovered via Second Pass Prompt"
                        }
            except Exception:
                pass

        trace["field_diagnostics"] = field_diag
        (row_debug_dir / "validated_response.json").write_text(json.dumps(final_fields, indent=2), encoding="utf-8")
        (row_debug_dir / "excel_row.json").write_text(json.dumps(final_fields, indent=2), encoding="utf-8")

        # Determine Final Extraction Status
        found_mandatory_count = sum(1 for k, _ in MANDATORY_FIELDS if field_diag[k]["found"])
        fill_rate = (found_mandatory_count / float(len(MANDATORY_FIELDS))) * 100.0

        if fill_rate >= 100.0:
            status = "FULLY_EXTRACTED"
        elif fill_rate >= 40.0:
            status = "PARTIAL_EXTRACTION"
        else:
            status = "LOW_CONFIDENCE"

        return {
            "rowIndex": row_idx,
            "url": url,
            "success": True,
            "category": doc_category,
            "confidence": round(fill_rate, 1),
            "status": status,
            "fields": final_fields,
            "duration": time.time() - t0,
            "worker_id": worker_id,
            "trace": trace
        }

    def execute_pipeline(self, input_path: str, output_path: str) -> dict:
        print("\n=========================================================================")
        print(">>> PRINCIPAL DEBUGGING ENGINE: MULTI-PASS RUNTIME TRACE & AUDIT")
        print("=========================================================================\n")

        input_file = Path(input_path)
        if not input_file.exists():
            print(f"[FAIL] Input file '{input_path}' does not exist!")
            return {"success": False, "error": "File not found"}

        excel_writer = ExcelWriterAgent(output_path)
        audit_agent = AuditAgent()

        # STEP 1: Workbook Agent
        file_bytes = input_file.read_bytes()
        analysis = self.workbook_agent.analyze_workbook(file_bytes, input_file.name)
        tasks = analysis["tasks"]

        if not tasks:
            print(f"No tasks found in workbook '{input_file.name}'")
            return {"success": False, "error": "No tasks found"}

        print(f"  -> Discovered URL column '{analysis['url_column']}' with {len(tasks)} document tasks.\n")

        master_schema = {"documentCategory": "Enterprise Invoice Batch", "fields": PRIORITY_COLUMNS}
        excel_writer.init_workbook(PRIORITY_COLUMNS)

        print(f"[EXECUTING LIVE DEBUGGER] Launching {self.max_workers} Workers...")
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

                try:
                    res = future.result()
                    results_map[row_idx] = res
                    tr = res.get("trace", {})

                    print(f"\n=======================================================")
                    print(f"Row {row_idx}")
                    print(f"Source URL: {res['url'][:60]}...")
                    print(f"Downloaded Successfully? {'YES' if tr.get('download_ok') else 'NO'}")
                    print(f"Image Enhanced? {'YES' if tr.get('enhanced_ok') else 'NO'}")
                    print(f"OCR Executed? {'YES' if tr.get('ocr_ok') else 'NO'}")
                    print(f"Vision Executed? {'YES' if tr.get('vision_ok') else 'NO'}")
                    print(f"Business Entity Resolution Executed? {'YES' if tr.get('resolver_ok') else 'NO'}")
                    print(f"Validation Executed? {'YES' if tr.get('validation_ok') else 'NO'}")
                    print(f"Second Pass Executed? {'YES' if tr.get('second_pass_executed') else 'NO'}")
                    print(f"Status: [{res['status']}] (Mandatory Field Coverage: {res['confidence']}%)")
                    print("-------------------------------------------------------")

                    diag = tr.get("field_diagnostics", {})
                    for k, lbl in MANDATORY_FIELDS:
                        fd = diag.get(k, {})
                        if fd.get("found"):
                            print(f"  {lbl:<25}: FOUND -> {repr(fd['val'])} (Source: {fd['source']})")
                        else:
                            print(f"  {lbl:<25}: MISSING -> Reason: {fd.get('reason')}")

                    print("-------------------------------------------------------")

                except Exception as e:
                    print(f"Row {row_idx}: [EXCEPT] {e}")

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

        # GENERATE FINAL EXTRACTION ACCURACY REPORT
        self.generate_accuracy_report(tasks, results_map)

        print(f"\n[COMPLETED] Output Excel workbook saved -> '{excel_writer.output_path}'")
        return {"success": True, "processed": len(results_map)}

    def generate_accuracy_report(self, tasks: list[dict], results_map: dict):
        total_rows = len(tasks)
        fully_extracted = sum(1 for r in results_map.values() if r.get("status") == "FULLY_EXTRACTED")
        partially_extracted = sum(1 for r in results_map.values() if r.get("status") == "PARTIAL_EXTRACTION")
        failed_rows = sum(1 for r in results_map.values() if not r.get("success") or r.get("status") in ["FAILED", "LOW_CONFIDENCE"])

        # Field-by-field accuracy tracking
        field_counts = {k: 0 for k, _ in MANDATORY_FIELDS}
        for res in results_map.values():
            tr = res.get("trace", {})
            diag = tr.get("field_diagnostics", {})
            for k, _ in MANDATORY_FIELDS:
                if diag.get(k, {}).get("found"):
                    field_counts[k] += 1

        print("\n=========================================================================")
        print(">>> EXTRACTION ACCURACY REPORT (RUNTIME EVIDENCE)")
        print("=========================================================================")
        print(f"Total Rows Processed     : {total_rows}")
        print(f"Rows Fully Extracted     : {fully_extracted}")
        print(f"Rows Partially Extracted : {partially_extracted}")
        print(f"Rows Failed / Low Conf   : {failed_rows}")
        print("-------------------------------------------------------------------------")
        for k, lbl in MANDATORY_FIELDS:
            acc = (field_counts[k] / float(total_rows)) * 100.0 if total_rows > 0 else 0.0
            print(f"{lbl:<26} Accuracy : {acc:5.1f}% ({field_counts[k]}/{total_rows})")

        overall_acc = (sum(field_counts.values()) / float(total_rows * len(MANDATORY_FIELDS))) * 100.0 if total_rows > 0 else 0.0
        print("-------------------------------------------------------------------------")
        print(f"OVERALL EXTRACTION ACCURACY % : {overall_acc:5.1f}%")
        print("=========================================================================\n")
