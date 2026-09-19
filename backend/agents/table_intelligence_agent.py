"""
Phase 2: Table Intelligence Agent Orchestrator
Top-level agent orchestrating detection, structure analysis, multi-page continuation,
reconstruction, validation, and semantic normalization.
"""
from typing import List, Dict, Any, Optional
from backend.agents.table_models import (
    TableExecutionResult, TableStructure, TableValidationReport, TableAnomaly
)
from backend.services.table_detector import table_detector
from backend.services.table_structure_engine import table_structure_engine
from backend.services.table_reconstruction_engine import table_reconstruction_engine
from backend.services.table_validation_engine import table_validation_engine
from backend.services.table_normalization_engine import table_normalization_engine
from backend.services.table_aggregator import table_aggregator

class TableIntelligenceAgent:
    def process_tables(
        self,
        raw_table_data: Any,
        text_content: str = "",
        page_number: int = 1,
        is_scanned: bool = False
    ) -> TableExecutionResult:
        """
        Executes end-to-end table understanding pipeline for a page or document.
        """
        # 1. Table Detection
        regions = table_detector.detect_table_regions(text_content, page_number=page_number, is_scanned=is_scanned)
        tbl_id = regions[0].table_id if regions else f"tbl-pg{page_number}"

        # 2. Table Structure Extraction
        structure: TableStructure = table_structure_engine.analyze_structure(
            raw_table_data,
            text_content=text_content,
            page_number=page_number,
            table_id=tbl_id
        )

        # 3. Semantic Normalization
        structure = table_normalization_engine.normalize_table(structure)

        # 4. Table Reconstruction & Column Shift Detection
        reconstructed_rows, anomalies = table_reconstruction_engine.reconstruct_table(structure)

        # 5. Validation & Math Audit
        validation_report: TableValidationReport = table_validation_engine.validate_table(
            table_structure=structure,
            reconstructed_rows=reconstructed_rows,
            detected_anomalies=anomalies
        )

        status = "COMPLETED" if validation_report.confidence >= 0.8 else "WAITING_FOR_HUMAN_REVIEW"

        return TableExecutionResult(
            table_id=tbl_id,
            page_number=page_number,
            table_structure=structure,
            validation_report=validation_report,
            reconstructed_rows=reconstructed_rows,
            confidence=validation_report.confidence,
            status=status
        )

    def process_multi_page_tables(
        self,
        page_raw_tables: List[Dict[str, Any]]
    ) -> List[TableExecutionResult]:
        """
        Processes multi-page table lists, stitching continuation tables across page breaks.
        """
        page_structures = []
        for idx, item in enumerate(page_raw_tables):
            p_num = item.get("page_number", idx + 1)
            raw = item.get("table_data") or item.get("line_items") or item
            struct = table_structure_engine.analyze_structure(raw, page_number=p_num)
            struct = table_normalization_engine.normalize_table(struct)
            page_structures.append((p_num, struct))

        # Stitch cross-page tables
        stitched_structures = table_aggregator.stitch_multi_page_tables(page_structures)

        results = []
        for struct in stitched_structures:
            reconstructed_rows, anomalies = table_reconstruction_engine.reconstruct_table(struct)
            val_report = table_validation_engine.validate_table(struct, reconstructed_rows, anomalies)

            status = "COMPLETED" if val_report.confidence >= 0.8 else "WAITING_FOR_HUMAN_REVIEW"

            results.append(TableExecutionResult(
                table_id=struct.table_id,
                page_number=struct.source_pages[0] if struct.source_pages else 1,
                table_structure=struct,
                validation_report=val_report,
                reconstructed_rows=reconstructed_rows,
                confidence=val_report.confidence,
                status=status
            ))

        return results

table_intelligence_agent = TableIntelligenceAgent()
