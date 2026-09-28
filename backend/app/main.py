from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .analytics import overview, state_table, ageing
from .ai_routes import router as ai_router

app = FastAPI(title="CIVICLENS API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(ai_router)

@app.get("/health")
def health():
    return {"status": "ok", "service": "civic-lens-api", "version": "1.0.0"}

@app.get("/api/v1/overview")
def get_overview():
    return overview()

@app.get("/api/v1/states")
def get_states():
    return state_table()

@app.get("/api/v1/ageing")
def get_ageing():
    return ageing()
