"""
Phase 2: Table Normalization Engine
Maps raw headers to standardized semantic keys (e.g., 'Qty.', 'QTY', 'Units' -> 'quantity')
while preserving original header text and source metadata.
"""
import re
from typing import Dict, Any, List
from backend.agents.table_models import TableStructure, TableColumn

class TableNormalizationEngine:
    SEMANTIC_HEADER_MAP = {
        "item": ["item", "item description", "description", "particulars", "product", "article", "details"],
        "quantity": ["qty", "qty.", "quantity", "units", "count", "number of items"],
        "unit_price": ["rate", "price", "unit price", "unit rate", "cost/unit", "price/unit", "unit cost"],
        "amount": ["amount", "total", "total price", "net amount", "line total", "total amount"],
        "tax": ["tax", "gst", "vat", "tax amount", "cgst", "sgst", "igst"],
        "hsn_sac": ["hsn", "sac", "hsn/sac", "code"],
        "discount": ["disc", "discount", "disc %", "discount amount"]
    }

    def normalize_table(self, table_structure: TableStructure) -> TableStructure:
        """
        Normalizes column header keys in TableStructure to standard semantic names.
        """
        normalized_cols: List[TableColumn] = []

        for col in table_structure.columns:
            orig = col.name
            orig_lower = orig.lower().strip()
            mapped_key = orig_lower

            for std_key, aliases in self.SEMANTIC_HEADER_MAP.items():
                if any(alias == orig_lower or alias in orig_lower for alias in aliases):
                    mapped_key = std_key
                    break

            col_copy = col.copy(deep=True)
            col_copy.name = mapped_key
            col_copy.display_name = orig
            normalized_cols.append(col_copy)

        table_structure.columns = normalized_cols
        table_structure.headers = [c.name for c in normalized_cols]
        return table_structure

table_normalization_engine = TableNormalizationEngine()
