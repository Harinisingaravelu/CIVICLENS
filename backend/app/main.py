import os
from contextlib import asynccontextmanager
from fastapi import FastAPI, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import Response
from .analytics import overview, state_table, ageing, insights
from .ai_routes import router as ai_router
from .export import csv_bytes
from .health import readiness
from .database import init_db, list_snapshots
from .snapshot import register_current_snapshot

@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db(); register_current_snapshot(); yield

app=FastAPI(title="CIVICLENS API",version="1.3.0",lifespan=lifespan)
origins=[x.strip() for x in os.getenv("CORS_ORIGINS","http://localhost:5500,http://127.0.0.1:5500").split(",") if x.strip()]
app.add_middleware(CORSMiddleware,allow_origins=origins,allow_methods=["GET","POST"],allow_headers=["Content-Type"])
app.include_router(ai_router)

@app.get("/health")
def health(): return {"status":"ok","service":"civic-lens-api","version":"1.3.0"}
@app.get("/ready")
def ready(): return readiness()
@app.get("/api/v1/overview")
def get_overview(): return overview()
@app.get("/api/v1/states")
def get_states(search: str|None=Query(default=None,max_length=100),limit:int=Query(default=100,ge=1,le=100)): return state_table(search=search,limit=limit)
@app.get("/api/v1/ageing")
def get_ageing(): return ageing()
@app.get("/api/v1/insights")
def get_insights(): return insights()
@app.get("/api/v1/snapshots")
def get_snapshots(): return list_snapshots()
@app.post("/api/v1/snapshots/register")
def register_snapshot(): return register_current_snapshot()
@app.get("/api/v1/export/csv")
def export_csv(): return Response(content=csv_bytes(),media_type="text/csv",headers={"Content-Disposition":"attachment; filename=civic-lens-validated.csv"})
