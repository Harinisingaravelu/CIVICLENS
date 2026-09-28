from fastapi import FastAPI, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import Response
from .analytics import overview, state_table, ageing, insights
from .ai_routes import router as ai_router
from .export import csv_bytes
from .health import readiness

app=FastAPI(title="CIVICLENS API",version="1.2.0")
app.add_middleware(CORSMiddleware,allow_origins=["*"],allow_methods=["GET","POST"],allow_headers=["Content-Type"])
app.include_router(ai_router)

@app.get("/health")
def health(): return {"status":"ok","service":"civic-lens-api","version":"1.2.0"}

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

@app.get("/api/v1/export/csv")
def export_csv():
    return Response(content=csv_bytes(),media_type="text/csv",headers={"Content-Disposition":"attachment; filename=civic-lens-validated.csv"})
