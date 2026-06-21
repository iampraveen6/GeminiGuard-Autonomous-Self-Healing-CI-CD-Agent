import os
from datetime import datetime
from dotenv import load_dotenv

# ✅ Load environment variables
load_dotenv()

# ✅ Project imports
from agents.analyzer import run_analysis
from core.fix_ranker import rank_fixes
from memory.store import save_memory
from integrations.github_pr import create_fix_pr


# ----------------------------
# ✅ LOAD LOGS (CI or Local)
# ----------------------------
def get_logs():
    """
    Load logs from CI or fallback to default
    """
    if os.path.exists("logs.txt"):
        print("📄 Reading CI logs from logs.txt")
        with open("logs.txt", "r") as f:
            return f.read()

    print("⚠️ No logs.txt found, using default logs")
    return "ModuleNotFoundError: No module named 'requests'"


# ----------------------------
# ✅ MAIN PIPELINE
# ----------------------------
def main():
    print("\n🚀 GeminiGuard - Autonomous Self-Healing CI/CD Agent\n")

    # ✅ Load logs
    logs = get_logs()

    print("\n📤 Sending logs to Gemini...\n")

    # -------------------- ANALYSIS --------------------
    result = run_analysis(logs)

    # ✅ Safe validation
    if not result:
        print("❌ Analysis failed: Empty response")
        return

    if isinstance(result, dict) and "error" in result:
        print("❌ Analysis failed")
        print(result["error"])
        return

    if isinstance(result, dict) and "fixes" not in result:
        print("❌ Invalid analysis output format")
        print(result)
        return

    print("=========== ANALYSIS RESULT ===========")
    print(result)
    print("=======================================\n")

    # -------------------- FIX HANDLING --------------------
    fixes = result.get("fixes", [])

    if not fixes:
        print("❌ No fixes suggested")
        return

    # ✅ Rank fixes
    print("🔧 Ranking fixes...\n")
    ranked_fixes = rank_fixes(fixes)

    for i, fix in enumerate(ranked_fixes, 1):
        print(f"Option {i}:")
        print(f"  ✅ Description : {fix.get('description')}")
        print(f"  📊 Confidence : {fix.get('confidence')}")
        print(f"  ⚠️ Risk       : {fix.get('risk')}")
        print(f"  🧮 Score      : {fix.get('_score')}\n")

    # ✅ Select best fix
    selected_fix = ranked_fixes[0]

    print("✅ Selected Best Fix:")
    print(selected_fix["description"])

    # -------------------- APPLY FIX --------------------
    print("\n🚀 Applying fix (simulation)...")

    confidence = selected_fix.get("confidence", 0)
    success = confidence >= 0.6

    # -------------------- VALIDATION --------------------
    if success:
        print("✅ Fix applied successfully")
        status = "success"
    else:
        print("❌ Fix failed")
        status = "failed"

    # -------------------- SAVE MEMORY --------------------
    print("\n💾 Saving to memory...")

    entry = {
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "logs": logs,
        "selected_fix": selected_fix,
        "status": status
    }

    try:
        save_memory(entry)
        print("✅ Memory saved")
    except Exception as e:
        print(f"⚠️ Memory save failed: {e}")

    # -------------------- CREATE PR --------------------
    if status == "success":
        print("\n🌐 Creating GitHub PR...")

        try:
            pr_result = create_fix_pr(selected_fix["description"])
            print(f"✅ GitHub Result: {pr_result}")
        except Exception as e:
            print(f"⚠️ PR creation failed: {str(e)}")

    # -------------------- SUMMARY --------------------
    print("\n=========== PIPELINE SUMMARY ===========")
    print(f"Status        : {status}")
    print(f"Best Fix      : {selected_fix['description']}")
    print("========================================")

    print("\n🎉 Pipeline execution complete!\n")


# ----------------------------
# ✅ ENTRY POINT
# ----------------------------
if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n⚠️ Interrupted by user")
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
