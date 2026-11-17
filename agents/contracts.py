"""Shared contracts for autonomous agent runs."""

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


@dataclass
class FailureEvent:
    repository: str
    sha: str
    logs: str
    workflow: str = ""
    run_id: str = ""
    branch: str = ""
    fingerprint: str = ""
    correlation_id: str = ""


@dataclass
class Diagnosis:
    root_cause: str
    fixes: List[Dict[str, Any]]
    error_type: str = "unknown"
    confidence: float = 0.0


@dataclass
class ValidationResult:
    passed: bool
    command: str
    exit_code: int
    output: str = ""
    changed_files: List[str] = field(default_factory=list)
    duration_seconds: float = 0.0


@dataclass
class AgentRun:
    correlation_id: str
    agent: str
    status: str
    reason: str = ""
    attempt: int = 0
    event: Optional[FailureEvent] = None
    diagnosis: Optional[Diagnosis] = None
    validation: Optional[ValidationResult] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
