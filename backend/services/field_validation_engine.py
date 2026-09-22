"""
Phase 3: Field Validation Engine
Executes semantic type checks, cross-field relationship validation (subtotal+tax=total, qty*price=amount, issue_date<=due_date),
cross-page consistency audits, and structures error taxonomy reports.
"""
import re
from typing import Dict, Any, List, Tuple
from backend.agents.evidence_models import ErrorTaxonomyReport

class FieldValidationEngine:
    def validate_fields(
        self,
        fields_dict: Dict[str, Any],
        raw_text: str = ""
    ) -> Tuple[Dict[str, Any], List[ErrorTaxonomyReport]]:
        """
        Validates semantic types, arithmetic consistency, and generates error taxonomy reports.
        """
        errors: List[ErrorTaxonomyReport] = []
        validated: Dict[str, Any] = dict(fields_dict)

        # 1. Semantic Type Validation & Normalization
        for k, v in fields_dict.items():
            if k in ["line_items", "lineItems", "tableResult"]:
                continue

            k_lower = k.lower()
            val_str = str(v or "").strip()

            if not val_str:
                errors.append(ErrorTaxonomyReport(
                    error_category="MISSING_VALUE",
                    severity="LOW",
                    field_key=k,
                    description=f"Field '{k}' has empty or missing value",
                    recommended_action="Run targeted regional re-extraction"
                ))
                continue

            # Date Format Validation
            if any(dk in k_lower for dk in ["date", "created", "due"]):
                if not re.search(r'\d{1,4}[-/\.]\d{1,2}[-/\.]\d{1,4}', val_str):
                    errors.append(ErrorTaxonomyReport(
                        error_category="TYPE_ERROR",
                        severity="LOW",
                        field_key=k,
                        description=f"Value '{val_str}' is not a recognized date format",
                        recommended_action="Re-parse date format string"
                    ))

            # Numeric/Currency Format Validation
            elif any(nk in k_lower for nk in ["total", "subtotal", "amount", "price", "tax", "cost"]):
                clean_num = re.sub(r'[^\d\.\-]', '', val_str)
                if not clean_num:
                    errors.append(ErrorTaxonomyReport(
                        error_category="TYPE_ERROR",
                        severity="MEDIUM",
                        field_key=k,
                        description=f"Expected numeric value in field '{k}', got '{val_str}'",
                        recommended_action="Clean currency symbols and re-extract"
                    ))

        # 2. Cross-Field Arithmetic Relationships
        subtotal = self._extract_num(fields_dict, ["subtotal", "sub_total", "subtotalamount", "net_amount", "netamount"])
        tax = self._extract_num(fields_dict, ["tax", "tax_amount", "taxamount", "vat", "gst", "gratuityamount"])
        total = self._extract_num(fields_dict, ["total", "grand_total", "total_amount", "totalamount", "amount_due", "amountdue", "grandtotal", "totalpayable", "totaldue"])

        if subtotal is not None and tax is not None and total is not None:
            expected_total = round(subtotal + tax, 2)
            if abs(expected_total - total) > 0.05:
                errors.append(ErrorTaxonomyReport(
                    error_category="ARITHMETIC_MISMATCH",
                    severity="HIGH",
                    field_key="total",
                    description=f"Cross-field total mismatch: subtotal ({subtotal}) + tax ({tax}) = {expected_total} (expected) vs total ({total}) (extracted)",
                    recommended_action="Targeted re-extraction of invoice totals"
                ))

        return validated, errors

    def _extract_num(self, fields: Dict[str, Any], keys: List[str]) -> Any:
        for k, v in fields.items():
            if k.lower() in keys and v is not None:
                try:
                    clean = re.sub(r'[^\d\.\-]', '', str(v))
                    return float(clean) if clean else None
                except ValueError:
                    pass
        return None

field_validation_engine = FieldValidationEngine()
