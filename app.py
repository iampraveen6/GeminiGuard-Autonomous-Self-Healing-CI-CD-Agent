# -*- coding: utf-8 -*-
import sys
import os

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import streamlit as st
from datetime import datetime

# Professional system status in collapsible section
if os.getenv('DEBUG_ENV') == 'true':
    with st.expander("🔧 System Status (Debug)", expanded=False):
        st.caption("Environment Configuration")
        
        col1, col2 = st.columns(2)
        with col1:
            api_key_status = "✅ Connected" if os.getenv('GEMINI_API_KEY') else "❌ Not Configured"
            st.metric("Gemini API", api_key_status)
        with col2:
            test_mode = os.getenv('TEST_MODE', 'false')
            mode_status = "🧪 Test Mode" if test_mode == 'true' else "🚀 Production"
            st.metric("Operation Mode", mode_status)
        
        st.divider()
        st.caption("System Information")
        st.write(f"Python Version: {sys.version.split()[0]}")
        st.write(f"Working Directory: {os.getcwd()}")

# Project imports
from agents.analyzer import run_analysis
from core.fix_ranker import rank_fixes
from memory.store import load_memory, save_memory
from integrations.github_pr import create_fix_pr

# Paths
MEMORY_FILE = "memory_db.json"

# ---------------- CONFIG ----------------
st.set_page_config(page_title="GeminiGuard", layout="wide")
st.title("GeminiGuard - AI Self-Healing CI/CD")

# ---------------- SESSION STATE ----------------
if "analysis_result" not in st.session_state:
    st.session_state.analysis_result = None

# ---------------- METRICS ----------------
data = load_memory()

total = len(data)
success = sum(1 for d in data if d.get("status") == "success")
rate = (success / total * 100) if total else 0

col1, col2, col3 = st.columns(3)
col1.metric("Total Issues", total)
col2.metric("Fixed", success)
col3.metric("Success Rate", f"{rate:.1f}%")

st.divider()

# ---------------- INPUT ----------------
st.subheader("Analyze CI/CD Logs")

logs = st.text_area("Paste logs here:")

# Analyze
if st.button("Analyze"):
    if not logs.strip():
        st.warning("Please enter logs")
    else:
        with st.spinner("Analyzing with Gemini..."):
            st.session_state.analysis_result = run_analysis(logs)

# Use stored result
result = st.session_state.analysis_result

if result:
    # Correct error handling
    if not result or ("error" in result and result["error"]):
        st.error(result.get("error", "Analysis failed"))
        st.stop()

    st.success("Analysis Complete")

    st.subheader("Root Cause")
    st.info(result.get("root_cause", "Unknown"))

    fixes = result.get("fixes", [])
    ranked = rank_fixes(fixes)

    st.subheader("Suggested Fixes")

    for i, fix in enumerate(ranked):
        st.write(f"### Option {i+1}")
        st.write(f"**Description:** {fix['description']}")
        st.write(f"Confidence: {fix['confidence']}")
        st.write(f"Risk: {fix['risk']}")
        st.write(f"Score: {fix.get('_score')}")
        st.divider()

    # Select fix
    selected = st.selectbox(
        "Choose Fix to Apply",
        ranked,
        format_func=lambda x: x["description"]
    )

    # Branch type selection
    branch_type = st.radio(
        "Branch Type",
        ["feature", "hotfix"],
        help="Feature: For new functionality | Hotfix: For urgent bug fixes"
    )

    # Apply + PR
    if st.button("Apply Fix & Create PR"):
        status = "success" if selected["confidence"] > 0.6 else "failed"

        entry = {
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "logs": logs,
            "selected_fix": selected,
            "status": status
        }

        save_memory(entry)

        if status == "success":
            st.success("Fix Applied Successfully")

            with st.spinner("Creating GitHub PR..."):
                pr_result = create_fix_pr(selected["description"], logs, branch_type)

                if "http" in pr_result:
                    st.success("PR Created Successfully!")
                    
                    # Extract PR URL from detailed result
                    pr_url = pr_result.split("\n\n")[0].split("PR Created: ")[1]
                    st.markdown(f"[View Pull Request]({pr_url})")
                    
                    # Show detailed validation results
                    if "Detailed Report:" in pr_result:
                        with st.expander("Validation Report", expanded=True):
                            detailed_part = pr_result.split("Detailed Report:")[1].strip()
                            
                            # Display each check with appropriate styling
                            for line in detailed_part.split('\n'):
                                if line.strip():
                                    if '✅' in line:
                                        st.success(line.strip())
                                    elif '❌' in line:
                                        st.error(line.strip())
                                    else:
                                        st.info(line.strip())
                else:
                    st.warning("PR Creation Failed")
                    
                    # Show detailed validation report for failures
                    if "Detailed Report:" in pr_result:
                        with st.expander("Validation Report", expanded=True):
                            detailed_part = pr_result.split("Detailed Report:")[1].strip()
                            
                            # Display each check with appropriate styling
                            for line in detailed_part.split('\n'):
                                if line.strip():
                                    if '✅' in line:
                                        st.success(line.strip())
                                    elif '❌' in line:
                                        st.error(line.strip())
                                    else:
                                        st.info(line.strip())

        else:
            st.error("Fix validation failed")

# ---------------- HISTORY ----------------
st.divider()
st.subheader("Fix History")

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
st.sidebar.title("GeminiGuard")

st.sidebar.markdown("""
### Features
- Gemini AI Log Analysis
- Root Cause Detection
- Multi-Fix Suggestions
- Auto Fix + PR Creation
- Memory Learning
""")

# Clear memory
if st.sidebar.button("Clear Memory"):
    if os.path.exists(MEMORY_FILE):
        os.remove(MEMORY_FILE)
        st.sidebar.success("Memory cleared! Please refresh.")