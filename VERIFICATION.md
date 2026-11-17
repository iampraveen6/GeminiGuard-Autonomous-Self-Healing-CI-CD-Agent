# GeminiGuard Verification Guide

This document explains how to inspect and verify the autonomous repair and release-agent changes without accidentally creating a GitHub pull request, merging code, or performing a deployment.

## 1. Inspect the Changes

Run these commands from the repository root:

```powershell
git status --short
git diff --stat
git diff -- .github/workflows/ci.yml main.py agents integrations memory config
```

The main implementation areas are:

| Area | Files | What to verify |
| --- | --- | --- |
| CI orchestration | `.github/workflows/ci.yml`, `.github/workflows/autonomous-repair.yml` | Normal CI, `workflow_run`, permissions, and `ai-fix/*` recursion prevention |
| CLI orchestration | `main.py`, `integrations/github_actions.py` | Event loading, agent execution, and audit persistence |
| Repair flow | `agents/repair_agent.py` | Diagnosis, patch normalization, policy validation, test execution, and PR-only behavior |
| Safety policy | `agents/policy.py`, `config/agent_policy.yaml` | Protected paths, editable extensions, file/line limits, and attempt limits |
| Repository tools | `agents/tools/repository.py`, `agents/tools/sandbox.py` | Unified-diff checking, patch application, and bounded validation |
| GitHub publication | `integrations/github_pr.py` | `ai-fix/...` branch naming and PR creation; no merge or deployment |
| Release flow | `agents/release_agent.py` | Staging allow-list and default dry-run rollback |
| Audit trail | `memory/store.py`, `memory_db.json` | Persisted agent status, diagnosis, validation, and publication results |

## 2. Run the Local Test Suite

Run the full suite:

```powershell
python -m pytest -q
```

Expected result:

```text
9 passed
```

Run only the autonomous-agent tests:

```powershell
python -m pytest -q tests/test_runner.py -k "agent or policy or release or repository"
```

These tests verify that:

- Protected workflow files are rejected.
- Release rollback stays in dry-run mode.
- Repair stops when no executable diff is supplied.
- Workflow deletion patches are rejected.

Also verify that the modules compile:

```powershell
python -m compileall -q agents core integrations memory main.py
```

## 3. Run a Safe Synthetic Repair

The following check uses a temporary Git repository, a stubbed analysis response, and no publisher. It applies a patch and validates it without touching this repository or GitHub:

```powershell
python -c @'
import subprocess
import tempfile
from pathlib import Path

from agents.contracts import FailureEvent
from agents.repair_agent import RepairAgent

with tempfile.TemporaryDirectory() as directory:
    root = Path(directory)
    subprocess.run(["git", "init"], cwd=root, check=True, capture_output=True)
    subprocess.run(["git", "config", "user.email", "verify@example.com"], cwd=root, check=True)
    subprocess.run(["git", "config", "user.name", "Verification"], cwd=root, check=True)

    app = root / "app.py"
    app.write_text("VALUE = 1\n", encoding="utf-8")
    subprocess.run(["git", "add", "app.py"], cwd=root, check=True)
    subprocess.run(["git", "commit", "-m", "initial"], cwd=root, check=True, capture_output=True)

    app.write_text("VALUE = 2\n", encoding="utf-8")
    patch = subprocess.run(
        ["git", "diff", "--", "app.py"],
        cwd=root,
        check=True,
        capture_output=True,
        text=True,
    ).stdout
    app.write_text("VALUE = 1\n", encoding="utf-8")

    agent = RepairAgent(
        root=str(root),
        analysis=lambda logs, test_mode=None: {
            "root_cause": "incorrect value",
            "fixes": [
                {
                    "description": "Update app value",
                    "confidence": 0.99,
                    "risk": "low",
                }
            ],
        },
    )
    result = agent.run(
        FailureEvent("owner/repo", "abc123", "app.py:1 AssertionError"),
        patch=patch,
        command='python -c "assert open(\'app.py\').read().strip() == \'VALUE = 2\'"',
    )
    print({
        "status": result.status,
        "reason": result.reason,
        "changed_files": result.validation.changed_files,
        "validation_passed": result.validation.passed,
    })
    assert result.status == "published"
    assert result.validation.passed is True
'@
```

The expected output contains:

```text
"status": "published"
"validation_passed": true
"changed_files": ["app.py"]
```

Here, `published` means the candidate is ready for publication. Because no `publish` callback was configured, this command does not create a branch or pull request.

## 4. Check Audit Records

