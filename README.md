# 🔮 GeminiGuard: Autonomous Self-Healing CI/CD Agent

> **Your CI/CD pipeline's autonomous guardian.**

GeminiGuard is an AI-powered agent that doesn't just *detect* CI/CD failures — it **understands, diagnoses, and heals them autonomously**. Powered by Google Gemini 2.5 Pro's 1M context window and multi-modal capabilities, it analyzes everything from build logs to UI test screenshots, generates fix PRs automatically, and learns from every resolution to prevent future regressions.

**What makes it different:** Unlike tools that only suggest fixes in comments, GeminiGuard creates actual fix branches, opens PRs, tracks API costs transparently, and integrates with Slack and Jira — all while building a memory of past failures to improve over time.


# 🚀 GeminiGuard: Autonomous Self-Healing CI/CD Agent

GeminiGuard is an AI-powered CI/CD automation system that detects pipeline failures, analyzes root causes using Google Gemini, and autonomously applies safe, ranked fixes.

---

## ✨ Features

- 🔍 Root Cause Analysis using Gemini 1.5 Pro
- 🧠 Multi-strategy fix generation with function calling
- 📊 Fix ranking based on confidence & risk
- ✅ Automated validation with test execution
- 🔄 Self-learning memory system
- 🖥 Observability dashboard (Streamlit)
- 🔐 Safe execution and rollback-ready design

---

## 🏗 Architecture

1. Failure detected from CI/CD
2. Gemini analyzes logs
3. Generates structured fix strategies
4. Rank fixes
5. Apply fix
6. Validate via tests
7. Store learning

---

## 🚀 Getting Started

### 1. Clone the repo

```bash
git clone https://github.com/yourusername/geminiguard-cicd.git
cd geminiguard-cicd
