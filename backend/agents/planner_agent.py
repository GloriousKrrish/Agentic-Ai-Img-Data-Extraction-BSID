"""
Phase 2: Agentic Planner Agent
Receives InputAnalysis and constructs an executable ExtractionPlan specifying agent selection,
processing strategy, validation rules, retry policies, and human review thresholds.
"""
import uuid
import time
from backend.agents.agentic_models import (
    InputAnalysis, ExtractionPlan, ProcessingStrategy,
    ValidationStrategy, RetryPolicy, HumanReviewPolicy
)
from backend.agents.capability_registry import capability_registry
from backend.agents.entity_prompts import DOMAIN_PRESETS

class PlannerAgent:
    def create_plan(self, analysis: InputAnalysis, user_preset: str = "") -> ExtractionPlan:
        plan_id = f"plan-{uuid.uuid4().hex[:8]}"
        created_at = time.strftime("%Y-%m-%dT%H:%M:%SZ")

        # 1. Determine Target Category & Schema Strategy
        schema_strategy = "dynamic"
        target_category = "General Document"

        if user_preset and user_preset in DOMAIN_PRESETS:
            schema_strategy = "preset"
            target_category = DOMAIN_PRESETS[user_preset]["category"]
        elif analysis.document_type == "invoice":
            target_category = "Invoice / Bill"
        elif analysis.document_type == "medical_report":
            target_category = "Medical / Lab Report"
        elif analysis.document_type == "kyc_document":
            target_category = "KYC / ID Card"
        elif analysis.document_type == "academic_result":
            target_category = "Academic Result / Marksheet"
        elif analysis.document_type == "financial_statement":
            target_category = "Financial Statement"
        elif analysis.document_type == "legal_contract":
            target_category = "Legal Contract"

        # 2. Select Required Agents
        selected_agents = ["input_analyzer", "schema_generator"]

        if analysis.requires_ocr:
            selected_agents.append("ocr_agent")

        if analysis.requires_vision or analysis.is_scanned:
            selected_agents.append("vision_extraction_agent")

        if analysis.requires_table_extraction:
            selected_agents.append("table_extraction_agent")

        selected_agents.extend(["validation_agent", "confidence_engine", "dynamic_exporter"])

        # 3. Formulate Tools & Processing Strategy
        tools = ["pdf_parser", "gemini_multimodal", "image_preprocessor", "openpyxl_exporter"]
        if analysis.requires_ocr:
            tools.append("tesseract_ocr")

        processing_strat = ProcessingStrategy(
            parallelizable=analysis.complexity != "high",
            chunk_required=analysis.requires_chunking,
            cross_page_context=analysis.page_count > 1,
            pyramid_slicing=analysis.is_scanned or analysis.input_type == "image"
        )

        # 4. Formulate Validation & Retry Strategy
        val_strat = ValidationStrategy(
            ocr_consensus=analysis.requires_ocr and analysis.requires_vision,
            arithmetic_validation=analysis.document_domain == "finance" or analysis.document_type == "invoice",
            schema_validation=True,
            confidence_threshold=0.75 if analysis.complexity == "high" else 0.70
        )

        retry_pol = RetryPolicy(
            enabled=True,
            max_retries=2,
            max_replans=2
        )

        hitl_pol = HumanReviewPolicy(
            enabled=True,
            threshold=0.70
        )

        return ExtractionPlan(
            plan_id=plan_id,
            input_classification=analysis.dict(),
            schema_strategy=schema_strategy,
            target_category=target_category,
            agents=selected_agents,
            tools=tools,
            processing_strategy=processing_strat,
            validation_strategy=val_strat,
            retry_policy=retry_pol,
            human_review=hitl_pol,
            output_formats=["json", "xlsx", "csv"],
            created_at=created_at
        )

planner_agent = PlannerAgent()
