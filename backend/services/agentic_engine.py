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

        # 3. EXECUTE — Schema Generation
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

        # 5. VALIDATE & SCORE
        t_val = time.time()
        schema = extraction_res.get("schema", [])
        validated_fields, score_card = validation_engine.validate_and_score(raw_fields, plan, ocr_text, schema)
        record_step("validation_engine", "Evaluate Validation & Scorecard", "COMPLETED", t_val, f"Overall Confidence: {score_card.overall_confidence*100:.1f}%, Trusted: {score_card.is_trusted}", conf=score_card.overall_confidence)

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
