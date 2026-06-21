import json
import os

DB_FILE = "memory_db.json"


# ------------------------
# ✅ Load Memory
# ------------------------
def load_memory():
    if not os.path.exists(DB_FILE):
        return []

    try:
        with open(DB_FILE, "r") as f:
            return json.load(f)
    except Exception:
        # ✅ Handle corrupted JSON safely
        return []


# ------------------------
# ✅ Save Memory
# ------------------------
def save_memory(entry):
    """
    Save a new memory entry.

    Expected format:
    {
        "timestamp": "...",
        "logs": "...",
        "selected_fix": {
            "description": "..."
        },
        "status": "success" or "failed"
    }
    """

    if not isinstance(entry, dict):
        return

    data = load_memory()

    # ✅ Basic validation
    if "selected_fix" not in entry:
        return

    if "description" not in entry.get("selected_fix", {}):
        return

    if "status" not in entry:
        entry["status"] = "unknown"

    data.append(entry)

    try:
        with open(DB_FILE, "w") as f:
            json.dump(data, f, indent=4)
    except Exception as e:
        print(f"⚠️ Failed to save memory: {e}")


# ------------------------
# ✅ Optional Utility
# ------------------------
def clear_memory():
    """Reset memory database"""
    with open(DB_FILE, "w") as f:
        json.dump([], f, indent=4)


def get_memory_stats():
    """Quick stats for debugging"""
    data = load_memory()

    total = len(data)
    success = sum(1 for d in data if d.get("status") == "success")
    failed = sum(1 for d in data if d.get("status") == "failed")

    return {
        "total": total,
        "success": success,
        "failed": failed
    }