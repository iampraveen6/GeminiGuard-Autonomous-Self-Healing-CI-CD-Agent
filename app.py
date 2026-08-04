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
        
        # Add quota status
        try:
            from core.gemini_client import usage_tracker, FREE_TIER_DAILY_LIMIT
            remaining = FREE_TIER_DAILY_LIMIT - usage_tracker["requests_today"]
            usage_percent = (usage_tracker["requests_today"] / FREE_TIER_DAILY_LIMIT) * 100
            
            st.divider()
            st.caption("API Quota Status")
            col3, col4 = st.columns(2)
            with col3:
                st.metric("Requests Today", usage_tracker["requests_today"])
            with col4:
                st.metric("Remaining", remaining)
            
            # Progress bar
            st.progress(usage_percent / 100, text=f"Daily Usage: {usage_percent:.1f}%")
            
            if remaining <= 2:
                st.warning("Approaching rate limit - will switch to test mode automatically")
        except Exception as e:
            st.caption(f"Quota status unavailable: {str(e)}")

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
    # Handle different error types
    if not result or ("error" in result and result["error"]):
        error_type = result.get("error", "Unknown error")
        
        if error_type == "RATE_LIMIT_APPROACHED":
            st.warning("Rate Limit Approaching")
            st.info(result.get("message", "Please try again later"))
            if result.get("mock_data"):
                st.info("Using test mode responses until quota resets")
                # Use the mock data
                result = result.get("mock_data")
        elif error_type == "QUOTA_EXCEEDED":
            st.error("API Quota Exceeded")
            st.warning(result.get("message", "Daily limit reached"))
            st.info(f"Usage: {result.get('usage_info', 'Unknown')}")
            st.info(f"Retry after: {result.get('retry_after', '24 hours')}")
            if result.get("mock_data"):
                st.info("Using test mode responses")
                result = result.get("mock_data")
        else:
            st.error(f"Analysis failed: {error_type}")
            st.stop()
    
    # If we got here, we have a valid result (either real or mock)
    if result and isinstance(result, dict) and result.get("auto_test_mode"):
        st.info("Running in test mode (rate limit protection)")
    
    # Ensure result is valid before proceeding
    if not result or not isinstance(result, dict):
        st.error("Analysis returned invalid result")
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
                    
                    # Show error type if present
                    if "Error Type:" in pr_result:
                        error_type_line = [line for line in pr_result.split('\n') if "Error Type:" in line][0]
                        st.info(error_type_line.strip())
                    
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
                    # Show error type and guidance prominently
                    if "Error Type:" in pr_result:
                        st.error("PR Creation Disabled")
                        
                        # Extract error type and guidance
                        lines = pr_result.split('\n')
                        for line in lines:
                            if "Error Type:" in line:
                                st.warning(line.strip())
                            elif "Guidance:" in line:
                                st.info(line.strip())
                    
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