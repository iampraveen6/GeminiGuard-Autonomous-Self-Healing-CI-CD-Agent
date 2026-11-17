"""Event-driven, PR-only autonomous repair agent."""

import hashlib
import uuid
from dataclasses import asdict
from typing import Callable, Dict, Optional

from agents.analyzer import run_analysis
from agents.contracts import AgentRun, Diagnosis, FailureEvent
from agents.policy import AgentPolicy, redact_secrets
from agents.tools.repository import RepositoryTool
from agents.tools.sandbox import run_validation
from core.fix_ranker import rank_fixes


class RepairAgent:
    """Diagnose and validate repairs without merging or deploying them."""

    def __init__(
        self,
        root: str = ".",
        policy: Optional[AgentPolicy] = None,
        analysis: Callable = run_analysis,
        publish: Optional[Callable] = None,
    ):
        self.policy = policy or AgentPolicy()
        self.repository = RepositoryTool(root, self.policy)
        self.analysis = analysis
        self.publish = publish

    @staticmethod
    def fingerprint(logs: str, sha: str = "") -> str:
        source = f"{sha}:{redact_secrets(logs)[:20_000]}"
        return hashlib.sha256(source.encode("utf-8")).hexdigest()[:16]

    @staticmethod
    def normalize_patch(patch: str) -> str:
        """Accept a plain diff or a single fenced diff, never arbitrary prose."""
        if not isinstance(patch, str):
            return ""
        patch = patch.strip()
        if patch.startswith("```") and patch.endswith("```"):
            lines = patch.splitlines()
            patch = "\n".join(lines[1:-1]).strip()
        return patch + "\n" if "diff --git " in patch else ""

    def run(self, event: FailureEvent, patch: str = "", command: str = "python -m pytest -q") -> AgentRun:
        correlation_id = event.correlation_id or str(uuid.uuid4())
        event.fingerprint = event.fingerprint or self.fingerprint(event.logs, event.sha)
        run = AgentRun(correlation_id, "repair", "received", event=event)
        self.policy.validate_attempt(1)

        context = self.repository.context_for_failure(event.logs)
        analysis_input = redact_secrets(event.logs) + context
        raw = self.analysis(analysis_input, test_mode=None)
        if not isinstance(raw, dict) or raw.get("error") or not raw.get("fixes"):
            run.status = "stopped"
            run.reason = "analysis did not produce actionable candidates"
            return run

        ranked = rank_fixes(raw["fixes"])
        run.diagnosis = Diagnosis(
            root_cause=raw.get("root_cause", "Unknown"),
            fixes=ranked,
            error_type=raw.get("error_type", "unknown"),
            confidence=float(ranked[0].get("confidence", 0)) if ranked else 0,
        )
        run.status = "diagnosed"

        patch = self.normalize_patch(patch or raw.get("patch", ""))
        if not patch:
            run.status = "stopped"
            run.reason = "no executable unified diff was supplied"
            return run

        try:
            changed = self.repository.apply_patch(patch)
        except (OSError, ValueError):
            run.status = "stopped"
            run.reason = "patch rejected by repository policy or git"
            return run

        validation = run_validation(self.repository.root, command)
        validation.changed_files = changed
        run.validation = validation
        if not validation.passed:
            run.status = "stopped"
            run.reason = "candidate patch did not pass validation"
            return run

        if self.publish:
            publish_result = self.publish(event, patch, run)
            run.metadata["publish_result"] = publish_result
            if isinstance(publish_result, dict) and publish_result.get("status") not in {"created", "existing"}:
                run.status = "stopped"
                run.reason = publish_result.get("reason", "validated patch could not be published")
                return run
        run.status = "published"
        run.reason = "validated patch is ready for PR publication"
        return run

    @staticmethod
    def audit_record(run: AgentRun) -> Dict:
        return asdict(run)
