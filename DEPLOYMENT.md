# Streamlit Cloud Deployment Guide

## Prerequisites
- GitHub account
- Streamlit Cloud account (sign up at https://streamlit.io/cloud)
- Gemini API key (from https://makersuite.google.com/app/apikey)

## Deployment Steps

### 1. Push Code to GitHub

```bash
git add .
git commit -m "Ready for Streamlit Cloud deployment"
git push origin main
```

### 2. Deploy to Streamlit Cloud

1. Go to https://share.streamlit.io
2. Click "New app"
3. Connect your GitHub account
4. Select your repository: `GeminiGuard-Autonomous-Self-Healing-CI-CD-Agent`
5. Main file path: `app.py` (root directory)
6. Click "Deploy"

### 3. Configure Secrets in Streamlit Cloud

In your Streamlit Cloud app settings, add these secrets:

**Required:**
- `GEMINI_API_KEY`: Your Gemini API key from Google AI Studio

**Optional (for GitHub integration):**
- `GITHUB_TOKEN`: Your GitHub personal access token
- `GITHUB_REPO`: Your repository in format `username/repo-name`
- `TEST_MODE`: Set to `true` for testing without API calls

### 4. Environment Variables (Alternative to Secrets)

You can also set environment variables in Streamlit Cloud:
- Go to your app settings
- Advanced → Environment variables
- Add the same variables as above

## Testing Before Deployment

Test locally first:
```bash
# With test mode (no API key needed)
# Set TEST_MODE=true in .env file
streamlit run app.py

# With real API
# Set your GEMINI_API_KEY in .env file
streamlit run app.py
```

## Troubleshooting

### App fails to start
- Check that `requirements.txt` includes all dependencies
- Ensure `app.py` is in the repository root
- Check Streamlit Cloud logs for specific errors

### API key errors
- Make sure `GEMINI_API_KEY` is set in Streamlit Cloud secrets
- Verify your API key is valid and active
- Check if you've exceeded API quotas

### Import errors
- Ensure all Python files are committed to Git
- Check that the directory structure is maintained
- Verify `requirements.txt` is complete

## File Structure for Deployment

```
GeminiGuard-Autonomous-Self-Healing-CI-CD-Agent/
├── app.py                    # Main entry point for Streamlit Cloud
├── requirements.txt          # Python dependencies
├── .gitignore               # Excludes .env and other files
├── agents/
│   └── analyzer.py
├── core/
│   ├── gemini_client.py
│   └── fix_ranker.py
├── dashboard/
│   └── app.py              # Original dashboard (still works locally)
├── integrations/
│   └── github_pr.py
├── memory/
│   └── store.py
└── tests/
    └── test_runner.py
```

## Post-Deployment

1. **Test the deployed app** using the URL provided by Streamlit Cloud
2. **Monitor usage** in Streamlit Cloud dashboard
3. **Set up custom domain** (optional) in app settings
4. **Configure authentication** (optional) for restricted access

## Cost Monitoring

- Streamlit Cloud: Free tier available (limitations apply)
- Gemini API: Free tier with generous limits, then pay-per-use
- Monitor your API usage in Google Cloud Console