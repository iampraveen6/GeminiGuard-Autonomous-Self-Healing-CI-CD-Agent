# GeminiGuard: AI-Powered CI/CD Log Analyzer

```
 ██████╗ ███████╗███╗   ███╗██╗███╗   ██╗██╗ ██████╗ ██╗   ██╗ █████╗ ██████╗ ██████╗ 
██╔════╝ ██╔════╝████╗ ████║██║████╗  ██║██║██╔════╝ ██║   ██║██╔══██╗██╔══██╗██╔══██╗
██║  ███╗█████╗  ██╔████╔██║██║██╔██╗ ██║██║██║  ███╗██║   ██║███████║██████╔╝██║  ██║
██║   ██║██╔══╝  ██║╚██╔╝██║██║██║╚██╗██║██║██║   ██║██║   ██║██╔══██║██╔══██╗██║  ██║
╚██████╔╝███████╗██║ ╚═╝ ██║██║██║ ╚████║██║╚██████╔╝╚██████╔╝██║  ██║██║  ██║██████╔╝
 ╚═════╝ ╚══════╝╚═╝     ╚═╝╚═╝╚═╝  ╚═══╝╚═╝ ╚═════╝  ╚═════╝ ╚═╝  ╚═╝╚═╝  ╚═╝╚═════╝ 
```

🛡️ **Your CI/CD Pipeline's AI-Powered Analyzer**

