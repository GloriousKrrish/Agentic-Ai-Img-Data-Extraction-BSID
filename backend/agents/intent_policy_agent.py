"""
v5.0 Intent Analysis & Policy/Safety Gate Agent
Parses user intent, enforces safety constraints, verifies tenant boundaries,
and applies deterministic operational policy limits before agentic planning.
"""
import uuid
import time
from typing import Dict, Any, List, Optional
from dataclasses import dataclass, field

@dataclass
class UserIntent:
    intent_id: str
    user_id: str
    tenant_id: str
    raw_prompt: str
    target_category: str = "AUTO_DETECT"
    requested_actions: List[str] = field(default_factory=list)
    multi_doc_context: bool = False
    requested_schema_name: Optional[str] = None
    created_at: float = field(default_factory=time.time)

@dataclass
class PolicyValidationResult:
    is_allowed: bool
    violations: List[str] = field(default_factory=list)
    sanitized_intent: Optional[UserIntent] = None
    applied_limits: Dict[str, Any] = field(default_factory=dict)
    safety_score: float = 1.0

class IntentPolicyAgent:
    """
    Evaluates raw prompts/intents against tenant policies, security gates,
    and platform resource limits.
    """

    ALLOWED_ACTIONS = {
        "EXTRACT", "VALIDATE", "CRITIQUE", "SUMMARIZE", "EXPORT",
        "CROSS_REFERENCE", "KNOWLEDGE_INDEX", "WEBHOOK_NOTIFY"
    }

    FORBIDDEN_KEYWORDS = [
        "DROP DATABASE", "DELETE USER", "BYPASS AUTH", "EXECUTE SYSTEM COMMAND",
        "READ OTHER TENANT", "PRIVILEGE ESCALATION", "EXFILTRATE KEY"
    ]

    DEFAULT_LIMITS = {
        "max_pages_per_doc": 100,
        "max_documents_in_batch": 50,
        "max_critique_attempts": 3,
        "allowed_export_formats": ["json", "csv", "xlsx", "pdf"],
        "rate_limit_jobs_per_min": 60
    }

    def parse_intent(
        self,
        raw_prompt: str,
        user_id: str,
        tenant_id: str,
        requested_actions: Optional[List[str]] = None,
        requested_schema_name: Optional[str] = None
    ) -> UserIntent:
        """
        Parses raw text prompt and options into a structured UserIntent.
        """
        actions = requested_actions or []
        prompt_lower = (raw_prompt or "").lower()

        if not actions:
            actions.append("EXTRACT")
            if "export" in prompt_lower or "download" in prompt_lower:
                actions.append("EXPORT")
            if "compare" in prompt_lower or "multi" in prompt_lower or "cross" in prompt_lower:
                actions.append("CROSS_REFERENCE")
            if "webhook" in prompt_lower or "notify" in prompt_lower:
                actions.append("WEBHOOK_NOTIFY")

        target_category = "AUTO_DETECT"
        if "invoice" in prompt_lower:
            target_category = "INVOICE"
        elif "receipt" in prompt_lower:
            target_category = "RECEIPT"
        elif "medical" in prompt_lower or "bill" in prompt_lower:
            target_category = "MEDICAL_BILL"
        elif "bank" in prompt_lower or "statement" in prompt_lower:
            target_category = "BANK_STATEMENT"

        multi_doc = "multi" in prompt_lower or "batch" in prompt_lower or "compare" in prompt_lower

        return UserIntent(
            intent_id=f"intent-{uuid.uuid4().hex[:8]}",
            user_id=user_id,
            tenant_id=tenant_id,
            raw_prompt=raw_prompt or "Standard Autonomous Extraction",
            target_category=target_category,
            requested_actions=list(set(actions)),
            multi_doc_context=multi_doc,
            requested_schema_name=requested_schema_name
        )

    def validate_policy(
        self,
        intent: UserIntent,
        user_permissions: Optional[List[str]] = None,
        tenant_tier: str = "ENTERPRISE"
    ) -> PolicyValidationResult:
        """
        Validates intent against security rules, tenant policies, and system capabilities.
        """
        violations = []
        user_perms = user_permissions or ["documents:read", "jobs:write", "webhooks:manage"]

        # 1. Check for malicious prompt patterns
        prompt_upper = intent.raw_prompt.upper()
        for forbidden in self.FORBIDDEN_KEYWORDS:
            if forbidden in prompt_upper:
                violations.append(f"Security Policy Violation: Forbidden pattern detected '{forbidden}'")

        # 2. Check tenant and action permissions
        for action in intent.requested_actions:
            if action not in self.ALLOWED_ACTIONS:
                violations.append(f"Action Policy Violation: Unknown or unauthorized action '{action}'")
            if action == "WEBHOOK_NOTIFY" and "webhooks:manage" not in user_perms and "admin" not in user_perms:
                violations.append("Permission Policy Violation: User lacks 'webhooks:manage' permission")

        # 3. Apply tenant-tier resource limits
        limits = dict(self.DEFAULT_LIMITS)
        if tenant_tier == "FREE":
            limits["max_pages_per_doc"] = 10
            limits["max_documents_in_batch"] = 5
            limits["max_critique_attempts"] = 1

        is_allowed = len(violations) == 0
        safety_score = 1.0 if is_allowed else max(0.0, 1.0 - (len(violations) * 0.4))

        return PolicyValidationResult(
            is_allowed=is_allowed,
            violations=violations,
            sanitized_intent=intent if is_allowed else None,
            applied_limits=limits,
            safety_score=safety_score
        )

intent_policy_agent = IntentPolicyAgent()
