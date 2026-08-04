import os
import requests
import json
import time
from datetime import datetime, timedelta

BASE_URL = "https://generativelanguage.googleapis.com/v1beta"

# -------------------------
# Rate Limiting Configuration
# -------------------------
FREE_TIER_DAILY_LIMIT = 20  # Free tier limit
RATE_LIMIT_BUFFER = 2  # Keep buffer before hitting limit
usage_tracker = {
    "requests_today": 0,
    "reset_time": datetime.now().replace(hour=0, minute=0, second=0, microsecond=0) + timedelta(days=1)
}


def check_rate_limit():
    """
    Check if we're approaching the rate limit
    Returns: (can_proceed, message, remaining_requests)
    """
    global usage_tracker
    
    # Reset counter if new day
    now = datetime.now()
    if now >= usage_tracker["reset_time"]:
        usage_tracker["requests_today"] = 0
        usage_tracker["reset_time"] = now.replace(hour=0, minute=0, second=0, microsecond=0) + timedelta(days=1)
    
    remaining = FREE_TIER_DAILY_LIMIT - usage_tracker["requests_today"]
    
    # Auto-switch to test mode if approaching limit
    if remaining <= RATE_LIMIT_BUFFER:
        os.environ["TEST_MODE"] = "true"  # Temporarily enable test mode
        return False, f"Rate limit approaching ({remaining} requests remaining). Auto-switched to test mode.", remaining
    
    return True, f"{remaining} requests remaining today", remaining


def record_api_call():
    """Record an API call for rate limiting"""
    global usage_tracker
    usage_tracker["requests_today"] += 1


def handle_quota_error(logs=None):
    """Handle quota exceeded error by switching to test mode"""
    os.environ["TEST_MODE"] = "true"
    mock_response = get_mock_response(logs)
    
    return {
        "error": "QUOTA_EXCEEDED",
        "message": "Daily API quota exceeded. Automatically switched to test mode.",
        "usage_info": f"Used {usage_tracker['requests_today']}/{FREE_TIER_DAILY_LIMIT} requests",
        "retry_after": "Daily quota resets at midnight UTC",
        "mock_data": mock_response
    }


# -------------------------
# Get API Key Dynamically
# -------------------------
def get_api_key():
    return os.getenv("GEMINI_API_KEY")


# -------------------------
# ✅ TEST MODE (Mock Response)
# -------------------------
def get_mock_response(logs=None):
    """
    Generate context-aware mock response based on log content
    """
    logs_lower = logs.lower() if logs else ""
    
    # Infrastructure-related mock responses
    if any(kw in logs_lower for kw in ['pod', 'kubernetes', 'container', 'pending', 'unready', 'k8s', 'docker']):
        return {
            "root_cause": "Kubernetes infrastructure issue - pod stuck in Pending state with unready containers",
            "fixes": [
                {
                    "description": "Check Kubernetes cluster health and node availability",
                    "confidence": 0.95,
                    "risk": "low"
                },
                {
                    "description": "Verify container image availability and pull policies",
                    "confidence": 0.9,
                    "risk": "medium"
                },
                {
                    "description": "Review resource quotas and limits for the namespace",
                    "confidence": 0.85,
                    "risk": "low"
                },
                {
                    "description": "Check network policies and DNS configuration",
                    "confidence": 0.8,
                    "risk": "medium"
                }
            ]
        }
    
    # External service-related mock responses
    elif any(kw in logs_lower for kw in ['artifactory', 'jfrog', 'nexus', 'gitlab', 'github', 'database', 'api gateway']):
        return {
            "root_cause": "External service connectivity or availability issue",
            "fixes": [
                {
                    "description": "Verify external service status and availability",
                    "confidence": 0.9,
                    "risk": "low"
                },
                {
                    "description": "Check network connectivity and firewall rules",
                    "confidence": 0.85,
                    "risk": "medium"
                },
                {
                    "description": "Review service authentication and credentials",
                    "confidence": 0.8,
                    "risk": "low"
                }
            ]
        }
    
    # Default generic mock response
    else:
        return {
            "root_cause": "CI/CD pipeline failure - review logs for specific error details",
            "fixes": [
                {
                    "description": "Review pipeline logs for specific error messages and stack traces",
                    "confidence": 0.7,
                    "risk": "low"
                },
                {
                    "description": "Check recent changes in configuration files and dependencies",
                    "confidence": 0.6,
                    "risk": "medium"
                },
                {
                    "description": "Verify environment variables and secrets configuration",
                    "confidence": 0.8,
                    "risk": "low"
                }
            ]
        }


# -------------------------
# ✅ Get Available Model
# -------------------------
def get_available_model(api_key):
    url = f"{BASE_URL}/models?key={api_key}"

    res = requests.get(url)

    if res.status_code != 200:
        raise Exception(f"Failed to list models: {res.text}")

    models = res.json().get("models", [])

    for m in models:
        if "generateContent" in m.get("supportedGenerationMethods", []):
            return m["name"]

    raise Exception("No usable model found")


# -------------------------
# Main Function
# -------------------------
def analyze_failure(logs: str, test_mode=None):
    """
    Analyze CI/CD failure logs
    
    Args:
        logs: The CI/CD log text
        test_mode: Override TEST_MODE setting (None = use environment variable)
    """
    # Use parameter if provided, otherwise check environment variable
    if test_mode is None:
        test_mode = os.getenv("TEST_MODE", "false").lower() == "true"
    
    # TEST MODE → Skip API entirely
    if test_mode:
        return get_mock_response(logs)

    api_key = get_api_key()

    if not api_key:
        return {"error": "Missing GEMINI_API_KEY"}

    # Check rate limit before making API call
    can_proceed, limit_message, remaining = check_rate_limit()
    if not can_proceed:
        mock_response = get_mock_response(logs)
        return {
            "error": "RATE_LIMIT_APPROACHED",
            "message": limit_message,
            "remaining_requests": remaining,
            "auto_test_mode": True,
            "mock_data": mock_response  # Return actual mock data
        }

    try:
        model_name = get_available_model(api_key)
        
        url = f"{BASE_URL}/{model_name}:generateContent?key={api_key}"

        prompt = f"""
        Analyze CI/CD logs and return ONLY JSON:

        {{
          "root_cause": "...",
          "fixes": [
            {{
              "description": "...",
              "confidence": 0.0,
              "risk": "low/medium/high"
            }}
          ]
        }}

        Logs:
        {logs}
        """

        payload = {
            "contents": [
                {
                    "parts": [
                        {"text": prompt}
                    ]
                }
            ]
        }

        headers = {"Content-Type": "application/json"}

        response = requests.post(url, headers=headers, json=payload)

        # Record successful API call
        if response.status_code == 200:
            record_api_call()

        # Handle quota exceeded error
        if response.status_code == 429:
            return handle_quota_error(logs)

        if response.status_code != 200:
            return {"error": response.text}

        result = response.json()

        # Extract text safely
        text_output = result["candidates"][0]["content"]["parts"][0]["text"]

        # Try parsing JSON from response
        try:
            json_start = text_output.find("{")
            json_end = text_output.rfind("}") + 1

            parsed = json.loads(text_output[json_start:json_end])
            return parsed

        except Exception:
            # fallback: wrap raw text as fix
            return {
                "root_cause": "Unknown",
                "fixes": [
                    {
                        "description": text_output,
                        "confidence": 0.6,
                        "risk": "medium"
                    }
                ]
            }

    except Exception as e:
        return {"error": str(e)}