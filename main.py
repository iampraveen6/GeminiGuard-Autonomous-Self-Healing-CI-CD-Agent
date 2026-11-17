import argparse
import json
from dotenv import load_dotenv

# ✅ Load environment variables
load_dotenv()

# ✅ Project imports
from agents.repair_agent import RepairAgent
from integrations.github_actions import load_failure_event
from integrations.github_pr import publish_validated_patch
from memory.store import save_memory


# ----------------------------
# ✅ LOAD LOGS (CI or Local)
# ----------------------------
def main():
    parser = argparse.ArgumentParser(description="Run the PR-only GeminiGuard repair agent")
    parser.add_argument("--patch-file", help="validated unified diff to apply")
    parser.add_argument("--event-file", default="github_event.json")
    args = parser.parse_args()
    event = load_failure_event(args.event_file)
    patch = open(args.patch_file, encoding="utf-8").read() if args.patch_file else ""
    publisher = lambda current_event, current_patch, run: publish_validated_patch(
        current_event, current_patch, run, root="."
    )
    result = RepairAgent(publish=publisher).run(event, patch=patch)
    save_memory({
        "agent": "repair",
        "status": result.status,
        "reason": result.reason,
        "run": RepairAgent.audit_record(result),
    })
    print(json.dumps({"status": result.status, "reason": result.reason}, indent=2))
    return 0 if result.status in {"published", "diagnosed"} else 1


# ----------------------------
# ✅ ENTRY POINT
# ----------------------------
if __name__ == "__main__":
    raise SystemExit(main())
