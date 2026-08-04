import sys
from core.gemini_client import analyze_failure


def run_analysis(logs):
    try:
        print("Analyzing failure log...\n")
    except UnicodeEncodeError:
        # Fallback if console doesn't support emojis
        sys.stdout.write("Analyzing failure log...\n")

    raw = analyze_failure(logs)

    # Case 1: Already proper dict (expected)
    if isinstance(raw, dict):
        return raw

    # Case 2: Raw string → try to parse JSON
    try:
        import json
        parsed = json.loads(raw)
        return parsed
    except Exception:
        # fallback (never fail pipeline)
        return {
            "root_cause": "Unknown",
            "fixes": [
                {
                    "description": raw,
                    "confidence": 0.5,
                    "risk": "medium"
                }
            ]
        }
