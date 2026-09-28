import os
import sqlite3
from pathlib import Path
from dotenv import load_dotenv

BACKEND_DIR = Path(__file__).resolve().parents[1]
load_dotenv(BACKEND_DIR / ".env")
DEFAULT_DB = Path(__file__).resolve().parents[2] / "data" / "civiclens.db"

def database_path() -> str:
    url = os.getenv("DATABASE_URL", "").strip()
    if not url:
        DEFAULT_DB.parent.mkdir(parents=True, exist_ok=True)
        return str(DEFAULT_DB)
    if url.startswith("sqlite:///"):
        path = Path(url.removeprefix("sqlite:///"))
        if not path.is_absolute(): path = Path(__file__).resolve().parents[2] / path
        path.parent.mkdir(parents=True, exist_ok=True)
        return str(path)
    raise ValueError("Only SQLite DATABASE_URL values are supported locally.")

def connect() -> sqlite3.Connection:
    conn = sqlite3.connect(database_path())
    conn.row_factory = sqlite3.Row
    return conn

def init_db() -> None:
    with connect() as conn:
        conn.executescript("""
        CREATE TABLE IF NOT EXISTS snapshots (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            snapshot_date TEXT NOT NULL,
            reporting_period TEXT NOT NULL,
            source_url TEXT NOT NULL,
            retrieved_at TEXT NOT NULL,
            record_count INTEGER NOT NULL,
            dataset_sha256 TEXT NOT NULL UNIQUE,
            created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(snapshot_date, reporting_period, source_url)
        );
        CREATE TABLE IF NOT EXISTS snapshot_states (
            snapshot_id INTEGER NOT NULL REFERENCES snapshots(id) ON DELETE CASCADE,
            state_ut TEXT NOT NULL,
            received INTEGER NOT NULL,
            disposed INTEGER NOT NULL,
            pending_0_60 INTEGER NOT NULL,
            pending_61_180 INTEGER NOT NULL,
            pending_181_365 INTEGER NOT NULL,
            pending_over_365 INTEGER NOT NULL,
            pending_total INTEGER NOT NULL,
            PRIMARY KEY(snapshot_id, state_ut)
        );
        CREATE INDEX IF NOT EXISTS idx_snapshot_states_snapshot ON snapshot_states(snapshot_id);
        CREATE INDEX IF NOT EXISTS idx_snapshots_date ON snapshots(snapshot_date DESC);
        """)

def list_snapshots() -> list[dict]:
    init_db()
    with connect() as conn:
        rows = conn.execute("SELECT id,snapshot_date,reporting_period,source_url,retrieved_at,record_count,dataset_sha256,created_at FROM snapshots ORDER BY snapshot_date DESC, id DESC").fetchall()
        return [dict(r) for r in rows]
