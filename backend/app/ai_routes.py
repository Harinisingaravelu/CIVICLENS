from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from .analytics import load_data
from .gemini import ask_gemini

router = APIRouter(prefix="/api/v1/ai", tags=["AI"])


class AskRequest(BaseModel):
    question: str = Field(min_length=3, max_length=500)


@router.post("/ask")
def ask(request: AskRequest):
    df = load_data()
    context = df[
        [
            "state_ut",
            "received",
            "disposed",
            "pending_total",
            "disposal_rate",
            "ageing_181_plus",
            "pressure_index",
        ]
    ].to_csv(index=False)

    try:
        answer = ask_gemini(request.question.strip(), context)
    except Exception as exc:
        raise HTTPException(
            status_code=502,
            detail=f"Gemini request failed: {type(exc).__name__}",
        ) from exc

    return {
        "question": request.question.strip(),
        "answer": answer,
        "snapshot_date": str(df["snapshot_date"].iloc[0]),
        "reporting_period": str(df["reporting_period"].iloc[0]),
    }
