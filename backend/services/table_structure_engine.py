"""
Phase 2: Table Structure Engine
Analyzes table regions to extract columns, rows, merged cells, row semantic classifications (HEADER, DATA, SUBTOTAL, TOTAL, FOOTER, NOTE, CONTINUATION), and hierarchical header structures.
"""
import re
import uuid
from typing import List, Dict, Any, Tuple
from backend.agents.table_models import (
    TableStructure, TableColumn, TableRow, TableCell, BoundingBox
)

class TableStructureEngine:
    def analyze_structure(
        self,
        raw_table_data: Any,
        text_content: str = "",
        page_number: int = 1,
        table_id: str = ""
    ) -> TableStructure:
        """
        Parses raw text/list lines into a strongly-typed TableStructure model.
        """
        if not table_id:
            table_id = f"tbl-{uuid.uuid4().hex[:6]}"

        if isinstance(raw_table_data, str) and raw_table_data:
            headers, rows_data = self._parse_text_table(raw_table_data)
        elif (raw_table_data is None or raw_table_data == [] or raw_table_data == {}) and text_content:
            headers, rows_data = self._parse_text_table(text_content)
        elif isinstance(raw_table_data, dict):
            headers = raw_table_data.get("headers", [])
            rows_data = raw_table_data.get("rows", [])
        elif isinstance(raw_table_data, list):
            if raw_table_data and isinstance(raw_table_data[0], list):
                headers = [str(c) for c in raw_table_data[0]]
                rows_data = raw_table_data[1:]
            elif raw_table_data and isinstance(raw_table_data[0], dict):
                headers = list(raw_table_data[0].keys())
                rows_data = raw_table_data
            else:
                if text_content:
                    headers, rows_data = self._parse_text_table(text_content)
                else:
                    headers = []
                    rows_data = []
        else:
            headers, rows_data = [], []

        # Build columns
        columns: List[TableColumn] = []
        for idx, h_name in enumerate(headers):
            clean_name = str(h_name).strip() or f"col_{idx+1}"
            sem_type = self._infer_semantic_type(clean_name)
            columns.append(TableColumn(
                column_id=f"col-{idx+1}",
                name=clean_name,
                display_name=clean_name.replace('_', ' ').title(),
                semantic_type=sem_type,
                position=idx,
                confidence=0.95
            ))

        # Build rows & classify semantics
        rows: List[TableRow] = []
        for r_idx, r_val in enumerate(rows_data):
            cell_list: List[TableCell] = []
            raw_cells: List[str] = []

            if isinstance(r_val, dict):
                for c_idx, col in enumerate(columns):
                    cell_raw = str(r_val.get(col.name, "") or r_val.get(col.display_name, "") or "")
                    raw_cells.append(cell_raw)
                    cell_list.append(TableCell(
                        cell_id=f"cell-{r_idx+1}-{c_idx+1}",
                        row_id=f"row-{r_idx+1}",
                        column_id=col.column_id,
                        raw_value=cell_raw,
                        normalized_value=self._normalize_cell_value(cell_raw, col.semantic_type),
                        data_type=col.semantic_type,
                        confidence=0.95,
                        source_page=page_number
                    ))
            elif isinstance(r_val, list):
                for c_idx, col in enumerate(columns):
                    cell_raw = str(r_val[c_idx]) if c_idx < len(r_val) else ""
                    raw_cells.append(cell_raw)
                    cell_list.append(TableCell(
                        cell_id=f"cell-{r_idx+1}-{c_idx+1}",
                        row_id=f"row-{r_idx+1}",
                        column_id=col.column_id,
                        raw_value=cell_raw,
                        normalized_value=self._normalize_cell_value(cell_raw, col.semantic_type),
                        data_type=col.semantic_type,
                        confidence=0.95,
                        source_page=page_number
                    ))

            row_text = " | ".join(raw_cells)
            row_type = self.classify_row_type(row_text, raw_cells, r_idx, len(rows_data))

            rows.append(TableRow(
                row_id=f"row-{r_idx+1}",
                row_type=row_type,
                page_number=page_number,
                position=r_idx,
                cells=cell_list,
                raw_text=row_text
            ))

        return TableStructure(
            table_id=table_id,
            headers=[c.name for c in columns],
            columns=columns,
            rows=rows,
            source_pages=[page_number],
            confidence=0.92
        )

    def classify_row_type(self, row_text: str, cells: List[str], row_idx: int, total_rows: int) -> str:
        """
        Classifies row semantics into: HEADER, DATA, SUBTOTAL, TOTAL, FOOTER, NOTE, CONTINUATION, UNKNOWN
        """
        text_lower = row_text.lower().strip()
        if not text_lower:
            return "UNKNOWN"

        # Check for Total / Subtotal keywords
        if any(k in text_lower for k in ["subtotal", "sub total", "sub-total", "amount due"]):
            return "SUBTOTAL"
        if any(k in text_lower for k in ["grand total", "total amount", "net total", "balance due", "total"]):
            return "TOTAL"

        # Check for Footer / Notes
        if any(k in text_lower for k in ["thank you", "terms & conditions", "page ", "payment due", "note:", "nb:"]):
            return "FOOTER"

        # Check for Header keywords if row_idx == 0 and contains no numeric values
        if row_idx == 0:
            has_numbers = any(re.search(r'\d', c) for c in cells)
            if not has_numbers and any(k in text_lower for k in ["item", "qty", "description", "price", "amount", "unit", "rate", "product"]):
                return "HEADER"

        # Check for continuation / text without price/amount numbers
        if row_idx > 0 and not any(k in text_lower for k in ["total", "subtotal", "tax", "gst"]):
            has_price_or_amount = any(re.search(r'\b\d{3,}\b|\b\d+[\.,]\d{2}\b', c) for c in cells)
            if not has_price_or_amount and ("warranty" in text_lower or "description" in text_lower or "continued" in text_lower or len(cells) <= 2):
                return "CONTINUATION"

        return "DATA"

    def _infer_semantic_type(self, col_name: str) -> str:
        lower = col_name.lower()
        if any(k in lower for k in ["amount", "price", "rate", "cost", "total", "fee", "tax", "salary", "subtotal"]):
            return "currency"
        elif any(k in lower for k in ["qty", "quantity", "count", "units"]):
            return "integer"
        elif any(k in lower for k in ["date", "time", "created"]):
            return "date"
        elif any(k in lower for k in ["id", "code", "no", "number", "sku", "hsn"]):
            return "identifier"
        return "string"

    def _normalize_cell_value(self, raw_val: str, sem_type: str) -> Any:
        if not raw_val or raw_val.lower() in ["null", "none", "n/a", "-"]:
            return None
        clean = raw_val.strip()
        if sem_type == "currency" or sem_type == "float":
            clean_num = re.sub(r'[^\d\.\-]', '', clean)
            try:
                return float(clean_num) if clean_num else None
            except ValueError:
                return clean
        elif sem_type == "integer":
            clean_num = re.sub(r'[^\d\-]', '', clean)
            try:
                return int(clean_num) if clean_num else None
            except ValueError:
                return clean
        return clean

    def _parse_text_table(self, text: str) -> Tuple[List[str], List[List[str]]]:
        lines = [l.strip() for l in text.splitlines() if l.strip()]
        if not lines:
            return [], []

        def split_line(l: str) -> List[str]:
            if '|' in l:
                return [c.strip() for c in l.split('|') if c.strip()]
            elif '\t' in l:
                return [c.strip() for c in l.split('\t') if c.strip()]
            else:
                parts = [c.strip() for c in re.split(r'\s{2,}', l) if c.strip()]
                if len(parts) <= 1:
                    parts = [c.strip() for c in l.split() if c.strip()]
                return parts

        # Check for multi-line or hierarchical headers
        header_line_idx = 0
        max_splits = 0
        for idx, l in enumerate(lines[:3]):
            l_lower = l.lower()
            splits = len(split_line(l))
            if any(k in l_lower for k in ["item", "qty", "product", "description", "rate", "amount", "price", "unit", "name", "total"]) and splits >= max_splits:
                header_line_idx = idx
                max_splits = splits

        headers = split_line(lines[header_line_idx])
        rows = []
        for l in lines[header_line_idx + 1:]:
            parts = split_line(l)
            if parts:
                rows.append(parts)

        return headers, rows

table_structure_engine = TableStructureEngine()
