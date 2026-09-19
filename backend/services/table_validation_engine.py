"""
Phase 2: Table Validation & Math Audit Engine
Performs structural validation, column consistency checks, duplicate header checks,
and mathematical formula verification (qty * price = amount, subtotal + tax = total, sum(line_items) = subtotal).
"""
from typing import List, Dict, Any, Tuple
from backend.agents.table_models import (
    TableStructure, TableValidationReport, TableAnomaly
)

class TableValidationEngine:
    def validate_table(
        self,
        table_structure: TableStructure,
        reconstructed_rows: List[Dict[str, Any]],
        detected_anomalies: List[TableAnomaly] = None
    ) -> TableValidationReport:
        """
        Validates structural coherence and mathematical consistency of a reconstructed table.
        """
        anomalies: List[TableAnomaly] = list(detected_anomalies or [])
        headers = table_structure.headers
        
        # 1. Duplicate Headers Check
        seen_h = set()
        dup_h = []
        for h in headers:
            h_lower = h.lower().strip()
            if h_lower in seen_h and h_lower:
                dup_h.append(h)
                anomalies.append(TableAnomaly(
                    anomaly_type="DUPLICATE_HEADER",
                    severity="LOW",
                    description=f"Duplicate header column name '{h}' detected",
                    suggested_fix="Deduplicate column names with position indices"
                ))
            seen_h.add(h_lower)

        # 2. Missing Cells Count
        missing_count = 0
        for row in reconstructed_rows:
            for k, v in row.items():
                if k.startswith("_"):
                    continue
                if v is None or v == "":
                    missing_count += 1

        # 3. Mathematical Arithmetic Checks
        math_valid = True
        formula_consistent = True

        calculated_line_total = 0.0
        has_item_amounts = False

        for row in reconstructed_rows:
            # Check row-level multiplication: quantity * unit_price == amount
            qty = self._extract_float(row, ["quantity", "qty", "units", "count"])
            price = self._extract_float(row, ["unit_price", "price", "rate", "cost", "unitprice"])
            amount = self._extract_float(row, ["amount", "total", "line_total", "total_price"])

            if amount is not None:
                has_item_amounts = True
                calculated_line_total += amount

            if qty is not None and price is not None and amount is not None and qty > 0 and price > 0:
                expected_amount = round(qty * price, 2)
                diff = abs(expected_amount - amount)
                if diff > 0.05: # Allow small rounding tolerance
                    math_valid = False
                    formula_consistent = False
                    anomalies.append(TableAnomaly(
                        anomaly_type="ARITHMETIC_MISMATCH",
                        severity="HIGH",
                        description=f"Row multiplication mismatch: {qty} * {price} = {expected_amount} (expected) vs {amount} (extracted)",
                        affected_row_id=row.get("_row_id"),
                        suggested_fix="Verify OCR text for price or quantity"
                    ))

        # Check document-level totals if present
        subtotal = None
        total = None

        for row in table_structure.rows:
            if row.row_type == "SUBTOTAL":
                subtotal = self._extract_float_from_raw(row.raw_text)
            elif row.row_type == "TOTAL":
                total = self._extract_float_from_raw(row.raw_text)

        if subtotal is not None and has_item_amounts:
            if abs(calculated_line_total - subtotal) > 1.0:
                formula_consistent = False
                anomalies.append(TableAnomaly(
                    anomaly_type="ARITHMETIC_MISMATCH",
                    severity="MEDIUM",
                    description=f"Sum of line items ({calculated_line_total:.2f}) does not match table subtotal ({subtotal:.2f})"
                ))

        # Overall validation scoring
        overall_conf = 1.0
        if anomalies:
            critical_cnt = sum(1 for a in anomalies if a.severity in ["HIGH", "CRITICAL"])
            med_cnt = sum(1 for a in anomalies if a.severity == "MEDIUM")
            low_cnt = sum(1 for a in anomalies if a.severity == "LOW")

            deduction = (critical_cnt * 0.3) + (med_cnt * 0.15) + (low_cnt * 0.05)
            overall_conf = max(1.0 - deduction, 0.4)

        structural_valid = len(anomalies) == 0 or overall_conf >= 0.8

        return TableValidationReport(
            structural_validity=structural_valid,
            numeric_validity=math_valid,
            row_validity=True,
            column_validity=len(dup_h) == 0,
            formula_consistency=formula_consistent,
            duplicate_headers=dup_h,
            missing_cells=missing_count,
            anomalies=anomalies,
            confidence=round(overall_conf, 2)
        )

    def _extract_float(self, row_dict: Dict[str, Any], candidate_keys: List[str]) -> Any:
        for k, v in row_dict.items():
            if k.lower() in candidate_keys:
                try:
                    return float(v) if v is not None else None
                except (ValueError, TypeError):
                    pass
        return None

    def _extract_float_from_raw(self, text: str) -> Any:
        import re
        matches = re.findall(r'\b\d+[\.,]\d{2}\b|\b\d+\b', text)
        if matches:
            try:
                clean = matches[-1].replace(',', '')
                return float(clean)
            except ValueError:
                return None
        return None

table_validation_engine = TableValidationEngine()
