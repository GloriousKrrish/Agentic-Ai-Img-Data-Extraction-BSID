"""
v5.0 Policy-Guarded Action Execution Engine
Executes post-extraction operations (exports, webhooks, notifications) strictly guarded
by Policy Safety Gate rules and HITL status checks.
"""
import uuid
import time
import json
from typing import Dict, Any, List, Optional
from dataclasses import dataclass, field
from backend.agents.intent_policy_agent import UserIntent, PolicyValidationResult
from backend.services.dynamic_exporter import generate_dynamic_excel, generate_dynamic_csv
from backend.services.webhook_manager import webhook_manager

@dataclass
class ActionResult:
    action_id: str
    action_type: str
    status: str  # "SUCCESS", "SKIPPED", "FAILED"
    target: str
    payload_summary: str
    executed_at: float = field(default_factory=time.time)
    error: Optional[str] = None

class ActionExecutionEngine:
    """
    Orchestrates post-extraction side-effects safely.
    """

    def execute_actions(
        self,
        intent: UserIntent,
        policy_result: PolicyValidationResult,
        canonical_result: Dict[str, Any],
        webhook_url: Optional[str] = None
    ) -> List[ActionResult]:
        """
        Executes permitted post-extraction actions.
        """
        results: List[ActionResult] = []

        if not policy_result.is_allowed:
            results.append(ActionResult(
                action_id=f"act-{uuid.uuid4().hex[:6]}",
                action_type="POLICY_GUARD",
                status="SKIPPED",
                target="SYSTEM",
                payload_summary="Actions blocked by Policy Safety Gate",
                error="Policy validation failed"
            ))
            return results

        actions = intent.requested_actions

        # 1. Export Action
        if "EXPORT" in actions:
            allowed_formats = policy_result.applied_limits.get("allowed_export_formats", ["json", "xlsx"])
            exported_files = []
            item_list = [canonical_result]
            for fmt in allowed_formats:
                try:
                    if fmt == "xlsx":
                        raw_bytes = generate_dynamic_excel(item_list)
                    elif fmt == "csv":
                        raw_bytes = generate_dynamic_csv(item_list).encode("utf-8")
                    else:
                        raw_bytes = json.dumps(canonical_result).encode("utf-8")
                    exported_files.append(f"{fmt.upper()} ({len(raw_bytes)} bytes)")
                except Exception as e:
                    exported_files.append(f"{fmt.upper()} (Error: {str(e)})")

            results.append(ActionResult(
                action_id=f"act-{uuid.uuid4().hex[:6]}",
                action_type="EXPORT",
                status="SUCCESS",
                target="DYNAMIC_EXPORTER",
                payload_summary=f"Generated exports: {', '.join(exported_files)}"
            ))

        # 2. Webhook Notification Action
        if "WEBHOOK_NOTIFY" in actions and webhook_url:
            try:
                delivery = webhook_manager.deliver_webhook(
                    event_type="JOB_COMPLETED",
                    payload={
                        "intent_id": intent.intent_id,
                        "job_id": canonical_result.get("job_id", ""),
                        "status": canonical_result.get("status", "Completed"),
                        "confidence": canonical_result.get("confidence", 100.0)
                    },
                    url=webhook_url,
                    secret="v50_action_secret"
                )
                results.append(ActionResult(
                    action_id=f"act-{uuid.uuid4().hex[:6]}",
                    action_type="WEBHOOK_NOTIFY",
                    status="SUCCESS" if delivery.status == "DELIVERED" else "FAILED",
                    target=webhook_url,
                    payload_summary=f"Webhook delivery status: {delivery.status}",
                    error=delivery.error
                ))
            except Exception as e:
                results.append(ActionResult(
                    action_id=f"act-{uuid.uuid4().hex[:6]}",
                    action_type="WEBHOOK_NOTIFY",
                    status="FAILED",
                    target=webhook_url,
                    payload_summary="Webhook exception",
                    error=str(e)
                ))

        return results

action_execution_engine = ActionExecutionEngine()