[![Python](https://img.shields.io/badge/Python-3.9+-blue?style=flat-square)](https://www.python.org/)
[![Powered by Google Gemini](https://img.shields.io/badge/Powered%20by-Google%20Gemini-orange?style=flat-square)](https://ai.google.dev/)
[![Streamlit](https://img.shields.io/badge/Streamlit-App-red?style=flat-square)](https://streamlit.io/)
[![License](https://img.shields.io/badge/License-MIT-green?style=flat-square)](LICENSE)

**Analyzes CI/CD logs with AI, categorizes errors, and suggests fixes with automatic PR creation.**

| Project Snapshot | |
|---|---|
| **What it is** | An AI-powered CI/CD log analyzer that uses Google Gemini to diagnose failures and suggest fixes. |
| **Why it matters** | Reduces debugging time, provides intelligent error categorization, and automates fix PR creation. |
| **Tech stack** | Python, Google Gemini API, Streamlit, PyGithub |
| **Key outcomes** | AI-powered log analysis, error categorization, confidence-ranked fixes, GitHub PR automation |

## 📋 Table of Contents

- [Features](#features)
- [How It Works](#how-it-works)
- [Prerequisites](#prerequisites)
- [Quick Start](#quick-start)
- [Deployment](#deployment)
- [Configuration](#configuration)
- [Usage](#usage)
- [Features Deep Dive](#features-deep-dive)
- [Troubleshooting](#troubleshooting)
- [License](#license)

---

## Features

✅ **AI-Powered Log Analysis** - Uses Google Gemini API to analyze CI/CD logs and identify root causes

✅ **Error Categorization** - Automatically categorizes errors as:
- Application errors (code-related)
- Infrastructure errors (Kubernetes, Docker, network)
- External service errors (Artifactory, GitLab, databases)

✅ **Confidence-Ranked Fixes** - Suggests fixes with confidence scores and risk levels

✅ **Smart PR Creation** - Automatically creates GitHub PRs with:
- Feature/hotfix branch naming
- Detailed validation reports
- Implementation guidance

✅ **Rate Limiting** - Built-in quota management with automatic test mode fallback

✅ **Context-Aware Test Mode** - Mock responses that match error types for testing

✅ **Dynamic Mode Toggle** - Switch between test and production mode without changing secrets

✅ **Professional Dashboard** - Streamlit-based UI with real-time status and validation feedback

---

## How It Works

```
1. Paste CI/CD logs into the dashboard
   ↓
2. Toggle between Test Mode or Production Mode
   ↓
3. AI analyzes logs and categorizes the error type
   ↓
4. Root cause identified with confidence score
   ↓
5. Multiple fix strategies suggested and ranked
   ↓
6. Select a fix and choose branch type (feature/hotfix)
   ↓
7. System validates fix relevance
   ↓
8. If valid: Creates GitHub PR with documentation
   ↓
9. If infrastructure error: Blocks PR and provides DevOps guidance
```

---

## Prerequisites

Before you begin, ensure you have:

- **Python 3.9 or higher**
- **Google Gemini API Key** (free tier available at [ai.google.dev](https://ai.google.dev/))
- **GitHub Personal Access Token** (for PR creation)
- **Git** (for cloning)

### Get Your API Keys

1. **Google Gemini API**: Visit [ai.google.dev](https://ai.google.dev/), sign in with your Google account, and create an API key (free tier includes 20 requests/day)

2. **GitHub Token**: Go to Settings → Developer settings → Personal access tokens → Generate new token (classic) with `repo` scope

---

## Quick Start

### 1. Clone the Repository

```bash
git clone https://github.com/iampraveen6/GeminiGuard-Autonomous-Self-Healing-CI-CD-Agent.git
cd GeminiGuard-Autonomous-Self-Healing-CI-CD-Agent
```

### 2. Install Dependencies

```bash
pip install -r requirements.txt
```

### 3. Configure Environment Variables

Create a `.env` file:

```env
GEMINI_API_KEY=your_gemini_api_key_here
TEST_MODE=true
DEBUG_ENV=true
GITHUB_TOKEN=ghp_your_github_token_here
GITHUB_REPO=yourusername/your-repo-name
```

### 4. Run Locally

```bash
streamlit run app.py
```

The dashboard will open at `http://localhost:8501`

---

## Deployment

### Streamlit Cloud Deployment

1. **Push your code to GitHub**

2. **Go to [share.streamlit.io](https://share.streamlit.io)**

3. **Click "New app"** and connect your repository

4. **Configure the following secrets:**

```
GEMINI_API_KEY = your_gemini_api_key_here
TEST_MODE = true
DEBUG_ENV = true
GITHUB_TOKEN = ghp_your_github_token_here
GITHUB_REPO = yourusername/your-repo-name
```

5. **Click Deploy**

Your app will be live at `https://your-app-name.streamlit.app`

### Environment Variables

| Variable | Required | Description | Default |
|----------|----------|-------------|---------|
| `GEMINI_API_KEY` | Yes | Your Google Gemini API key | - |
| `TEST_MODE` | No | Use mock responses (true) or real API (false) | false |
| `DEBUG_ENV` | No | Enable debug panel | false |
| `GITHUB_TOKEN` | No | GitHub personal access token for PRs | - |
| `GITHUB_REPO` | No | Repository name (owner/repo) | - |

---

## Configuration

### Test Mode vs Production Mode

**Test Mode:**
- Uses context-aware mock responses
- No API quota consumption
- Perfect for testing and development
- Mock responses match error types (infrastructure, external, application)

**Production Mode:**
- Uses real Google Gemini API
- Consumes API quota (20 requests/day free tier)
- More accurate analysis
- Better root cause detection

**Dynamic Toggle:**
- Use the sidebar toggle to switch modes instantly
- No need to change secrets
- Session-aware setting

### Error Categorization

The system automatically categorizes errors:

**Infrastructure Errors:**
- Kubernetes pod issues
- Docker container problems
- Network/DNS issues
- CI/CD runner problems
- Result: PR creation blocked, DevOps guidance provided

**External Service Errors:**
- Artifactory/JFrog connectivity
- GitLab/GitHub issues
- Database connection problems
- Result: PR creation blocked, service coordination guidance

**Application Errors:**
- Missing dependencies
- Code syntax errors
- Import errors
- Configuration issues
- Result: PR creation enabled with code fixes

---

## Usage

### Basic Workflow

1. **Open the dashboard** at your deployed URL or `http://localhost:8501`

2. **Choose mode** in the sidebar:
   - Test Mode for testing (no quota)
   - Production Mode for real analysis (consumes quota)

3. **Paste CI/CD logs** into the text area

4. **Click "Analyze"** to get AI-powered analysis

5. **Review the results:**
   - Root cause identification
   - Error type categorization
   - Confidence-ranked fix suggestions

6. **Select a fix** from the dropdown

7. **Choose branch type:**
   - Feature for new functionality
   - Hotfix for urgent bug fixes

8. **Click "Apply Fix & Create PR"**
   - System validates fix relevance
   - Creates appropriate branch
   - Opens PR with documentation
   - Or blocks PR for infrastructure errors

### Understanding Validation

The system validates fixes before creating PRs:

**Validation Checks:**
- Technical action keywords (install, fix, update, etc.)
- File/configuration references (requirements.txt, config files, etc.)
- Content substance (description length)
- Log relevance (matching keywords)

**Confidence Scoring:**
- Technical keywords: 30%
- File references: 40%
- Content substance: 10-20%
- Log relevance: 10% (bonus)

**Threshold:** Only fixes with ≥50% confidence create PRs

### GitHub PR Creation

For application errors, PRs include:
- Proper branch naming (`feature/ai-fix-timestamp-description` or `hotfix/ai-fix-timestamp-description`)
- Detailed validation report
- Implementation guidance
- Related log context
- Professional PR description

---

## Features Deep Dive

### Rate Limiting & Quota Management

**Automatic Protection:**
- Tracks daily API usage
- Switches to test mode when 2 requests remain
- Shows quota status in debug panel
- Prevents quota exhaustion

**Quota Status Display:**
- Requests used today
- Remaining requests
- Usage percentage
- Reset time information

### Context-Aware Mock Responses

Instead of generic responses, test mode provides:
- Infrastructure-specific suggestions for Kubernetes/Docker issues
- External service guidance for Artifactory/GitLab problems
- Application code fixes for import/dependency errors

### Error Type Detection

**Infrastructure Indicators:**
- pod, kubernetes, k8s, container, docker
- pending, unready, namespace, executor, runner
- crashloop, oomkilled, deadline, quota

**External Service Indicators:**
- artifactory, jfrog, nexus, github, gitlab
- database, api gateway, service mesh

**Application Indicators:**
- code, function, class, import, file, variable

### Validation Reporting

**Detailed Feedback:**
- Per-check breakdown
- Pass/fail status for each check
- Confidence score calculation
- Actionable improvement suggestions

---

## Troubleshooting

### "Missing GitHub configuration"
- Ensure `GITHUB_TOKEN` and `GITHUB_REPO` are set in secrets
- Check token has `repo` scope
- Verify repository format: `owner/repo-name`

### "API Quota Exceeded"
- Switch to Test Mode to continue without API
- Wait for daily quota reset (midnight UTC)
- Consider upgrading to paid Gemini plan

### "PR Creation Disabled"
- Check if error is infrastructure-related
- Infrastructure errors correctly block PR creation
- Only application errors create PRs

### "Validation failed"
- Review the detailed validation report
- Fix suggestions need technical keywords
- Add file references to improve confidence
- Ensure description is substantial (>20 characters)

### TOML Format Errors
- Don't use quotes around boolean values
- Use quotes around string values with special characters
- Ensure proper TOML syntax in Streamlit Cloud secrets

---

## License

This project is licensed under the MIT License - see the LICENSE file for details.

---

## Acknowledgments

- **Google Gemini API** for AI-powered analysis
- **Streamlit** for the beautiful dashboard
- **PyGithub** for GitHub API integration
- **Open Source Community** for inspiration and tools

---

**Built with ❤️ by [Praveen Kittur](https://github.com/iampraveen6)**