"""
v5.0 Explicit Tool & Capability Registry
Provides a centralized, typed, policy-checked inventory of all document
processing tools and sub-agents available to the Autonomous Planner.
"""
from typing import Dict, Any, List, Optional
from dataclasses import dataclass, field

@dataclass
class ToolMetadata:
    tool_id: str
    name: str
    description: str
    capabilities: List[str]
    is_deterministic: bool = True
    required_permissions: List[str] = field(default_factory=list)
    cost_weight: float = 1.0
    latency_ms: int = 100

class ToolRegistry:
    """
    Registry of platform tools and capability metadata for agentic planning.
    """

    def __init__(self):
        self._tools: Dict[str, ToolMetadata] = {}
        self._register_default_tools()

    def _register_default_tools(self):
        tools = [
            ToolMetadata(
                tool_id="input_analyzer",
                name="Input Document Analyzer",
                description="Analyzes document type, format, page count, and complexity",
                capabilities=["analyze", "classify", "metadata"],
                is_deterministic=True,
                cost_weight=0.1,
                latency_ms=50
            ),
            ToolMetadata(
                tool_id="ocr_engine",
                name="Multi-Modal OCR Engine",
                description="Extracts raw text and bounding boxes from scanned images and PDFs",
                capabilities=["ocr", "text_extraction"],
                is_deterministic=True,
                cost_weight=0.5,
                latency_ms=200
            ),
            ToolMetadata(
                tool_id="vision_extractor",
                name="Vision LLM Extractor",
                description="Visual extraction of unstructured fields using LLM multimodal reasoning",
                capabilities=["vision", "multimodal", "unstructured_extraction"],
                is_deterministic=False,
                cost_weight=2.0,
                latency_ms=800
            ),
            ToolMetadata(
                tool_id="schema_generator",
                name="Dynamic Schema Generator",
                description="Infers structural schema and domain categories from raw content",
                capabilities=["schema_generation", "taxonomy"],
                is_deterministic=True,
                cost_weight=0.5,
                latency_ms=150
            ),
            ToolMetadata(
                tool_id="schema_constrained_extractor",
                name="Schema-Constrained Extractor",
                description="Extracts data strictly bounded by user-defined schema specifications",
                capabilities=["schema_extraction", "typed_extraction"],
                is_deterministic=True,
                cost_weight=1.0,
                latency_ms=300
            ),
            ToolMetadata(
                tool_id="pdf_intelligence",
                name="PDF Multi-Page Intelligence",
                description="Renders scanned pages and orchestrates adaptive page chunking",
                capabilities=["pdf_rendering", "page_chunking"],
                is_deterministic=True,
                cost_weight=0.8,
                latency_ms=250
            ),
            ToolMetadata(
                tool_id="table_intelligence",
                name="Advanced Table Intelligence Engine",
                description="Detects cell bounds, normalizes headers, and stitches multi-page tables",
                capabilities=["table_detection", "table_stitching", "math_validation"],
                is_deterministic=True,
                cost_weight=1.0,
                latency_ms=400
            ),
            ToolMetadata(
                tool_id="validation_engine",
                name="Field Validation & Scorecard Engine",
                description="Validates regex formats, cross-field arithmetic, and confidence scoring",
                capabilities=["validation", "scoring", "confidence"],
                is_deterministic=True,
                cost_weight=0.2,
                latency_ms=50
            ),
            ToolMetadata(
                tool_id="evidence_grounder",
                name="Source Evidence Grounding Engine",
                description="Binds extracted fields to exact visual coordinates and text snippets",
                capabilities=["evidence_grounding", "provenance"],
                is_deterministic=True,
                cost_weight=0.3,
                latency_ms=100
            ),
            ToolMetadata(
                tool_id="critique_critic",
                name="Self-Correction & Anomaly Critic",
                description="Evaluates extraction errors and formulates targeted re-extraction requests",
                capabilities=["critique", "self_correction", "diagnosis"],
                is_deterministic=True,
                cost_weight=0.5,
                latency_ms=150
            ),
            ToolMetadata(
                tool_id="multi_doc_reasoner",
                name="Multi-Document Correlation Engine",
                description="Cross-references entities and computes consensus across document batches",
                capabilities=["multi_doc", "cross_referencing", "batch_insight"],
                is_deterministic=True,
                cost_weight=1.5,
                latency_ms=500
            ),
            ToolMetadata(
                tool_id="knowledge_builder",
                name="Tenant Knowledge & Taxonomy Store",
                description="Learns domain schemas and stores reusable extraction patterns per tenant",
                capabilities=["knowledge_indexing", "pattern_learning"],
                is_deterministic=True,
                cost_weight=0.4,
                latency_ms=100
            ),
            ToolMetadata(
                tool_id="dynamic_exporter",
                name="Multi-Format Exporter",
                description="Generates canonical exports in JSON, CSV, XLSX, and PDF Audit formats",
                capabilities=["export", "formatting"],
                is_deterministic=True,
                cost_weight=0.3,
                latency_ms=100
            ),
            ToolMetadata(
                tool_id="webhook_dispatcher",
                name="HMAC Webhook Dispatcher",
                description="Delivers signed webhook events to external tenant integration endpoints",
                capabilities=["webhook_notify", "integration"],
                is_deterministic=True,
                required_permissions=["webhooks:manage"],
                cost_weight=0.2,
                latency_ms=150
            )
        ]
        for tool in tools:
            self._tools[tool.tool_id] = tool

    def get_tool(self, tool_id: str) -> Optional[ToolMetadata]:
        return self._tools.get(tool_id)

    def list_tools(self) -> List[ToolMetadata]:
        return list(self._tools.values())

    def select_tools_for_intent(self, intent_actions: List[str], multi_doc: bool = False) -> List[str]:
        """
        Dynamically selects appropriate tool IDs required to satisfy requested intent actions.
        """
        selected = ["input_analyzer", "validation_engine", "evidence_grounder", "critique_critic"]

        if "EXTRACT" in intent_actions:
            selected.extend(["ocr_engine", "schema_generator", "table_intelligence"])
        if multi_doc or "CROSS_REFERENCE" in intent_actions:
            selected.append("multi_doc_reasoner")
        if "KNOWLEDGE_INDEX" in intent_actions:
            selected.append("knowledge_builder")
        if "EXPORT" in intent_actions:
            selected.append("dynamic_exporter")
        if "WEBHOOK_NOTIFY" in intent_actions:
            selected.append("webhook_dispatcher")

        # Deduplicate while preserving order
        result = []
        for t in selected:
            if t not in result and t in self._tools:
                result.append(t)
        return result

tool_registry = ToolRegistry()
