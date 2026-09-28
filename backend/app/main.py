import os
from contextlib import asynccontextmanager
from fastapi import FastAPI, File, HTTPException, Query, Request, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import Response
from .analytics import overview, state_table, ageing, insights
from .ai_routes import router as ai_router
from .export import csv_bytes
from .health import readiness
from .database import init_db, list_snapshots
from .snapshot import register_current_snapshot
from .ingestion import ingest_csv_bytes
from .history import list_history, compare_snapshots, latest_comparison, state_history
from .monitoring import record_request, metrics, timer

@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    register_current_snapshot()
    yield

app=FastAPI(title="CIVICLENS API",version="1.5.0",lifespan=lifespan)
origins=[x.strip() for x in os.getenv("CORS_ORIGINS","http://localhost:5500,http://127.0.0.1:5500").split(",") if x.strip()]
app.add_middleware(CORSMiddleware,allow_origins=origins,allow_methods=["GET","POST"],allow_headers=["Content-Type"])

@app.middleware("http")
async def observe_requests(request: Request, call_next):
    started=timer()
    response=await call_next(request)
    record_request(request.url.path,request.method,response.status_code,(timer()-started)*1000)
    return response

app.include_router(ai_router)

@app.get("/health")
def health(): return {"status":"ok","service":"civic-lens-api","version":"1.5.0"}

@app.get("/ready")
def ready(): return readiness()

@app.get("/metrics")
def get_metrics(): return metrics()

@app.get("/api/v1/overview")
def get_overview(): return overview()

@app.get("/api/v1/states")
def get_states(search: str|None=Query(default=None,max_length=100),limit:int=Query(default=100,ge=1,le=100)):
    return state_table(search=search,limit=limit)

@app.get("/api/v1/ageing")
def get_ageing(): return ageing()

@app.get("/api/v1/insights")
def get_insights(): return insights()

@app.get("/api/v1/snapshots")
def get_snapshots(): return list_snapshots()

@app.post("/api/v1/snapshots/register")
def register_snapshot(): return register_current_snapshot()

@app.get("/api/v1/history")
def get_history():
    return {"status":"ok","snapshots":list_history(),"latest_comparison":latest_comparison()}

@app.get("/api/v1/history/compare")
def get_history_compare(from_date:str=Query(...,pattern=r"^\d{4}-\d{2}-\d{2}$"),to_date:str=Query(...,pattern=r"^\d{4}-\d{2}-\d{2}$")):
    try:
        return compare_snapshots(from_date,to_date)
    except ValueError as exc:
        raise HTTPException(status_code=400,detail=str(exc)) from exc

@app.get("/api/v1/history/state/{state_ut}")
def get_state_history(state_ut:str=Query(...,min_length=1,max_length=100)):
    return state_history(state_ut)

@app.post("/api/v1/snapshots/ingest")
async def ingest_snapshot(file: UploadFile=File(...)):
    if os.getenv("ENABLE_SNAPSHOT_INGESTION","false").lower()!="true":
        raise HTTPException(status_code=403,detail="Snapshot ingestion is disabled. Set ENABLE_SNAPSHOT_INGESTION=true for a controlled local/admin workflow.")
    if file.content_type not in {None,"text/csv","application/csv","application/vnd.ms-excel"} and not (file.filename or "").lower().endswith(".csv"):
        raise HTTPException(status_code=415,detail="Only CSV snapshot files are accepted.")
    try:
        content=await file.read()
        return ingest_csv_bytes(content)
    except ValueError as exc:
        raise HTTPException(status_code=400,detail=str(exc)) from exc

@app.get("/api/v1/export/csv")
def export_csv():
    return Response(content=csv_bytes(),media_type="text/csv",headers={"Content-Disposition":"attachment; filename=civic-lens-validated.csv"})
