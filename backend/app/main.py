from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pathlib import Path
import csv

app = FastAPI(title="CIVICLENS API", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

DATA_FILE = Path(__file__).resolve().parents[2] / "data" / "cpgrams_snapshot.csv"

def load_rows():
    if not DATA_FILE.exists():
        return []
    with DATA_FILE.open("r", encoding="utf-8-sig") as f:
        return list(csv.DictReader(f))

@app.get("/health")
def health():
    return {"status": "ok", "service": "civic-lens-api"}

@app.get("/api/v1/overview")
def overview():
    rows = load_rows()
    def n(k):
        return sum(float(r.get(k) or 0) for r in rows)
    received = n("received")
    disposed = n("disposed")
    pending = n("pending_total")
    return {
        "rows": len(rows),
        "received": received,
        "disposed": disposed,
        "pending": pending,
        "disposal_rate": round(disposed / received * 100, 2) if received else 0
    }

@app.get("/api/v1/states")
def states():
    return load_rows()
