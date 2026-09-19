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

capability_registry = CapabilityRegistry()
