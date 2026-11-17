"""Safe repository inspection and unified-diff application."""

import os
import re
import subprocess
from pathlib import Path
from typing import List

from agents.policy import AgentPolicy


class RepositoryTool:
    def __init__(self, root: str = ".", policy: AgentPolicy = None):
        self.root = Path(root).resolve()
        self.policy = policy or AgentPolicy()

    def _safe_path(self, relative_path: str) -> Path:
        candidate = (self.root / relative_path).resolve()
        if self.root not in candidate.parents and candidate != self.root:
            raise ValueError("path escapes repository")
        return candidate

    def read_file(self, relative_path: str, max_bytes: int = 100_000) -> str:
        path = self._safe_path(relative_path)
        if not path.is_file():
            raise FileNotFoundError(relative_path)
        return path.read_text(encoding="utf-8", errors="replace")[:max_bytes]

    def changed_files(self) -> List[str]:
        result = subprocess.run(
            ["git", "diff", "--name-only"],
            cwd=self.root,
            text=True,
            capture_output=True,
            check=True,
        )
        return [line for line in result.stdout.splitlines() if line]

    def context_for_failure(self, logs: str, max_files: int = 6, max_bytes: int = 60_000) -> str:
        """Collect only source files named by common stack-trace formats."""
        candidates = re.findall(r"(?<![\w/])([A-Za-z0-9_.-]+(?:/[A-Za-z0-9_.-]+)*\.(?:py|js|ts|java|go|rs))(?::\d+)?", logs)
        seen = []
        for candidate in candidates:
            normalized = candidate.replace("\\", "/")
            if normalized not in seen and self.policy.can_edit(normalized):
                seen.append(normalized)
        sections = []
        total = 0
        for path in seen[:max_files]:
            try:
                content = self.read_file(path, max_bytes=max_bytes - total)
            except (FileNotFoundError, ValueError):
                continue
            section = f"\n--- {path} ---\n{content}"
            if total + len(section) > max_bytes:
                break
            sections.append(section)
            total += len(section)
        return "".join(sections)

    def apply_patch(self, patch: str) -> List[str]:
        if not patch or "diff --git " not in patch:
            raise ValueError("only unified git diffs are accepted")
        paths = re.findall(r"^(?:--- a/|\+\+\+ b/)(.+)$", patch, re.MULTILINE)
        paths = [path for path in paths if path != "/dev/null"]
        self.policy.validate_changed_files(paths)
        changed_lines = sum(
            1 for line in patch.splitlines()
            if (line.startswith("+") and not line.startswith("+++"))
            or (line.startswith("-") and not line.startswith("---"))
        )
        if changed_lines > self.policy.max_changed_lines:
            raise ValueError("patch changes too many lines")
        subprocess.run(
            ["git", "apply", "--check", "--whitespace=error"],
            cwd=self.root,
            input=patch,
            text=True,
            capture_output=True,
            check=True,
        )
        subprocess.run(
            ["git", "apply", "--whitespace=error"],
            cwd=self.root,
            input=patch,
            text=True,
            capture_output=True,
            check=True,
        )
        return self.changed_files()
