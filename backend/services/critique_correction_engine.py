"""
v5.0 Critique & Self-Correction Feedback Loop Engine
Evaluates extraction results against domain schemas, validation rules, and math constraints,
diagnoses anomalies, and generates targeted self-correction re-extraction requests.
"""
import uuid
import re
from typing import Dict, Any, List, Optional
from dataclasses import dataclass, field

def _normalize_key(k: str) -> str:
    return k.lower().replace("_", "").replace("-", "").replace(" ", "")

@dataclass
class CritiqueAnomaly:
    anomaly_id: str
    field_name: str
    anomaly_type: str  # "MATH_MISMATCH", "MISSING_REQUIRED", "FORMAT_INVALID", "LOW_CONFIDENCE"
    description: str
    severity: str  # "CRITICAL", "WARNING"

@dataclass
class CritiqueDiagnosis:
    diagnosis_id: str
    has_anomalies: bool
    anomalies: List[CritiqueAnomaly] = field(default_factory=list)
    retry_recommended: bool = False
    reextraction_fields: List[str] = field(default_factory=list)
    suggested_strategy: Optional[str] = None
    critique_score: float = 100.0

class CritiqueAndSelfCorrectionEngine:
    """
    Automated Critique Critic that inspects extracted document output,
    identifies discrepancies, and controls the self-correction feedback loop.
    """

    REQUIRED_KEYS_BY_CATEGORY = {
        "INVOICE": ["invoice_number", "total_amount", "date"],
        "MEDICAL_BILL": ["patient_name", "total_amount", "subtotal"],
        "RECEIPT": ["total_amount", "date"],
        "BANK_STATEMENT": ["account_number", "ending_balance"]
    }

    def evaluate_extraction(
        self,
        extracted_fields: Dict[str, Any],
        category: str = "AUTO_DETECT",
        ocr_text: str = "",
        validations: Optional[Dict[str, bool]] = None,
        current_attempt: int = 1,
        max_attempts: int = 3
    ) -> CritiqueDiagnosis:
        """
        Diagnoses extraction output quality and decides whether to trigger targeted self-correction.
        """
        anomalies: List[CritiqueAnomaly] = []
        norm_map = {_normalize_key(k): (k, v) for k, v in extracted_fields.items()}

        # 1. Math Inconsistency Check
        val_checks = validations or {}
        if val_checks.get("arithmetic") is False or val_checks.get("math") is False:
            anomalies.append(CritiqueAnomaly(
                anomaly_id=f"anom-{uuid.uuid4().hex[:6]}",
                field_name="total_amount / subtotal",
                anomaly_type="MATH_MISMATCH",
                description="Calculated sum of subtotal, tax, or line items does not match total amount.",
                severity="CRITICAL"
            ))

        # 2. Missing Required Field Check
        req_keys = self.REQUIRED_KEYS_BY_CATEGORY.get(category.upper(), ["total_amount"])
        reextract_fields = []
        for rk in req_keys:
            norm_rk = _normalize_key(rk)
            val_tuple = norm_map.get(norm_rk)
            if not val_tuple or val_tuple[1] is None or str(val_tuple[1]).strip() in ["", "None", "null", "N/A"]:
                anomalies.append(CritiqueAnomaly(
                    anomaly_id=f"anom-{uuid.uuid4().hex[:6]}",
                    field_name=rk,
                    anomaly_type="MISSING_REQUIRED",
                    description=f"Required domain field '{rk}' is missing or empty.",
                    severity="WARNING"
                ))
                reextract_fields.append(rk)

        # 3. Format & Date Validation Check
        date_tuple = norm_map.get("date") or norm_map.get("invoicedate")
        if date_tuple and date_tuple[1]:
            val_str = str(date_tuple[1]).strip()
            # Simple regex check for plausible date
            if not re.search(r"\d{1,4}[-/\.]\d{1,2}[-/\.]\d{1,4}", val_str) and not re.search(r"[A-Za-z]{3,9}\s+\d{1,2}", val_str):
                anomalies.append(CritiqueAnomaly(
                    anomaly_id=f"anom-{uuid.uuid4().hex[:6]}",
                    field_name=date_tuple[0],
                    anomaly_type="FORMAT_INVALID",
                    description=f"Field '{date_tuple[0]}' has implausible date value '{val_str}'.",
                    severity="WARNING"
                ))
                reextract_fields.append(date_tuple[0])

        has_anomalies = len(anomalies) > 0
        critique_score = max(0.0, round(100.0 - (len(anomalies) * 20.0), 1))

        # Determine if retry is recommended within retry budget
        can_retry = current_attempt < max_attempts
        has_critical = any(a.severity == "CRITICAL" for a in anomalies)
        retry_recommended = can_retry and (has_critical or len(reextract_fields) > 0)

        suggested_strategy = None
        if retry_recommended:
            if has_critical:
                suggested_strategy = "TARGETED_MATH_REEXTRACTION"
            else:
                suggested_strategy = "FOCUSED_FIELD_REEXTRACTION"

        return CritiqueDiagnosis(
            diagnosis_id=f"diag-{uuid.uuid4().hex[:8]}",
            has_anomalies=has_anomalies,
            anomalies=anomalies,
            retry_recommended=retry_recommended,
            reextraction_fields=reextract_fields,
            suggested_strategy=suggested_strategy,
            critique_score=critique_score
        )

critique_correction_engine = CritiqueAndSelfCorrectionEngine()
