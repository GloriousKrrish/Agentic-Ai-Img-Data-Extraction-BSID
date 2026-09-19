"""
Phase 4 & 7: Agentic Execution Engine & Self-Correction Loop
Orchestrates the ANALYZE -> PLAN -> EXECUTE -> OBSERVE -> VALIDATE -> DIAGNOSE -> REPLAN -> RE-EXECUTE loop,
tracking step logs, handling bounded retries, and determining HITL state transitions.
"""
import time
import json
import uuid
from typing import Dict, Any, List
from backend.agents.agentic_models import (
    InputAnalysis, ExtractionPlan, ExecutionStepLog, ConfidenceScoreCard
)
from backend.agents.input_analyzer_agent import input_analyzer_agent
from backend.agents.planner_agent import planner_agent
from backend.services.schema_generator import generate_dynamic_schema
from backend.services.universal_extractor import extract_universal_document
from backend.services.validation_engine import validation_engine
from backend.services.file_parser import parse_file_content

class AgenticExecutionEngine:
    def execute_agentic_workflow(
        self,
        file_bytes: bytes,
        filename: str,
        mime_type: str = "",
        user_preset: str = "",
        log_callback = None
    ) -> Dict[str, Any]:
        """
        Executes complete agentic workflow loop for a document.
        """
        step_logs: List[ExecutionStepLog] = []

        def record_step(agent_name: str, stage: str, status: str, start_t: float, summary: str = "", err: str = None, conf: float = 0.0) -> ExecutionStepLog:
            log_item = ExecutionStepLog(
                step_id=f"step-{uuid.uuid4().hex[:6]}",
                agent_or_tool=agent_name,
                stage=stage,
                status=status,
                start_time=start_t,
                end_time=time.time(),
                input_summary=f"File: {filename} ({len(file_bytes)} bytes)",
                output_summary=summary[:300],
                error=err,
                confidence=conf
            )
            step_logs.append(log_item)
            if log_callback:
                log_callback("INFO" if status != "FAILED" else "ERROR", f"[{agent_name}] {stage}: {status} — {summary[:120]}")
            return log_item

        # 1. ANALYZE
        t_start = time.time()
        analysis: InputAnalysis = input_analyzer_agent.analyze(file_bytes, filename, mime_type)
        record_step("input_analyzer", "Analyze Input Document", "COMPLETED", t_start, f"Type: {analysis.input_type}, Category: {analysis.document_type}, Complexity: {analysis.complexity}")

        # 2. PLAN
        t_plan = time.time()
        plan: ExtractionPlan = planner_agent.create_plan(analysis, user_preset=user_preset)
        record_step("planner_agent", "Formulate Extraction Plan", "COMPLETED", t_plan, f"Plan ID: {plan.plan_id}, Target: {plan.target_category}, Agents: {', '.join(plan.agents)}")

        # Check if PDF input -> execute multi-page / scanned PDF intelligence workflow
        if analysis.input_type == "pdf":
            from backend.agents.pdf_intelligence_agent import pdf_intelligence_agent
            from backend.services.pdf_aggregator_engine import pdf_aggregator_engine
            from backend.agents.pdf_models import ExtractedPageResult

            t_pdf_anal = time.time()
            pdf_analysis = pdf_intelligence_agent.analyze_pdf(file_bytes)
            record_step(
                "pdf_intelligence_agent",
                "PDF Intelligence Analysis",
                "COMPLETED",
                t_pdf_anal,
                f"Total Pages: {pdf_analysis.total_pages}, Scanned: {pdf_analysis.scanned_page_count}, Tables: {pdf_analysis.table_page_count}, Complexity: {pdf_analysis.estimated_complexity}"
            )

            # Generate Schema
            t_schema = time.time()
            parsed_file = parse_file_content(file_bytes, filename, mime_type)
            ocr_text = parsed_file.get("text_content", "")
            schema_info = generate_dynamic_schema(file_bytes, mime_type, text_content=ocr_text)
            schema = schema_info.get("fields", [])
            record_step("schema_generator", "Generate Dynamic Schema", "COMPLETED", t_schema, f"Category: {schema_info.get('documentCategory')}, Fields: {len(schema)}")

            # Process Pages in Adaptive Chunks
            chunk_size = pdf_analysis.recommended_chunk_size
            total_pages = pdf_analysis.total_pages
            page_results: List[ExtractedPageResult] = []

            for chunk_start in range(0, total_pages, chunk_size):
                chunk_end = min(chunk_start + chunk_size, total_pages)
                chunk_num = (chunk_start // chunk_size) + 1
                t_chunk = time.time()

                for p_idx in range(chunk_start, chunk_end):
                    page_num = p_idx + 1
                    p_class = pdf_analysis.page_classifications[p_idx] if p_idx < len(pdf_analysis.page_classifications) else None
                    is_scanned_page = p_class.requires_ocr if p_class else False

                    # Render page JPEG if scanned or image heavy
                    page_bytes = file_bytes
                    page_mime = mime_type
                    if is_scanned_page or (p_class and p_class.type in ["SCANNED", "IMAGE_HEAVY", "TABLE_HEAVY"]):
                        rendered_jpeg = pdf_intelligence_agent.render_page_to_jpeg(file_bytes, page_num, dpi=300)
                        if rendered_jpeg:
                            page_bytes = rendered_jpeg
                            page_mime = "image/jpeg"

                    # Extract page data
                    page_res = extract_universal_document(page_bytes, schema_info, page_mime, text_content=ocr_text)
                    page_fields = page_res.get("extractedFields", {}) or {}
                    page_items = page_fields.get("line_items") or page_fields.get("lineItems") or []

                    page_results.append(ExtractedPageResult(
                        page_number=page_num,
                        chunk_number=chunk_num,
                        extracted_fields=page_fields,
                        line_items=page_items if isinstance(page_items, list) else [],
                        confidence=page_res.get("confidence", 85.0),
                        status="COMPLETED",
                        is_scanned=is_scanned_page
                    ))

                record_step("pdf_intelligence_agent", f"Process PDF Chunk {chunk_num} (Pages {chunk_start+1}-{chunk_end})", "COMPLETED", t_chunk, f"Processed {chunk_end - chunk_start} pages in Chunk {chunk_num}")

            # Cross-Page Aggregation & Table Continuation
            t_agg = time.time()
            aggregated = pdf_aggregator_engine.aggregate_pages(page_results)
            record_step("pdf_aggregator_engine", "Cross-Page Table Continuation & Aggregation", "COMPLETED", t_agg, f"Stitched {len(aggregated.line_items)} line items across {total_pages} pages. Conflicts: {len(aggregated.conflicts)}")

            # Table Intelligence Engine Pass
            from backend.agents.table_intelligence_agent import table_intelligence_agent
            t_tbl = time.time()
            table_exec_res = table_intelligence_agent.process_tables(
                raw_table_data=aggregated.line_items,
                text_content=ocr_text,
                page_number=1,
                is_scanned=pdf_analysis.is_scanned_pdf
            )
            record_step(
                "table_intelligence_agent",
                "Advanced Table Intelligence & Structural Analysis",
                "COMPLETED",
                t_tbl,
                f"Columns: {len(table_exec_res.table_structure.columns)}, Rows: {len(table_exec_res.table_structure.rows)}, Math Validity: {table_exec_res.validation_report.numeric_validity}, Anomalies: {len(table_exec_res.validation_report.anomalies)}"
            )

            validated_fields, score_card = validation_engine.validate_and_score(aggregated.document_fields, plan, ocr_text, schema)
            
            final_status = "COMPLETED" if (score_card.is_trusted and not aggregated.conflicts and table_exec_res.validation_report.structural_validity) else "WAITING_FOR_HUMAN_REVIEW"
            record_step("job_manager", "Finalize Multi-Page PDF Job State", "COMPLETED", time.time(), f"Final Status: {final_status}, Overall Conf: {score_card.overall_confidence*100:.1f}%")

            return {
                "status": final_status,
                "confidence": round(score_card.overall_confidence * 100.0, 1),
                "scorecard": score_card.dict(),
                "pdfAnalysis": pdf_analysis.dict(),
                "tableResult": table_exec_res.dict(),
                "analysis": analysis.dict(),
                "plan": plan.dict(),
                "schema": schema,
                "rows": [
                    {
                        "rowIndex": 1,
                        "fields": validated_fields,
                        "status": final_status,
                        "confidence": round(score_card.overall_confidence * 100.0, 1)
                    }
                ],
                "extractedFields": validated_fields,
                "executionLogs": [s.dict() for s in step_logs],
                "documentCategory": schema_info.get("documentCategory", plan.target_category),
                "documentTitle": schema_info.get("documentTitle", f"PDF Document ({total_pages} pages)")
            }

        # 3. EXECUTE — Schema Generation (Standard Non-PDF Flow)
        t_schema = time.time()
        parsed_file = parse_file_content(file_bytes, filename, mime_type)
        ocr_text = parsed_file.get("text_content", "")


        schema_info = generate_dynamic_schema(file_bytes, mime_type, text_content=ocr_text)
        record_step("schema_generator", "Generate Dynamic Schema", "COMPLETED", t_schema, f"Category: {schema_info.get('documentCategory')}, Fields: {len(schema_info.get('fields', []))}")

        # 4. EXECUTE — Multimodal Vision / Document Extraction Pass 1
        t_ext = time.time()
        extraction_res = extract_universal_document(file_bytes, schema_info, mime_type, text_content=ocr_text)
        raw_fields = extraction_res.get("extractedFields", {}) or {}
        record_step("vision_extraction_agent", "Extract Document Fields (Pass 1)", "COMPLETED", t_ext, f"Extracted {len(raw_fields)} raw fields using {extraction_res.get('modelUsed')}")

        # 5. ACCURACY, CONSENSUS, EVIDENCE & SELF-CORRECTION PASS
        t_acc = time.time()
        from backend.agents.accuracy_agent import accuracy_agent
        accuracy_res = accuracy_agent.process_accuracy_pipeline(
            document_id=plan.plan_id,
            extracted_fields=raw_fields,
            raw_text=ocr_text,
            file_bytes=file_bytes,
            mime_type=mime_type,
            schema_info=schema_info
        )
        record_step("accuracy_agent", "Accuracy, Consensus & Source Evidence Engine", "COMPLETED", t_acc, f"Evidences Bound: {len(accuracy_res.get('evidences', {}))}, Quality Strategy: {accuracy_res.get('quality', {}).get('recommended_strategy')}")

        validated_fields = accuracy_res.get("validatedFields", raw_fields)
        schema = extraction_res.get("schema", [])
        validated_fields, score_card = validation_engine.validate_and_score(validated_fields, plan, ocr_text, schema)
        record_step("validation_engine", "Evaluate Validation & Scorecard", "COMPLETED", time.time(), f"Overall Confidence: {score_card.overall_confidence*100:.1f}%, Trusted: {score_card.is_trusted}", conf=score_card.overall_confidence)

        # 6. DIAGNOSE & REPLAN (Self-Correction Loop)
        replan_count = 0
        max_replans = plan.retry_policy.max_replans

        while score_card.overall_confidence < plan.human_review.threshold and replan_count < max_replans:
            replan_count += 1
            t_replan = time.time()
            flagged = score_card.flagged_fields
            replan_summary = f"Confidence ({score_card.overall_confidence:.2f}) < threshold ({plan.human_review.threshold:.2f}). Flagged fields: {', '.join(flagged[:5])}"
            record_step("planner_agent", f"Diagnose & Re-plan (Pass {replan_count + 1})", "REPLANNING", t_replan, replan_summary)

            # Re-execute targeted pass with progressive hints
            targeted_prompt_hint = f"CRITICAL RE-EXTRACTION: Pay extreme attention to missing/low confidence fields: {', '.join(flagged)}. Verify numbers with 1:1 pixel accuracy."
            retry_res = extract_universal_document(file_bytes, schema_info, mime_type, text_content=f"{ocr_text}\n\n{targeted_prompt_hint}")
            retry_raw = retry_res.get("extractedFields", {}) or {}

            # Merge improvements
            for k, val in retry_raw.items():
                if val and str(val).strip() and not str(validated_fields.get(k, "") or "").strip():
                    validated_fields[k] = val

            validated_fields, score_card = validation_engine.validate_and_score(validated_fields, plan, ocr_text, schema)
            record_step("vision_extraction_agent", f"Targeted Re-extraction (Pass {replan_count + 1})", "COMPLETED", t_replan, f"New Overall Confidence: {score_card.overall_confidence*100:.1f}%", conf=score_card.overall_confidence)

        # 7. HITL State Determination
        final_status = "COMPLETED"
        if score_card.human_review_required:
            final_status = "WAITING_FOR_HUMAN_REVIEW"

        record_step("job_manager", "Finalize Job State", "COMPLETED", time.time(), f"Final Status: {final_status}, Trusted: {score_card.is_trusted}")

        return {
            "status": final_status,
            "confidence": round(score_card.overall_confidence * 100.0, 1),
            "scorecard": score_card.dict(),
            "analysis": analysis.dict(),
            "plan": plan.dict(),
            "schema": schema,
            "rows": [
                {
                    "rowIndex": 1,
                    "fields": validated_fields,
                    "status": final_status,
                    "confidence": round(score_card.overall_confidence * 100.0, 1)
                }
            ],
            "extractedFields": validated_fields,
            "executionLogs": [s.dict() for s in step_logs],
            "documentCategory": schema_info.get("documentCategory", plan.target_category),
            "documentTitle": schema_info.get("documentTitle", "Extracted Document")
        }

agentic_execution_engine = AgenticExecutionEngine()
