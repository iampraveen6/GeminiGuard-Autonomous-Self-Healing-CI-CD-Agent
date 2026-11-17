"""Separate post-deployment health and rollback policy boundary."""

from dataclasses import dataclass
from typing import Callable, Optional


@dataclass
class DeploymentEvent:
    deployment_id: str
    version: str
    rollback_version: Optional[str] = None
    environment: str = "staging"


@dataclass
class ReleaseDecision:
    status: str
    reason: str
    rollback_attempted: bool = False


class ReleaseAgent:
    def __init__(
        self,
        health_check: Callable[[], bool],
        rollback: Callable[[str], bool],
        dry_run: bool = True,
        allowed_environments=("staging",),
        max_rollbacks: int = 1,
    ):
        self.health_check = health_check
        self.rollback = rollback
        self.dry_run = dry_run
        self.allowed_environments = set(allowed_environments)
        self.max_rollbacks = max_rollbacks
        self.rollback_count = 0

    def observe(self, event: DeploymentEvent) -> ReleaseDecision:
        if event.environment not in self.allowed_environments:
            return ReleaseDecision("blocked", "environment is not allow-listed")
        if self.health_check():
            return ReleaseDecision("healthy", "deployment passed health checks")
        if not event.rollback_version:
            return ReleaseDecision("escalated", "deployment unhealthy and no rollback target exists")
        if self.rollback_count >= self.max_rollbacks:
            return ReleaseDecision("blocked", "rollback frequency limit exceeded")
        if self.dry_run:
            return ReleaseDecision("rollback_pending", "dry-run: rollback would be requested")
        self.rollback_count += 1
        if self.rollback(event.rollback_version):
            if self.health_check():
                return ReleaseDecision("rolled_back", "rollback completed and health recovered", True)
            return ReleaseDecision("rollback_failed", "rollback completed but health did not recover", True)
        return ReleaseDecision("rollback_failed", "rollback command failed", True)
