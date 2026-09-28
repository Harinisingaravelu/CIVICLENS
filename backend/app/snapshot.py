from datetime import datetime, timezone
import hashlib
from .analytics import load_data, validate_dataframe
from .database import connect, init_db

BASE_COLUMNS = ["state_ut","snapshot_date","reporting_period","received","disposed","pending_0_60","pending_61_180","pending_181_365","pending_over_365","pending_total","source"]

def register_dataframe(df) -> dict:
    df = validate_dataframe(df)
    init_db()
    csv_text = df[BASE_COLUMNS].to_csv(index=False)
    digest = hashlib.sha256(csv_text.encode("utf-8")).hexdigest()
    snapshot_date = str(df["snapshot_date"].iloc[0])
    reporting_period = str(df["reporting_period"].iloc[0])
    source_url = str(df["source"].iloc[0])
    retrieved_at = datetime.now(timezone.utc).isoformat()
    with connect() as conn:
        existing = conn.execute("SELECT id FROM snapshots WHERE dataset_sha256=?", (digest,)).fetchone()
        if existing:
            return {"status":"already_registered","snapshot_id":existing[0],"dataset_sha256":digest}
        duplicate = conn.execute(
            "SELECT id FROM snapshots WHERE snapshot_date=? AND reporting_period=? AND source_url=?",
            (snapshot_date, reporting_period, source_url),
        ).fetchone()
        if duplicate:
            return {"status":"already_registered","snapshot_id":duplicate[0],"reason":"same snapshot identity already exists"}
        try:
            cur = conn.execute(
                "INSERT INTO snapshots(snapshot_date,reporting_period,source_url,retrieved_at,record_count,dataset_sha256) VALUES(?,?,?,?,?,?)",
                (snapshot_date, reporting_period, source_url, retrieved_at, len(df), digest),
            )
        except Exception as exc:
            if "UNIQUE constraint failed" not in str(exc):
                raise
            existing = conn.execute("SELECT id FROM snapshots WHERE dataset_sha256=?", (digest,)).fetchone()
            if existing:
                return {"status":"already_registered","snapshot_id":existing[0],"dataset_sha256":digest}
            duplicate = conn.execute(
                "SELECT id FROM snapshots WHERE snapshot_date=? AND reporting_period=? AND source_url=?",
                (snapshot_date, reporting_period, source_url),
            ).fetchone()
            if duplicate:
                return {"status":"already_registered","snapshot_id":duplicate[0],"reason":"same snapshot identity already exists"}
            raise
        snapshot_id = cur.lastrowid
        state_cols = ["state_ut","received","disposed","pending_0_60","pending_61_180","pending_181_365","pending_over_365","pending_total"]
        conn.executemany(
            "INSERT INTO snapshot_states(snapshot_id,state_ut,received,disposed,pending_0_60,pending_61_180,pending_181_365,pending_over_365,pending_total) VALUES(?,?,?,?,?,?,?,?,?)",
            [(snapshot_id,*row) for row in df[state_cols].itertuples(index=False,name=None)],
        )
        return {"status":"registered","snapshot_id":snapshot_id,"dataset_sha256":digest,"record_count":len(df)}

def register_current_snapshot() -> dict:
    return register_dataframe(load_data().drop(columns=["disposal_rate","pending_share","ageing_181_plus","pressure_index"]))
