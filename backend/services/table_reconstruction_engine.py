"""
Phase 2: Table Reconstruction Engine
Reconstructs clean, normalized tabular outputs, performs column-shift detection, missing cell alignment, and preserves 1:1 source evidence.
"""
import re
from typing import List, Dict, Any, Tuple
from backend.agents.table_models import (
    TableStructure, TableRow, TableCell, TableAnomaly
)

class TableReconstructionEngine:
    def reconstruct_table(
        self,
        table_structure: TableStructure
    ) -> Tuple[List[Dict[str, Any]], List[TableAnomaly]]:
        """
        Reconstructs structured data rows from TableStructure and detects column shifts / anomalies.
        """
        reconstructed_rows: List[Dict[str, Any]] = []
        anomalies: List[TableAnomaly] = []

        if not table_structure or not table_structure.columns:
            return reconstructed_rows, anomalies

        expected_col_count = len(table_structure.columns)
        col_names = [c.name for c in table_structure.columns]

        for row in table_structure.rows:
            # Skip non-data rows for primary line items output, but flag totals
            if row.row_type in ["HEADER", "FOOTER", "NOTE"]:
                continue

            row_dict: Dict[str, Any] = {"_row_type": row.row_type, "_row_id": row.row_id}
            cell_count = len(row.cells)

            # Detect column shift or cell count mismatch
            if cell_count != expected_col_count:
                anomalies.append(TableAnomaly(
                    anomaly_type="COLUMN_SHIFT",
                    severity="MEDIUM",
                    description=f"Row {row.position+1} cell count ({cell_count}) mismatch with columns ({expected_col_count})",
                    affected_row_id=row.row_id,
                    suggested_fix="Align cells based on semantic data types"
                ))

            for cell in row.cells:
                # Find matching column
                matching_col = next((c for c in table_structure.columns if c.column_id == cell.column_id), None)
                key_name = matching_col.name if matching_col else f"col_{cell.column_id}"
                
                # Check for unexpected string in numeric column
                if matching_col and matching_col.semantic_type in ["currency", "float", "integer"]:
                    if cell.raw_value and not cell.normalized_value and not re.search(r'\d', cell.raw_value):
                        anomalies.append(TableAnomaly(
                            anomaly_type="UNEXPECTED_TYPE",
                            severity="LOW",
                            description=f"Non-numeric value '{cell.raw_value}' in numeric column '{key_name}'",
                            affected_row_id=row.row_id,
                            affected_column_id=cell.column_id
                        ))

                row_dict[key_name] = cell.normalized_value if cell.normalized_value is not None else cell.raw_value

            reconstructed_rows.append(row_dict)

        return reconstructed_rows, anomalies

table_reconstruction_engine = TableReconstructionEngine()
