from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from .analytics import load_data
from .gemini import ask_gemini
from .query_engine import answer_question, compact_context
router = APIRouter(prefix="/api/v1/ai", tags=["AI"])
class AskRequest(BaseModel):
    question: str = Field(min_length=3, max_length=500)
SUGGESTIONS = ["What is the pending workload in Tamil Nadu?","Which ageing bucket is largest?","Show states with high 181+ day workload.","Explain this dataset."]
@router.get("/suggestions")
def suggestions(): return {"suggestions": SUGGESTIONS}
@router.post("/ask")
def ask(request: AskRequest):
    question=request.question.strip(); df=load_data(); deterministic=answer_question(question)
    context=(f"Use this deterministic result as the factual answer. Explain naturally without adding facts or changing numbers. Mention snapshot/reporting period when useful.\nDETERMINISTIC RESULT: {deterministic['calculation']}\nMETADATA: snapshot={deterministic['snapshot_date']}; period={deterministic['reporting_period']}" if deterministic else f"Relevant CIVICLENS rows:\n{compact_context(question)}")
    try: answer=ask_gemini(question,context)
    except Exception as exc: raise HTTPException(status_code=502,detail=f"Gemini request failed: {type(exc).__name__}") from exc
    return {"question":question,"answer":answer,"intent":deterministic["intent"] if deterministic else "grounded_dataset_query","answer_data":deterministic["answer_data"] if deterministic else None,"calculation":deterministic["calculation"] if deterministic else None,"grounding":deterministic["grounding"] if deterministic else "gemini_dataset_context","snapshot_date":str(df["snapshot_date"].iloc[0]),"reporting_period":str(df["reporting_period"].iloc[0]),"source":str(df["source"].iloc[0])}
