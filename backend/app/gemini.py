import os
from typing import Optional

try:
    from google import genai
except ImportError:
    genai = None

def ask_gemini(question: str, context: str) -> str:
    api_key = os.getenv("GEMINI_API_KEY")
    model = os.getenv("GEMINI_MODEL", "gemini-2.5-flash")

    if not api_key:
        return "Gemini is not configured. Add GEMINI_API_KEY to the backend environment."
    if genai is None:
        return "Gemini SDK is not installed. Install the backend requirements first."

    prompt = f"""You are CIVICLENS Analytics Copilot.
Answer only from the supplied dataset context.
Do not invent facts, causes, dates or metrics.
Mention the snapshot/reporting period when relevant.
The pressure_index is a project-defined exploratory metric, not an official government metric.

DATA CONTEXT:
{context}

USER QUESTION:
{question}
"""
    client = genai.Client(api_key=api_key)
    response = client.models.generate_content(model=model, contents=prompt)
    return response.text or "No grounded response was returned."
