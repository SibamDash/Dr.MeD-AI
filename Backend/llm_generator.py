import os
import re
import json
import google.generativeai as genai
from dotenv import load_dotenv

load_dotenv()

# ── API KEY ───────────────────────────────────────────────────────────────────
# Priority: .env file GEMINI_API_KEY  →  hardcoded below
HARDCODED_API_KEY = "AIzaSyB8Vv8LXR9g-W4x0SdX9UpkSFroZL9NT2I"
# ─────────────────────────────────────────────────────────────────────────────


# ── EXPECTED JSON KEYS ────────────────────────────────────────────────────────
# This is the exact shape the frontend (buildSummaryHTML) reads.
# If Gemini returns partial JSON we fill missing keys with safe defaults.
REQUIRED_KEYS = {
    "patient_summary":         "Not available",
    "test_report_summary":     "Not available",
    "clinical_interpretation": "Not available",
    "known_information":       [],
    "unclear_information":     [],
    "recommendations":         []
}
# ─────────────────────────────────────────────────────────────────────────────


def _extract_json_from_text(raw):
    """
    Robustly extract a JSON object from a string that may contain:
      - Markdown code fences  ```json … ```
      - Extra text before/after the JSON object
      - Trailing commas  (very common Gemini mistake)
    Returns a dict or None if all attempts fail.
    """
    if not raw:
        return None

    # 1. Strip markdown fences
    text = re.sub(r"```(?:json)?", "", raw).strip()

    # 2. Find the outermost { … } block
    start = text.find("{")
    end   = text.rfind("}")
    if start == -1 or end == -1 or end <= start:
        print("ERROR: no { } block found in Gemini response")
        return None

    json_str = text[start:end + 1]

    # 3. Try direct parse first
    try:
        return json.loads(json_str)
    except json.JSONDecodeError as e:
        print(f"Direct JSON parse failed ({e}). Trying repair...")

    # 4. Repair trailing commas before } or ]  (most common Gemini error)
    repaired = re.sub(r",\s*([}\]])", r"\1", json_str)
    try:
        return json.loads(repaired)
    except json.JSONDecodeError as e:
        print(f"Repaired JSON parse also failed ({e}).")
        print("--- Raw Gemini output (first 1500 chars) ---")
        print(raw[:1500])
        print("--------------------------------------------")
        return None


def _fill_defaults(data):
    """Fill any missing required keys so the frontend never crashes."""
    for key, default in REQUIRED_KEYS.items():
        if key not in data or data[key] is None:
            data[key] = default
        # Make sure list fields are actually lists
        if isinstance(default, list) and not isinstance(data[key], list):
            data[key] = [str(data[key])] if data[key] else []
    return data


def analyze_with_llm(text, patient_context, structured_data, file_paths=None):
    """
    Analyze medical report text using Google Gemini.
    Returns a fully validated dict matching the frontend JSON shape,
    or None to trigger the backend demo fallback.
    """
    api_key = (os.getenv("GEMINI_API_KEY") or HARDCODED_API_KEY or "").strip()

    if not api_key or api_key == "AIzaSyDemoKeyReplaceWithYours":
        print("No valid GEMINI_API_KEY — using backend demo fallback.")
        return None

    try:
        genai.configure(api_key=api_key)

        # ── Discover available models ─────────────────────────────────────────
        available_models = []
        try:
            print("Checking available Gemini models...")
            for m in genai.list_models():
                if "generateContent" in m.supported_generation_methods:
                    available_models.append(m.name)
            print(f"Found models: {', '.join(available_models) or 'none'}")
        except Exception as e:
            print(f"list_models() failed: {e}")

        # ── Prompt ────────────────────────────────────────────────────────────
        prompt = f"""
You are Dr.MeD-AI, an expert medical AI assistant.
Analyze the following medical document (lab report or prescription).
Return ONLY valid JSON — no explanation, no markdown fences, no extra text before or after.

PATIENT CONTEXT:
- Age: {patient_context.get('age', 'Unknown')}
- Condition: {patient_context.get('condition', 'None')}
- Literacy Level: {patient_context.get('literacyLevel', 'Medium')}

DOCUMENT TEXT:
{text[:8000]}

STRUCTURED LAB VALUES (pre-extracted):
{json.dumps(structured_data, indent=2)}

Return ONLY this JSON (all fields required, no fields skipped):
{{
    "patient_summary": "Patient name, age, gender extracted from the document.",
    "test_report_summary": "Summary of all test findings or prescription medications.",
    "clinical_interpretation": "Detailed clinical interpretation grounded in medical guidelines.",
    "known_information": ["Confirmed fact 1", "Confirmed fact 2"],
    "unclear_information": ["Missing detail 1", "Missing detail 2"],
    "recommendations": [
        {{
            "title": "Short actionable title",
            "description": "Specific advice for this patient.",
            "icon": "emoji",
            "priority": "high or medium or low"
        }}
    ]
}}
"""

        # ── Optional: attach images ────────────────────────────────────────────
        contents = [prompt]
        if file_paths:
            for path in file_paths:
                if path.lower().endswith(('.png', '.jpg', '.jpeg', '.webp', '.heic', '.heif')):
                    try:
                        import PIL.Image
                        contents.append(PIL.Image.open(path))
                        print(f"Added image: {os.path.basename(path)}")
                    except ImportError:
                        print("PIL not installed — image skipped.")
                    except Exception as e:
                        print(f"Could not load image {path}: {e}")

        # ── Select models ──────────────────────────────────────────────────────
        models_to_try = []
        if available_models:
            models_to_try += [m for m in available_models if "flash" in m.lower()]
            models_to_try += [m for m in available_models if "pro" in m.lower() and m not in models_to_try]
            models_to_try += [m for m in available_models if m not in models_to_try]
        if not models_to_try:
            models_to_try = [
                "models/gemini-1.5-flash",
                "models/gemini-2.0-flash",
                "models/gemini-1.5-pro",
                "models/gemini-pro",
            ]

        # ── Call Gemini ────────────────────────────────────────────────────────
        raw_text = None
        for m_name in models_to_try:
            try:
                print(f"Trying model: {m_name}...")
                model    = genai.GenerativeModel(m_name)
                response = model.generate_content(contents)
                if response and response.text:
                    raw_text = response.text
                    print(f"Got response from: {m_name}")
                    break
            except Exception as e:
                print(f"{m_name} failed: {e}")

        if not raw_text:
            print("All Gemini models failed.")
            return None

        # ── Always print raw response to terminal ──────────────────────────────
        print("\n" + "=" * 60)
        print("RAW GEMINI RESPONSE:")
        print("=" * 60)
        print(raw_text[:3000])
        print("=" * 60 + "\n")

        # ── Parse JSON ─────────────────────────────────────────────────────────
        result = _extract_json_from_text(raw_text)
        if result is None:
            print("JSON parsing failed — using demo fallback.")
            return None

        result = _fill_defaults(result)
        print("LLM result parsed OK. Keys:", list(result.keys()))
        return result

    except Exception as e:
        print(f"LLM crashed: {e}")
        import traceback
        traceback.print_exc()
        return None