After a local CLI or CI-style run, inspect the audit file:

```powershell
Get-Content memory_db.json
```

Each repair record should include:

- `agent: "repair"`
- A terminal status such as `stopped`, `published`, or `diagnosed`
- A reason
- The event and correlation ID
- Diagnosis details
- Validation command, exit code, and changed files
- Publication metadata when a publisher was configured

Do not treat a `published` status as a merged change. This agent is designed to open a PR only.

## 5. Check the CLI Without Publishing

The CLI accepts a GitHub-style event file and an optional unified diff:

```powershell
python main.py --event-file github_event.json --patch-file candidate.patch
```

Before running it locally:

1. Use a temporary clone or disposable branch.
2. Do not set `GITHUB_TOKEN` or `GITHUB_REPO` unless a real PR is intended.
3. Use a patch that changes only an allowed source file.
4. Confirm the configured validation command passes.
5. Inspect the JSON printed by `main.py`.
6. Inspect `memory_db.json`.

With no GitHub credentials, the publisher will be blocked rather than creating a PR. The working tree may still contain the applied candidate patch, so use a temporary clone or clean it manually after inspection.

## 6. Verify GitHub Actions End to End

Perform this only from a temporary branch. Do not deliberately break the default branch.

1. Confirm repository Actions are enabled.
2. Confirm `GEMINI_API_KEY` is configured as a repository secret.
3. Confirm the workflow has the required permissions:
   - `contents: write`
   - `actions: read`
   - `pull-requests: write`
4. Create a harmless test failure on a branch that does not start with `ai-fix/`.
5. Push the branch and open the failed normal CI run.
6. Confirm the `workflow_run` event starts the `repair` job in `.github/workflows/autonomous-repair.yml`.
7. Inspect the repair job logs and verify:
   - The failed `head_sha` is checked out.
   - The failed logs are downloaded.
   - The event is loaded from `github_event.json`.
   - Gemini returns an actionable diagnosis.
   - The candidate patch passes policy checks.
   - The validation command passes.
8. If publication succeeds, verify:
   - A branch named `ai-fix/...` is created.
   - A pull request is opened against the default branch.
   - The pull request is not merged automatically.
   - No deployment or rollback occurs.
9. Confirm that the `ai-fix/...` branch does not start another repair run.

The workflow currently contains:

```yaml
python main.py --event-file github_event.json || true
```

Therefore, a green repair job does not necessarily mean that a repair succeeded. Always inspect the printed JSON, job logs, pull-request state, and audit record.

## 7. Verify Release-Agent Safety

The release agent defaults to dry-run mode and only allows staging:

```yaml
release:
  mode: dry_run
  allowed_environments:
    - staging
  max_rollbacks: 1
```

The existing test confirms that an unhealthy staging deployment with a rollback target returns `rollback_pending` and does not call the rollback function.

Expected safety behavior:

- Healthy deployment → `healthy`
- Unhealthy deployment without a rollback target → `escalated`
- Production or another non-allow-listed environment → `blocked`
- Dry-run rollback → `rollback_pending`
- Enabled rollback after the limit → `blocked`

## 8. Success Criteria

The implementation is behaving as intended when all of the following are true:

- The test suite passes.
- Protected files and unsupported extensions are rejected.
- A valid source patch applies cleanly.
- The validation command runs and passes.
- An audit entry is written.
- Local checks do not create a PR.
- GitHub repair creates only an `ai-fix/...` branch and PR.
- No merge or deployment occurs automatically.
- Agent-created branches do not recursively trigger repairs.
- Release rollback remains dry-run until an explicit deployment adapter and policy are configured.

## Troubleshooting

### The workflow is green but no PR exists

Check the `Diagnose failure` step logs and `memory_db.json`. The workflow uses `|| true`, so the job can be green when the agent stops because there is no actionable diagnosis, no patch, failed validation, missing credentials, or a blocked policy decision.

### The agent reports no executable diff

Provide a real unified Git diff containing `diff --git`, or allow Gemini to return one in the structured `patch` field. A prose description of a fix is intentionally not executable.

### A patch is rejected

Check whether it:

- Changes more than five files.
- Changes more than 250 lines.
- Touches `.github/workflows/*`, `.env*`, key/certificate files, or policy files.
- Uses an unsupported source extension.
- Deletes a protected workflow.

### A PR was not created

Check `GITHUB_TOKEN`, `REPO_NAME` or `GITHUB_REPO`, repository write permissions, and whether an open PR already exists for the generated `ai-fix/...` branch.
