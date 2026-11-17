"""GitHub Actions event normalization for the repair agent."""

import hashlib
import json
import os
from pathlib import Path

from agents.contracts import FailureEvent
from agents.policy import redact_secrets


def load_failure_event(path: str = "github_event.json", logs_path: str = "logs.txt") -> FailureEvent:
    payload = {}
    if Path(path).is_file():
        payload = json.loads(Path(path).read_text(encoding="utf-8"))
    logs = Path(logs_path).read_text(encoding="utf-8", errors="replace") if Path(logs_path).is_file() else ""
    repository = payload.get("repository", {}).get("full_name") or os.getenv("REPO_NAME", "")
    workflow = payload.get("workflow_run", {}).get("name", "")
    run_id = str(payload.get("workflow_run", {}).get("id", os.getenv("GITHUB_RUN_ID", "")))
    sha = payload.get("workflow_run", {}).get("head_sha") or os.getenv("GITHUB_SHA", "")
    branch = payload.get("workflow_run", {}).get("head_branch") or os.getenv("GITHUB_REF_NAME", "")
    fingerprint = hashlib.sha256(f"{repository}:{run_id}:{redact_secrets(logs)[:20000]}".encode()).hexdigest()[:16]
    return FailureEvent(repository, sha, redact_secrets(logs), workflow, run_id, branch, fingerprint)
