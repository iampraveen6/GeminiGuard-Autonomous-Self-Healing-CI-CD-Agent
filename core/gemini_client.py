import os
import requests
import json

BASE_URL = "https://generativelanguage.googleapis.com/v1beta"


# -------------------------
# ✅ Get API Key Dynamically
# -------------------------
def get_api_key():
    return os.getenv("GEMINI_API_KEY")


# -------------------------
# ✅ TEST MODE (Mock Response)
# -------------------------
def get_mock_response():
    return {
        "root_cause": "Missing Python dependency 'requests'",
        "fixes": [
            {
                "description": "Install missing dependency using pip install requests",
                "confidence": 0.9,
                "risk": "low"
            },
            {
                "description": "Verify virtual environment activation",
                "confidence": 0.7,
                "risk": "medium"
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
# ✅ Main Function
# -------------------------
def analyze_failure(logs: str):
    # ✅ TEST MODE → Skip API entirely
    if os.getenv("TEST_MODE") == "true":
        return get_mock_response()

    api_key = get_api_key()

    if not api_key:
        return {"error": "Missing GEMINI_API_KEY"}

    try:
        model_name = get_available_model(api_key)
        print(f"✅ Using model: {model_name}")

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

        if response.status_code != 200:
            return {"error": response.text}

        result = response.json()

        # ✅ Extract text safely
        text_output = result["candidates"][0]["content"]["parts"][0]["text"]

        # ✅ Try parsing JSON from response
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