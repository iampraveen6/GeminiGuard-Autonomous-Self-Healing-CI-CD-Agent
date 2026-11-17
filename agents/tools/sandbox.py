"""Bounded validation runner for candidate repairs."""

import subprocess
import time
from pathlib import Path

from agents.contracts import ValidationResult


def run_validation(root: str = ".", command: str = "python -m pytest -q", timeout: int = 300) -> ValidationResult:
    started = time.monotonic()
    try:
        completed = subprocess.run(
            command,
            cwd=Path(root),
            shell=True,
            text=True,
            capture_output=True,
            timeout=timeout,
        )
        output = (completed.stdout + "\n" + completed.stderr).strip()
        return ValidationResult(
            passed=completed.returncode == 0,
            command=command,
            exit_code=completed.returncode,
            output=output[-20_000:],
            duration_seconds=round(time.monotonic() - started, 3),
        )
    except subprocess.TimeoutExpired as exc:
        return ValidationResult(
            passed=False,
            command=command,
            exit_code=124,
            output=str(exc),
            duration_seconds=round(time.monotonic() - started, 3),
        )
