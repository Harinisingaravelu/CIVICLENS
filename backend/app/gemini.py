import os
from pathlib import Path

import httpx
from dotenv import load_dotenv

BACKEND_DIR = Path(__file__).resolve().parents[1]
load_dotenv(BACKEND_DIR / ".env")

DEFAULT_MODEL = "gemini-3.8-flash"
FALLBACK_MODEL = "gemini-2.5-flash"
API_BASE = "https://generativelanguage.googleapis.com/v1beta"


def _safe_error(response: httpx.Response) -> str:
    try:
        payload = response.json()
        error = payload.get("error", {}) if isinstance(payload, dict) else {}
        status = error.get("status")
        message = error.get("message")
        if status and message:
            return f"{status}: {message}"
        if message:
            return str(message)
    except Exception:
        pass
    return f"HTTP {response.status_code}"


def _request_model(api_key: str, model: str, prompt: str) -> str:
    url = f"{API_BASE}/models/{model}:generateContent"
    payload = {
        "contents": [
            {
                "role": "user",
                "parts": [{"text": prompt}],
            }
        ]
    }

    try:
        response = httpx.post(
            url,
            headers={
                "x-goog-api-key": api_key,
                "Content-Type": "application/json",
            },
            json=payload,
            timeout=45.0,
        )
    except httpx.HTTPError as exc:
        raise RuntimeError("Gemini network request failed.") from exc

    if response.status_code >= 400:
        raise RuntimeError(f"Gemini API error: {_safe_error(response)}")

    try:
        data = response.json()
        candidates = data.get("candidates", [])
        text_parts = []
        for candidate in candidates:
            content = candidate.get("content", {})
            for part in content.get("parts", []):
                if part.get("text"):
                    text_parts.append(part["text"])
        answer = "\n".join(text_parts).strip()
    except Exception as exc:
        raise RuntimeError("Gemini returned an unreadable response.") from exc

    return answer or "No grounded response was returned."


def ask_gemini(question: str, context: str) -> str:
    api_key = (os.getenv("GEMINI_API_KEY") or "").strip()
    configured_model = (os.getenv("GEMINI_MODEL") or DEFAULT_MODEL).strip()

    if not api_key:
        return "Gemini is not configured. Add GEMINI_API_KEY to the service environment."

    prompt = f"""You are CIVICLENS Analytics Copilot.

Grounding rules:
- Answer only from the supplied CIVICLENS dataset context.
- Never invent facts, causes, dates, trends, rankings, or metrics.
- Mention the snapshot date/reporting period when relevant.
- Clearly distinguish dataset facts from calculations and interpretation.
- pressure_index is a project-defined exploratory metric, not an official government metric.
- Do not label a state or department as good/bad based on this snapshot.
- If the dataset cannot answer the question, say so.

DATA CONTEXT:
{context}

USER QUESTION:
{question}
"""

    models = [configured_model]
    if configured_model != FALLBACK_MODEL:
        models.append(FALLBACK_MODEL)

    errors = []
    for model in models:
        try:
            return _request_model(api_key, model, prompt)
        except RuntimeError as exc:
            errors.append(f"{model}: {exc}")

    raise RuntimeError("Gemini request failed. " + " | ".join(errors))
