import json
import os

MEMORY_FILE = "memory_db.json"


# ------------------------
# ✅ Risk Handling
# ------------------------
def get_risk_score(risk):
    mapping = {
        "low": 1,
        "medium": 2,
        "high": 3
    }
    return mapping.get(str(risk).lower(), 2)


# ------------------------
# ✅ Confidence Handling
# ------------------------
def normalize_confidence(conf):
    try:
        return float(conf)
    except:
        return 0.0


# ------------------------
# ✅ Load Memory
# ------------------------
def load_memory():
    if not os.path.exists(MEMORY_FILE):
        return []

    try:
        with open(MEMORY_FILE, "r") as f:
            return json.load(f)
    except:
        return []


# ------------------------
# ✅ Memory-Based Score
# ------------------------
def calculate_memory_bonus(fix_description, memory_data):
    """
    Check if similar fixes succeeded in past
    """

    score = 0

    for entry in memory_data:
        past_fix = entry.get("selected_fix", {}).get("description", "")
        status = entry.get("status")

        # ✅ simple similarity check
        if fix_description.lower() in past_fix.lower():
            if status == "success":
                score += 2      # reward
            else:
                score -= 1      # penalty

    return score


# ------------------------
# ✅ Score Calculation
# ------------------------
def compute_score(fix, memory_data):
    confidence = normalize_confidence(fix.get("confidence"))
    risk_score = get_risk_score(fix.get("risk"))
    description = fix.get("description", "")

    memory_bonus = calculate_memory_bonus(description, memory_data)

    # ✅ Final formula
    score = (confidence * 10) - risk_score + memory_bonus

    return score


# ------------------------
# ✅ MAIN FUNCTION
# ------------------------
def rank_fixes(fixes):
    if not fixes or not isinstance(fixes, list):
        return []

    memory_data = load_memory()

    for fix in fixes:
        fix["_score"] = compute_score(fix, memory_data)

    ranked = sorted(
        fixes,
        key=lambda x: x["_score"],
        reverse=True
    )

    return ranked


# ------------------------
# ✅ Debug Utility
# ------------------------
def print_ranked_fixes(fixes):
    print("\n🔧 Ranked Fixes:\n")

    for i, fix in enumerate(fixes, 1):
        print(f"Option {i}:")
