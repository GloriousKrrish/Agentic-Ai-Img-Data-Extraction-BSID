"""
Phase 2: Multi-Page Table Aggregator Engine
Stitches multi-page continuation tables across page breaks, deduplicates repeated page headers,
and resolves cross-page table conflicts.
"""
from typing import List, Dict, Any, Tuple
from backend.agents.table_models import (
    TableStructure, TableRow, TableColumn, TableAnomaly
)

class TableAggregatorEngine:
    def stitch_multi_page_tables(
        self,
        tables_per_page: List[Tuple[int, TableStructure]]
    ) -> List[TableStructure]:
        """
        Stitches tables across page breaks if they represent the same continuous table.
        """
        if not tables_per_page:
            return []

        sorted_tables = sorted(tables_per_page, key=lambda x: x[0])
        consolidated: List[TableStructure] = []

        current_table: TableStructure = None

        for page_num, tbl in sorted_tables:
            if current_table is None:
                current_table = tbl.copy(deep=True)
                current_table.source_pages = [page_num]
                continue

            # Check if this table is a continuation of current_table
            if self._is_continuation(current_table, tbl):
                # Continuation detected! Deduplicate repeated headers and append rows
                current_table.source_pages.append(page_num)
                existing_row_keys = {r.raw_text for r in current_table.rows}

                for row in tbl.rows:
                    # Skip repeated header row on new page
                    if row.row_type == "HEADER" or row.raw_text in existing_row_keys:
                        continue

                    # Mark row position
                    row_copy = row.copy(deep=True)
                    row_copy.page_number = page_num
                    row_copy.position = len(current_table.rows)
                    current_table.rows.append(row_copy)
            else:
                consolidated.append(current_table)
                current_table = tbl.copy(deep=True)
                current_table.source_pages = [page_num]

        if current_table:
            consolidated.append(current_table)

        return consolidated

    def _is_continuation(self, table_a: TableStructure, table_b: TableStructure) -> bool:
        """
        Determines whether table_b is a continuation of table_a.
        """
        # 1. Column count match
        if len(table_a.columns) != len(table_b.columns):
            return False

        # 2. Header similarity
        headers_a = [h.lower() for h in table_a.headers]
        headers_b = [h.lower() for h in table_b.headers]

        if headers_a == headers_b and headers_a:
            return True

        # 3. Check if first row of table_b matches headers of table_a
        if table_b.rows and table_b.rows[0].row_type == "HEADER":
            first_row_cells = [c.raw_value.lower() for c in table_b.rows[0].cells]
            if first_row_cells == headers_a:
                return True

        # 4. If table_a has no total row yet and column count matches
        last_row_type = table_a.rows[-1].row_type if table_a.rows else "DATA"
        if last_row_type in ["DATA", "CONTINUATION"]:
            return True

        return False

table_aggregator = TableAggregatorEngine()
