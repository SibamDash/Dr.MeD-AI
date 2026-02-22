import requests
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")

# Strong medical guardrails
SYSTEM_PROMPT = """
You are a medication guidance assistant for a medical report platform.

Your role:
- Explain medicine composition.
- Explain why it is prescribed.
- Explain benefits.
- Mention common side effects.
- Mention serious side effects briefly.
- Mention precautions.
- Encourage consulting a doctor.

Strict rules:
- Do NOT diagnose diseases.
- Do NOT change dosage.
- Do NOT recommend alternative medicines.
- If question is unrelated to medicine, politely refuse.

Tone:
- Clear
- Calm
- Patient-friendly
- Non-technical language
"""

def ask_chatbot(user_message, context=""):
    try:
        if not OPENROUTER_API_KEY:
            return "API key is not configured properly."

        headers = {
            "Authorization": f"Bearer {OPENROUTER_API_KEY}",
            "Content-Type": "application/json",
            "HTTP-Referer": "http://localhost:5001",
            "X-Title": "Dr.MeD Chatbot"
        }

        payload = {
            "model": "mistralai/mistral-7b-instruct",
            "messages": [
                {
                    "role": "system",
                    "content": SYSTEM_PROMPT
                },
                {
                    "role": "user",
                    "content": f"Medicine context: {context}\n\nUser question: {user_message}"
                }
            ],
            "temperature": 0.4
        }

        response = requests.post(
            "https://openrouter.ai/api/v1/chat/completions",
            headers=headers,
            json=payload,
            timeout=20
        )

        if response.status_code != 200:
            print("OpenRouter error:", response.text)
            return "Sorry, I am unable to respond right now."

        data = response.json()

        return data["choices"][0]["message"]["content"].strip()

    except Exception as e:
        print("Chatbot error:", e)
        return "Sorry, I am unable to respond right now."