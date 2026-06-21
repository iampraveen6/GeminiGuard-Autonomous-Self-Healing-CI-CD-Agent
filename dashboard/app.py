import sys
import os

# ✅ Fix imports
BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
sys.path.append(BASE_DIR)

import streamlit as st
from datetime import datetime

# Project imports
from agents.analyzer import run_analysis
from core.fix_ranker import rank_fixes
from memory.store import load_memory, save_memory
from integrations.github_pr import create_fix_pr

# ✅ Paths
MEMORY_FILE = os.path.join(BASE_DIR, "memory_db.json")

# ---------------- CONFIG ----------------
st.set_page_config(page_title="GeminiGuard", layout="wide")
st.title("🚀 GeminiGuard - AI Self-Healing CI/CD")

# ---------------- SESSION STATE ----------------
if "analysis_result" not in st.session_state:
    st.session_state.analysis_result = None

# ---------------- METRICS ----------------
data = load_memory()

total = len(data)
success = sum(1 for d in data if d.get("status") == "success")
rate = (success / total * 100) if total else 0

col1, col2, col3 = st.columns(3)
col1.metric("📦 Total Issues", total)
col2.metric("✅ Fixed", success)
col3.metric("📈 Success Rate", f"{rate:.1f}%")

st.divider()

# ---------------- INPUT ----------------
st.subheader("🧠 Analyze CI/CD Logs")

logs = st.text_area("Paste logs here:")

# ✅ Analyze
if st.button("🔍 Analyze"):
    if not logs.strip():
        st.warning("Please enter logs")
    else:
        with st.spinner("Analyzing with Gemini..."):
            st.session_state.analysis_result = run_analysis(logs)

# ✅ Use stored result
result = st.session_state.analysis_result

if result:
    # ✅ Correct error handling
    if not result or ("error" in result and result["error"]):
        st.error(result.get("error", "Analysis failed"))
        st.stop()

    st.success("✅ Analysis Complete")

    st.subheader("📌 Root Cause")
    st.info(result.get("root_cause", "Unknown"))

    fixes = result.get("fixes", [])
    ranked = rank_fixes(fixes)

    st.subheader("🛠 Suggested Fixes")

    for i, fix in enumerate(ranked):
        st.write(f"### Option {i+1}")
        st.write(f"**Description:** {fix['description']}")
        st.write(f"✅ Confidence: {fix['confidence']}")
        st.write(f"⚠ Risk: {fix['risk']}")
        st.write(f"🧮 Score: {fix.get('_score')}")
        st.divider()

    # ✅ Select fix
    selected = st.selectbox(
        "Choose Fix to Apply",
        ranked,
        format_func=lambda x: x["description"]
    )

    # ✅ Apply + PR
    if st.button("🚀 Apply Fix & Create PR"):
        status = "success" if selected["confidence"] > 0.6 else "failed"

        entry = {
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "logs": logs,
            "selected_fix": selected,
            "status": status
        }

        save_memory(entry)

        if status == "success":
            st.success("✅ Fix Applied Successfully")

            with st.spinner("Creating GitHub PR..."):
                pr_result = create_fix_pr(selected["description"])

                if "http" in pr_result:
                    st.success("🎉 PR Created Successfully!")
                    st.markdown(f"👉 [View Pull Request]({pr_result})")
                else:
                    st.info(pr_result)

        else:
            st.error("❌ Fix validation failed")

# ---------------- HISTORY ----------------
st.divider()
st.subheader("📊 Fix History")

history_data = load_memory()

if not history_data:
    st.info("No execution history found yet.")
else:
    for item in reversed(history_data):
        timestamp = item.get('timestamp', 'Unknown Time')
        status = item.get('status', 'UNKNOWN').upper()

        with st.expander(f"{timestamp} - {status}"):
            st.write(item)

# ---------------- SIDEBAR ----------------
st.sidebar.title("⚙️ GeminiGuard")

st.sidebar.markdown("""
### 🔹 Features
- Gemini AI Log Analysis
- Root Cause Detection
- Multi-Fix Suggestions
- Auto Fix + PR Creation
- Memory Learning
""")

# ✅ Clear memory
if st.sidebar.button("🗑 Clear Memory"):
    if os.path.exists(MEMORY_FILE):
        os.remove(MEMORY_FILE)
        st.sidebar.success("Memory cleared! Please refresh.")
