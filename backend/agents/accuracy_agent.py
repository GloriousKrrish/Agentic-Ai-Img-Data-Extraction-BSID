"""
Phase 3: Accuracy & Source Evidence Agent Orchestrator
Top-level agent orchestrating document quality assessment, candidate reconciliation,
1:1 source evidence binding, field validation, error taxonomy reporting, and targeted self-correction.
"""
from typing import Dict, Any, List, Optional
from backend.agents.evidence_models import (
    DocumentQualityAssessment, FieldEvidence, ConsensusResult, ErrorTaxonomyReport
)
from backend.services.document_quality_analyzer import document_quality_analyzer
from backend.services.source_evidence_engine import source_evidence_engine
from backend.services.extraction_consensus_engine import extraction_consensus_engine
from backend.services.field_validation_engine import field_validation_engine
from backend.services.targeted_reextraction_engine import targeted_reextraction_engine

class AccuracyAgent:
    def process_accuracy_pipeline(
        self,
        document_id: str,
        extracted_fields: Dict[str, Any],
        raw_text: str = "",
        file_bytes: bytes = b"",
        mime_type: str = "",
        schema_info: Dict[str, Any] = None
    ) -> Dict[str, Any]:
        """
        Executes end-to-end accuracy, consensus, evidence, and self-correction pipeline.
        """
        # 1. Document Quality Assessment
        quality: DocumentQualityAssessment = document_quality_analyzer.assess_quality(
            file_bytes, f"doc_{document_id}", mime_type, raw_text
        )

        # 2. Field Validation & Error Taxonomy
        validated_fields, errors = field_validation_engine.validate_fields(extracted_fields, raw_text)

        # 3. Identify Problematic Fields requiring Targeted Re-Extraction
        problematic = [e.field_key for e in errors if e.severity in ["HIGH", "CRITICAL"] and e.field_key]

        if problematic and file_bytes and schema_info:
            reextracted = targeted_reextraction_engine.reextract_fields(
                file_bytes, schema_info, mime_type, problematic, raw_text
            )
            for k, new_v in reextracted.items():
                if new_v and str(new_v).strip():
                    validated_fields[k] = new_v

            # Re-validate post self-correction
            validated_fields, errors = field_validation_engine.validate_fields(validated_fields, raw_text)

        # 4. Source Evidence Binding
        evidences: Dict[str, FieldEvidence] = source_evidence_engine.bind_field_evidence(
            document_id=document_id,
            fields_dict=validated_fields,
            raw_text=raw_text
        )

        overall_conf = 0.95
        if errors:
            high_cnt = sum(1 for e in errors if e.severity in ["HIGH", "CRITICAL"])
            overall_conf = max(0.4, 0.95 - (high_cnt * 0.2) - (len(errors) * 0.05))

        return {
            "quality": quality.dict(),
            "validatedFields": validated_fields,
            "evidences": {k: v.dict() for k, v in evidences.items()},
            "errors": [e.dict() for e in errors],
            "overallConfidence": round(overall_conf, 2),
            "status": "COMPLETED" if overall_conf >= 0.8 else "WAITING_FOR_HUMAN_REVIEW"
        }

accuracy_agent = AccuracyAgent()
