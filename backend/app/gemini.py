import os
from pathlib import Path

from dotenv import load_dotenv

try:
    from google import genai
except ImportError:
    genai = None

BACKEND_DIR = Path(__file__).resolve().parents[1]
load_dotenv(BACKEND_DIR / ".env")


def ask_gemini(question: str, context: str) -> str:
    api_key = os.getenv("GEMINI_API_KEY")
    model = os.getenv("GEMINI_MODEL", "gemini-2.5-flash")

    if not api_key:
        return "Gemini is not configured. Add GEMINI_API_KEY to backend/.env."
    if genai is None:
        return "Gemini SDK is not installed. Install the backend requirements first."

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

    client = genai.Client(api_key=api_key)
    response = client.models.generate_content(model=model, contents=prompt)
    return response.text or "No grounded response was returned."
