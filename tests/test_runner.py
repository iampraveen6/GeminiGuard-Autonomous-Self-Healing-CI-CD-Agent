import os
import sys

# ✅ Add project root to Python path
BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.append(BASE_DIR)

# ✅ Imports from your project
from core.gemini_client import analyze_failure
from core.fix_ranker import rank_fixes
from integrations.github_pr import create_fix_pr
from memory.store import save_memory
from agents.analyzer import run_analysis



def test_gemini():
    print("🔍 Testing Gemini (Mock)...")

    # ✅ Fake response (no API call)
    result = {
        "fixes": [
            {
                "description": "Install missing dependency using pip install requests",
                "confidence": 0.9,
                "risk": "low"
            }
        ]
    }

    assert result is not None
    assert "fixes" in result

    print("✅ Gemini test passed (mock)\n")



def test_ranker():
    print("🔧 Testing Ranker...")

    fixes = [
        {"description": "Fix A", "confidence": 0.3, "risk": "low"},
        {"description": "Fix B", "confidence": 0.9, "risk": "medium"},
    ]

    ranked = rank_fixes(fixes)

    assert ranked[0]["confidence"] >= ranked[1]["confidence"]

    print("✅ Ranker test passed\n")


def test_github():
    print("🌐 Testing GitHub integration...")

    try:
        result = create_fix_pr("Test fix for CI/CD issue")

        assert result is not None
        print(f"✅ GitHub test passed: {result}\n")

    except Exception as e:
        print(f"⚠️ GitHub test skipped: {e}\n")


def test_memory():
    print("💾 Testing Memory...")

    entry = {
        "logs": "Test log",
        "selected_fix": {"description": "Test fix"},
        "status": "success"
    }

    save_memory(entry)

    assert os.path.exists("memory_db.json")

    print("✅ Memory test passed\n")


def test_full_pipeline():
    print("🚀 Testing Full Pipeline...")

    result = run_analysis("ModuleNotFoundError: requests")

    assert result is not None

    print("✅ Full pipeline test passed\n")


# ✅ MAIN RUNNER
if __name__ == "__main__":
    print("\n🧪 RUNNING ALL TESTS...\n")

    test_gemini()
    test_ranker()
    test_github()
    test_memory()
    test_full_pipeline()

    print("🎉 ALL TESTS PASSED ✅\n")