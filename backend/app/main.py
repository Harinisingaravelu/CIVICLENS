from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pathlib import Path
import csv

app = FastAPI(title="CIVICLENS API", version="0.2.0")

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

def num(rows, key):
    return sum(float(r.get(key) or 0) for r in rows)

@app.get("/health")
def health():
    return {"status": "ok", "service": "civic-lens-api", "version": "0.2.0"}

@app.get("/api/v1/overview")
def overview():
    rows = load_rows()
    received = num(rows, "received")
    disposed = num(rows, "disposed")
    pending = num(rows, "pending_total")
    return {
        "rows": len(rows),
        "received": int(received),
        "disposed": int(disposed),
        "pending": int(pending),
        "disposal_rate": round(disposed / received * 100, 2) if received else 0,
    }

@app.get("/api/v1/states")
def states():
    rows = load_rows()
    for r in rows:
        for key in ("received","disposed","pending_total","pending_0_60","pending_61_180","pending_181_365","pending_over_365"):
            r[key] = float(r.get(key) or 0)
        r["disposal_rate"] = round(r["disposed"] / r["received"] * 100, 2) if r["received"] else 0
        r["ageing_181_plus"] = r["pending_181_365"] + r["pending_over_365"]
    return sorted(rows, key=lambda x: x["pending_total"], reverse=True)
