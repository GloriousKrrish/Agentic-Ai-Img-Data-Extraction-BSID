"""
Phase 3: Capability & Tool Registry
Maintains a central registry of available agents, services, and tools for the Agentic Planner.
"""
from typing import Dict, List, Optional
from backend.agents.agentic_models import AgentCapability

class CapabilityRegistry:
    def __init__(self):
        self._capabilities: Dict[str, AgentCapability] = {}
        self._register_default_capabilities()

    def register(self, cap: AgentCapability):
        self._capabilities[cap.name] = cap

    def get(self, name: str) -> Optional[AgentCapability]:
        return self._capabilities.get(name)

    def list_all(self) -> List[AgentCapability]:
        return list(self._capabilities.values())

    def find_capable(self, input_type: str, required_capability: str) -> List[AgentCapability]:
        matches = []
        for cap in self._capabilities.values():
            if input_type in cap.supported_input_types or "*" in cap.supported_input_types:
                if required_capability in cap.capabilities or "*" in cap.capabilities:
                    matches.append(cap)
        return matches

    def _register_default_capabilities(self):
        self.register(AgentCapability(
            name="input_analyzer",
            label="Universal Input Analyzer",
            purpose="Inspects binary structure, mime type, tables, scanned state, and complexity",
            supported_input_types=["*"],
            capabilities=["analysis", "classification", "domain_detection"],
            output_type="InputAnalysis"
        ))

        self.register(AgentCapability(
            name="ocr_agent",
            label="Dual-Pass OCR Engine",
            purpose="Extracts printed and handwritten text using OCR engine",
            supported_input_types=["image", "pdf", "png", "jpg"],
            capabilities=["ocr", "text_extraction"],
            output_type="text"
        ))

        self.register(AgentCapability(
            name="vision_extraction_agent",
            label="Multimodal Vision AI Extractor",
            purpose="Uses multimodal LLM with image pyramid sub-crops for zero-shot data extraction",
            supported_input_types=["image", "pdf", "png", "jpg", "webp"],
            capabilities=["vision_extraction", "schema_mapping", "line_item_extraction"],
            output_type="dict"
        ))

        self.register(AgentCapability(
            name="table_extraction_agent",
            label="Table & Line-Item Parser",
            purpose="Parses multi-row nested tabular structures into structured arrays",
            supported_input_types=["pdf", "image", "docx", "xlsx", "csv"],
            capabilities=["table_extraction", "line_items"],
            output_type="list"
        ))

        self.register(AgentCapability(
            name="schema_generator",
            label="Dynamic Schema Generator",
            purpose="Generates dynamic JSON schema definitions and domain preset fields",
            supported_input_types=["*"],
            capabilities=["schema_generation", "domain_presets"],
            output_type="dict"
        ))

        self.register(AgentCapability(
            name="validation_agent",
            label="Unified Validation & Math Audit Engine",
            purpose="Executes schema checks, regex rules, arithmetic audits, and OCR consensus",
            supported_input_types=["*"],
            capabilities=["validation", "math_audit", "ocr_consensus"],
            output_type="ValidationReport"
        ))

        self.register(AgentCapability(
            name="confidence_engine",
            label="Multi-Factor Confidence Evaluator",
            purpose="Derives field-level confidence scores based on multi-signal evidence",
            supported_input_types=["*"],
            capabilities=["confidence_scoring", "hitl_trigger"],
            output_type="ConfidenceScoreCard"
        ))

        self.register(AgentCapability(
            name="dynamic_exporter",
            label="Dual-Sheet Excel & CSV Exporter",
            purpose="Formats extracted datasets into multi-tab Excel workbooks and CSV files",
            supported_input_types=["dict", "list"],
            capabilities=["excel_export", "csv_export", "json_export"],
            output_type="bytes"
        ))

        self.register(AgentCapability(
            name="pdf_intelligence_agent",
            label="PDF Intelligence & High-Res Renderer",
            purpose="Analyzes font counts, text density, image density, page classification, and renders 300 DPI JPEGs",
            supported_input_types=["pdf"],
            capabilities=["pdf_intelligence", "pdf_page_classification", "pdf_page_rendering"],
            output_type="PDFDocumentAnalysis"
        ))

        self.register(AgentCapability(
            name="pdf_aggregator_engine",
            label="Cross-Page Aggregator & Table Continuation Engine",
            purpose="Stitches multi-page continuation line items, deduplicates headers, and resolves cross-page field conflicts",
            supported_input_types=["pdf", "list"],
            capabilities=["cross_page_aggregation", "pdf_table_continuation", "cross_page_context"],
            output_type="AggregatedDocumentResult"
        ))

        # Phase 2: Table Intelligence Capabilities
        self.register(AgentCapability(
            name="table_detector",
            label="Multi-Signal Table Detector",
            purpose="Detects table boundaries using text blocks, drawing lines, whitespace alignment, and visual patterns",
            supported_input_types=["pdf", "image", "png", "jpg"],
            capabilities=["table_detection", "bounding_box"],
            output_type="TableRegion"
        ))

        self.register(AgentCapability(
            name="table_structure_analyzer",
            label="Table Structure Analyzer",
            purpose="Parses table regions into columns, rows, merged cells, and hierarchical headers",
            supported_input_types=["pdf", "image", "dict", "list"],
            capabilities=["table_structure", "row_detection", "column_detection"],
            output_type="TableStructure"
        ))

        self.register(AgentCapability(
            name="row_classifier",
            label="Row Semantic Classifier",
            purpose="Classifies table row semantics (HEADER, DATA, SUBTOTAL, TOTAL, FOOTER, NOTE, CONTINUATION)",
            supported_input_types=["list", "dict"],
            capabilities=["row_classification", "semantic_labeling"],
            output_type="str"
        ))

        self.register(AgentCapability(
            name="column_mapper",
            label="Header & Column Mapper",
            purpose="Maps raw headers to standardized semantic column names and infer data types",
            supported_input_types=["list"],
            capabilities=["column_mapping", "semantic_types"],
            output_type="List[TableColumn]"
        ))

        self.register(AgentCapability(
            name="cell_extractor",
            label="Cell Intelligence Extractor",
            purpose="Extracts cell text, normalized values, data types, and 1:1 source bounding boxes",
            supported_input_types=["dict", "list"],
            capabilities=["cell_extraction", "value_normalization"],
            output_type="TableCell"
        ))

        self.register(AgentCapability(
            name="table_reconstruction_engine",
            label="Table Reconstruction Engine",
            purpose="Reconstructs clean data tables, handles column shift detection, and aligns missing cells",
            supported_input_types=["TableStructure"],
            capabilities=["table_reconstruction", "column_shift_detection"],
            output_type="List[dict]"
        ))

        self.register(AgentCapability(
            name="table_normalizer",
            label="Table Normalization Engine",
            purpose="Standardizes headers and cell data without losing raw text or source metadata",
            supported_input_types=["TableStructure"],
            capabilities=["table_normalization"],
            output_type="TableStructure"
        ))

        self.register(AgentCapability(
            name="table_validator",
            label="Table Validation & Math Engine",
            purpose="Audits row multiplication (qty*price=amount), subtotal sums, and column consistency",
            supported_input_types=["TableStructure"],
            capabilities=["table_validation", "table_math_audit"],
            output_type="TableValidationReport"
        ))

        self.register(AgentCapability(
            name="table_aggregator",
            label="Multi-Page Table Aggregator",
            purpose="Stitches multi-page continuation tables across page breaks and deduplicates headers",
            supported_input_types=["list"],
            capabilities=["multi_page_table_stitching", "table_continuation"],
            output_type="List[TableStructure]"
        ))

        self.register(AgentCapability(
            name="table_anomaly_detector",
            label="Table Anomaly Detector",
            purpose="Flags unexpected column counts, missing cells, invalid data types, and broken continuations",
            supported_input_types=["TableStructure"],
            capabilities=["table_anomaly_detection"],
            output_type="List[TableAnomaly]"
        ))

capability_registry = CapabilityRegistry()

