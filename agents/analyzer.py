import json
import sys
from core.gemini_client import analyze_failure


def run_analysis(logs, test_mode=None):
    try:
        print("Analyzing failure log...\n")
    except UnicodeEncodeError:
        # Fallback if console doesn't support emojis
        sys.stdout.write("Analyzing failure log...\n")

    raw = analyze_failure(logs, test_mode)

    # Case 1: Already proper dict (expected)
    if isinstance(raw, dict):
        return raw

    # Case 2: Raw string → try to parse JSON
    try:
        import json
        parsed = json.loads(raw)
        return parsed
    except (TypeError, ValueError, json.JSONDecodeError):
        return {"error": "Model returned malformed structured output"}
