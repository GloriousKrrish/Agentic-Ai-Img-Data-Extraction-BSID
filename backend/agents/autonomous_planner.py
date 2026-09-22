"""
v5.0 Autonomous Planner with Dynamic Tool Selection & Checkpoint Strategy
Formulates structured execution plans containing step dependencies, tool selections,
critique checkpoints, and fallback strategies.
"""
import uuid
import time
from typing import Dict, Any, List, Optional
from dataclasses import dataclass, field
from backend.agents.intent_policy_agent import UserIntent, PolicyValidationResult
from backend.agents.tool_registry import tool_registry, ToolMetadata

@dataclass
class PlanStep:
    step_id: str
    name: str
    tool_id: str
    purpose: str
    dependencies: List[str] = field(default_factory=list)
    checkpoint_required: bool = False
    status: str = "PENDING"
    result_summary: Optional[str] = None
    error: Optional[str] = None

@dataclass
class AutonomousExecutionPlan:
    plan_id: str
    intent_id: str
    user_id: str
    tenant_id: str
    strategy_name: str
    steps: List[PlanStep] = field(default_factory=list)
    selected_tools: List[str] = field(default_factory=list)
    estimated_latency_ms: int = 500
    max_critique_attempts: int = 3
    created_at: float = field(default_factory=time.time)

class AutonomousPlanner:
    """
    Formulates, adapts, and manages agentic document extraction plans.
    """

    def create_plan(
        self,
        intent: UserIntent,
        policy_result: PolicyValidationResult,
        doc_metadata: Optional[Dict[str, Any]] = None
    ) -> AutonomousExecutionPlan:
        """
        Generates an ordered, dependency-tracked execution plan.
        """
        doc_meta = doc_metadata or {}
        doc_type = doc_meta.get("mime_type", "")
        is_pdf = "pdf" in doc_type.lower() or intent.target_category == "PDF_DOCUMENT"

        selected_tools = tool_registry.select_tools_for_intent(
            intent.requested_actions,
            multi_doc=intent.multi_doc_context
        )

        steps: List[PlanStep] = []

        # Step 1: Document Analysis
        s1_id = f"step-1-{uuid.uuid4().hex[:4]}"
        steps.append(PlanStep(
            step_id=s1_id,
            name="Document Structural Analysis",
            tool_id="input_analyzer",
            purpose="Determine document type, complexity, and visual layout",
            dependencies=[],
            checkpoint_required=False
        ))

        # Step 2: PDF Page Parsing / Chunking (if PDF)
        s2_id = f"step-2-{uuid.uuid4().hex[:4]}"
        if is_pdf:
            steps.append(PlanStep(
                step_id=s2_id,
                name="PDF Multi-Page Intelligence",
                tool_id="pdf_intelligence",
                purpose="Render scanned pages and partition PDF into adaptive chunks",
                dependencies=[s1_id],
                checkpoint_required=False
            ))

        # Step 3: Schema Determination & Extraction
        s3_id = f"step-3-{uuid.uuid4().hex[:4]}"
        tool_for_schema = "schema_constrained_extractor" if intent.requested_schema_name else "schema_generator"
        steps.append(PlanStep(
            step_id=s3_id,
            name="Schema & Field Extraction",
            tool_id=tool_for_schema,
            purpose="Extract target document fields using dynamic or requested schema",
            dependencies=[s2_id if is_pdf else s1_id],
            checkpoint_required=False
        ))

        # Step 4: Table Intelligence
        s4_id = f"step-4-{uuid.uuid4().hex[:4]}"
        steps.append(PlanStep(
            step_id=s4_id,
            name="Table Structure & Math Intelligence",
            tool_id="table_intelligence",
            purpose="Extract tabular data, normalize columns, and verify row arithmetic",
            dependencies=[s3_id],
            checkpoint_required=False
        ))

        # Step 5: Field Validation Gate
        s5_id = f"step-5-{uuid.uuid4().hex[:4]}"
        steps.append(PlanStep(
            step_id=s5_id,
            name="Field Validation & Scorecard Gate",
            tool_id="validation_engine",
            purpose="Score extraction quality, check field regexes, and verify math integrity",
            dependencies=[s4_id],
            checkpoint_required=True
        ))

        # Step 6: Evidence Grounding
        s6_id = f"step-6-{uuid.uuid4().hex[:4]}"
        steps.append(PlanStep(
            step_id=s6_id,
            name="Source Evidence Grounding",
            tool_id="evidence_grounder",
            purpose="Bind extracted fields to exact visual bounding coordinates and text snippets",
            dependencies=[s5_id],
            checkpoint_required=False
        ))

        # Step 7: Critique & Self-Correction Checkpoint
        s7_id = f"step-7-{uuid.uuid4().hex[:4]}"
        steps.append(PlanStep(
            step_id=s7_id,
            name="Critique & Self-Correction Checkpoint",
            tool_id="critique_critic",
            purpose="Evaluate extraction errors and trigger targeted re-extraction if needed",
            dependencies=[s6_id],
            checkpoint_required=True
        ))

        # Step 8: Multi-Doc Reasoning (Optional)
        s8_id = f"step-8-{uuid.uuid4().hex[:4]}"
        if intent.multi_doc_context or "CROSS_REFERENCE" in intent.requested_actions:
            steps.append(PlanStep(
                step_id=s8_id,
                name="Multi-Document Correlation",
                tool_id="multi_doc_reasoner",
                purpose="Correlate entities and check consistency across document set",
                dependencies=[s7_id],
                checkpoint_required=False
            ))

        # Step 9: Knowledge Building (Optional)
        s9_id = f"step-9-{uuid.uuid4().hex[:4]}"
        if "KNOWLEDGE_INDEX" in intent.requested_actions:
            steps.append(PlanStep(
                step_id=s9_id,
                name="Tenant Knowledge Pattern Learning",
                tool_id="knowledge_builder",
                purpose="Store schema and taxonomy patterns into tenant knowledge base",
                dependencies=[s7_id],
                checkpoint_required=False
            ))

        # Step 10: Action Execution (Export / Webhook)
        s10_id = f"step-10-{uuid.uuid4().hex[:4]}"
        action_tool = "webhook_dispatcher" if "WEBHOOK_NOTIFY" in intent.requested_actions else "dynamic_exporter"
        steps.append(PlanStep(
            step_id=s10_id,
            name="Post-Extraction Action & Export",
            tool_id=action_tool,
            purpose="Generate canonical export and dispatch integrations",
            dependencies=[s7_id],
            checkpoint_required=True
        ))

        total_est_lat = sum(
            tool_registry.get_tool(s.tool_id).latency_ms
            for s in steps if tool_registry.get_tool(s.tool_id)
        )

        max_attempts = policy_result.applied_limits.get("max_critique_attempts", 3)

        return AutonomousExecutionPlan(
            plan_id=f"plan-{uuid.uuid4().hex[:8]}",
            intent_id=intent.intent_id,
            user_id=intent.user_id,
            tenant_id=intent.tenant_id,
            strategy_name=f"Autonomous_{intent.target_category}_Pipeline",
            steps=steps,
            selected_tools=selected_tools,
            estimated_latency_ms=total_est_lat,
            max_critique_attempts=max_attempts
        )

autonomous_planner = AutonomousPlanner()
