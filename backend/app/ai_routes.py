from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field, field_validator
from .analytics import load_data
from .gemini import ask_gemini
from .query_engine import answer_question, compact_context
from .historical_ai import historical_result

router = APIRouter(prefix="/api/v1/ai", tags=["AI"])

class AskRequest(BaseModel):
    question: str = Field(min_length=3, max_length=500)

    @field_validator("question")
    @classmethod
    def question_must_contain_text(cls, value: str) -> str:
        value = value.strip()
        if len(value) < 3:
            raise ValueError("Question must contain at least 3 non-whitespace characters.")
        return value

SUGGESTIONS = [
    "What is the pending workload in Tamil Nadu?",
    "Which ageing bucket is largest?",
    "Show states with high 181+ day workload.",
    "Explain this dataset.",
    "What changed since the previous verified snapshot?",
]

@router.get("/suggestions")
def suggestions():
    return {"suggestions": SUGGESTIONS}

@router.post("/ask")
def ask(request: AskRequest):
    question = request.question.strip()
    df = load_data()

    historical = historical_result(question)
    deterministic = answer_question(question)

    if historical is not None:
        result = historical["result"]
        context = (
            "Use the following verified CIVICLENS historical result as the factual basis. "
            "Do not invent a trend, cause, ranking, or missing snapshot. "
            f"HISTORICAL RESULT: {result}\n"
        )
        intent = historical["intent"]
        answer_data = result
        calculation = None
        grounding = "verified_snapshot_history"
    else:
        context = (
            f"Use this deterministic result as the factual answer. Explain naturally without "
            f"adding facts or changing numbers. Mention snapshot/reporting period when useful.\n"
            f"DETERMINISTIC RESULT: {deterministic['calculation']}\n"
            f"METADATA: snapshot={deterministic['snapshot_date']}; period={deterministic['reporting_period']}"
            if deterministic
            else f"Relevant CIVICLENS rows:\n{compact_context(question)}"
        )
        intent = deterministic["intent"] if deterministic else "grounded_dataset_query"
        answer_data = deterministic["answer_data"] if deterministic else None
        calculation = deterministic["calculation"] if deterministic else None
        grounding = deterministic["grounding"] if deterministic else "gemini_dataset_context"

    try:
        answer = ask_gemini(question, context)
    except Exception:
        # Keep the analytics product usable even if the optional Gemini service
        # is unavailable, rate-limited, or temporarily rejects the configured key.
        # Deterministic answers remain fully grounded in the verified dataset.
        if deterministic:
            answer = deterministic["calculation"]
            grounding = "deterministic_dataset_fallback"
        elif historical is not None:
            answer = (
                "Gemini is temporarily unavailable. The verified historical result "
                "is shown below without adding unsupported interpretation."
            )
            grounding = "verified_snapshot_history_fallback"
        else:
            answer = (
                "Gemini is temporarily unavailable. Please retry shortly. "
                "The dashboard's deterministic analytics remain available."
            )
            grounding = "dataset_context_fallback"

    return {
        "question": question,
        "answer": answer,
        "intent": intent,
        "answer_data": answer_data,
        "calculation": calculation,
        "grounding": grounding,
        "snapshot_date": str(df["snapshot_date"].iloc[0]),
        "reporting_period": str(df["reporting_period"].iloc[0]),
        "source": str(df["source"].iloc[0]),
    }
