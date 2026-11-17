"""Policy gates shared by repair and release agents."""

import fnmatch
import os
from typing import Iterable, List


DEFAULT_PROTECTED_PATTERNS = (
    ".github/workflows/*",
    ".env",
    ".env.*",
    "*.pem",
    "*.key",
    "config/agent_policy.yaml",
    "agents/policy.py",
)


class AgentPolicy:
    def __init__(
        self,
        editable_patterns: Iterable[str] = ("*.py", "*.js", "*.ts", "*.java", "*.go", "*.rs"),
        protected_patterns: Iterable[str] = DEFAULT_PROTECTED_PATTERNS,
        max_changed_files: int = 5,
        max_changed_lines: int = 250,
        max_attempts: int = 3,
    ):
        self.editable_patterns = tuple(editable_patterns)
        self.protected_patterns = tuple(protected_patterns)
        self.max_changed_files = max_changed_files
        self.max_changed_lines = max_changed_lines
        self.max_attempts = max_attempts

    def can_edit(self, path: str) -> bool:
        normalized = path.replace("\\", "/").lstrip("./")
        if any(fnmatch.fnmatch(normalized, pattern) for pattern in self.protected_patterns):
            return False
        return any(fnmatch.fnmatch(normalized, pattern) for pattern in self.editable_patterns)

    def validate_changed_files(self, paths: Iterable[str]) -> List[str]:
        changed = [path.replace("\\", "/") for path in paths]
        if len(changed) > self.max_changed_files:
            raise ValueError("patch changes too many files")
        denied = [path for path in changed if not self.can_edit(path)]
        if denied:
            raise ValueError("patch contains protected or unsupported files: " + ", ".join(denied))
        return changed

    def validate_attempt(self, attempt: int) -> None:
        if attempt > self.max_attempts:
            raise ValueError("repair attempt limit exceeded")


def redact_secrets(value: str) -> str:
    """Redact common CI secret formats before persistence or model calls."""
    import re

    patterns = (
        r"(?i)(authorization\s*:\s*bearer\s+)[^\s]+",
        r"(?i)(token|password|secret|api[_-]?key)\s*[=:]\s*[^\s]+",
    )
    result = value
    for pattern in patterns:
        result = re.sub(pattern, r"\1[REDACTED]", result)
    return result
