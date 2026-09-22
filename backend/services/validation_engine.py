"""
Phase 5 & 6: Unified Validation & Multi-Factor Confidence Engine
Performs objective schema validation, regex format checks, arithmetic audits, OCR/LLM consensus matching,
and calculates observable field-level and document-level confidence scorecards.
"""
import re
from typing import Dict, Any, List, Tuple
from backend.agents.agentic_models import (
    ExtractionPlan, ValidationReport, FieldConfidence, ConfidenceScoreCard
)
from backend.services.data_sanitizer import perform_math_audit

class ValidationEngine:
    def validate_and_score(
        self,
        extracted_fields: Dict[str, Any],
        plan: ExtractionPlan,
        ocr_text: str = "",
        schema: List[Dict[str, Any]] = None
    ) -> Tuple[Dict[str, Any], ConfidenceScoreCard]:
        """
        Validates extracted record, applies self-corrections, and calculates a multi-factor confidence scorecard.
        """
        field_scores: Dict[str, FieldConfidence] = {}
        flagged_fields: List[str] = []
        review_reasons: List[str] = []

        schema_keys = [f["key"] for f in schema] if schema else list(extracted_fields.keys())
        ocr_upper = (ocr_text or "").upper()

        total_weight = 0.0
        weighted_score = 0.0

        for key, raw_val in extracted_fields.items():
            if key in ["serNo", "invoiceImageLink", "line_items", "lineItems"]:
                continue

            val_str = str(raw_val or "").strip()
            sources = ["vision"]
            validations = {"schema": True, "regex": True, "arithmetic": True}
            field_conf = 0.0

            if not val_str or val_str.lower() in ["null", "none", "n/a", "undefined"]:
                validations["schema"] = False
                field_scores[key] = FieldConfidence(
                    field_key=key,
                    value="",
                    confidence=0.0,
                    sources=sources,
                    validations=validations
                )
                flagged_fields.append(key)
                total_weight += 1.0
                continue

            # 1. Base Score for non-empty value (Multimodal Vision AI Extraction)
            field_conf = 0.80

            # 2. Regex Format Validation
            key_lower = key.lower()
            regex_pass = True

            if "mobile" in key_lower or "phone" in key_lower:
                clean_phone = re.sub(r'\D', '', val_str)
                if len(clean_phone) == 10 and clean_phone[0] in "6789":
                    regex_pass = True
                    field_conf += 0.15
                else:
                    regex_pass = False
            elif "gst" in key_lower or "gstin" in key_lower:
                if len(val_str) == 15 and val_str[:2].isdigit():
                    regex_pass = True
                    field_conf += 0.15
                else:
                    regex_pass = False
            elif "date" in key_lower:
                if re.search(r'\d{2}[/-]\d{2}[/-]\d{2,4}|\d{4}[/-]\d{2}[/-]\d{2}', val_str):
                    regex_pass = True
                    field_conf += 0.15
                else:
                    regex_pass = False
            elif any(nk in key_lower for nk in ["amount", "total", "cost", "price", "tax", "discount", "quantity"]):
                if re.search(r'^\d+(\.\d+)?$', val_str.replace(',', '').replace('$', '').replace('₹', '')):
                    regex_pass = True
                    field_conf += 0.15
                else:
                    regex_pass = False
            else:
                field_conf += 0.10

            validations["regex"] = regex_pass

            # 3. OCR Text Consensus Check (if OCR text available)
            if ocr_upper and val_str.upper() in ocr_upper:
                sources.append("ocr")
                field_conf += 0.05

            field_scores[key] = FieldConfidence(
                field_key=key,
                value=val_str,
                confidence=min(round(field_conf, 2), 1.0),
                sources=sources,
                validations=validations
            )

            weighted_score += field_conf
            total_weight += 1.0

        # 4. Arithmetic Consistency Audit & Cross-Field Validation
        math_audit = perform_math_audit(extracted_fields)
        from backend.services.field_validation_engine import field_validation_engine
        _, field_errors = field_validation_engine.validate_fields(extracted_fields, ocr_text)

        arithmetic_errors = [e for e in field_errors if e.error_category == "ARITHMETIC_MISMATCH"]
        arithmetic_passed = math_audit.get("passed", True) and len(arithmetic_errors) == 0

        if not arithmetic_passed:
            details = math_audit.get("details") or (arithmetic_errors[0].description if arithmetic_errors else "Math mismatch")
            review_reasons.append(f"Arithmetic consistency check failed: {details}")

        # Compute Overall Confidence
        overall_conf = round((weighted_score / total_weight), 2) if total_weight > 0 else 0.50
        if not arithmetic_passed:
            overall_conf = max(overall_conf - 0.20, 0.40)

        threshold = plan.human_review.threshold if plan else 0.70
        review_required = (overall_conf < threshold) or not arithmetic_passed or len(flagged_fields) > (len(schema_keys) * 0.5)

        if review_required and not review_reasons:
            review_reasons.append(f"Overall confidence score ({overall_conf:.2f}) below threshold ({threshold:.2f})")

        scorecard = ConfidenceScoreCard(
            overall_confidence=overall_conf,
            is_trusted=overall_conf >= threshold,
            field_scores=field_scores,
            flagged_fields=flagged_fields,
            human_review_required=review_required,
            review_reasons=review_reasons
        )

        return extracted_fields, scorecard

validation_engine = ValidationEngine()
