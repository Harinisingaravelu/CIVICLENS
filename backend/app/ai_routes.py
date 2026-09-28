from fastapi import APIRouter
from pydantic import BaseModel
from .analytics import load_data
from .gemini import ask_gemini

router = APIRouter(prefix="/api/v1/ai", tags=["AI"])

class AskRequest(BaseModel):
    question: str

@router.post("/ask")
def ask(request: AskRequest):
    df = load_data()
    context = df[[
        "state_ut","received","disposed","pending_total",
        "disposal_rate","ageing_181_plus","pressure_index"
    ]].to_csv(index=False)
    answer = ask_gemini(request.question, context)
    return {
        "question": request.question,
        "answer": answer,
        "snapshot_date": str(df["snapshot_date"].iloc[0]),
        "reporting_period": str(df["reporting_period"].iloc[0])
    }
