from __future__ import annotations

from datetime import date
import pandas as pd

from .database import connect, init_db

STATE_COLUMNS = [
    "received",
    "disposed",
    "pending_0_60",
    "pending_61_180",
    "pending_181_365",
    "pending_over_365",
]

def _snapshot_row(snapshot_date: str):
    init_db()
    with connect() as conn:
        return conn.execute(
            "SELECT id, snapshot_date, reporting_period, source_url, retrieved_at, record_count, dataset_sha256 "
            "FROM snapshots WHERE snapshot_date=? ORDER BY id DESC LIMIT 1", (snapshot_date,)
        ).fetchone()

def _states(snapshot_id: int) -> pd.DataFrame:
    with connect() as conn:
        rows = conn.execute(
            "SELECT state_ut, received, disposed, pending_0_60, pending_61_180, pending_181_365, pending_over_365, pending_total "
            "FROM snapshot_states WHERE snapshot_id=? ORDER BY state_ut", (snapshot_id,)
        ).fetchall()
    return pd.DataFrame([dict(r) for r in rows])

def list_history() -> list[dict]:
    init_db()
    with connect() as conn:
        rows = conn.execute(
            "SELECT id, snapshot_date, reporting_period, source_url, retrieved_at, record_count, dataset_sha256 "
            "FROM snapshots ORDER BY snapshot_date ASC, id ASC"
        ).fetchall()
    return [dict(r) for r in rows]

def _delta(before: int | float, after: int | float) -> dict:
    change = after - before
    pct = round((change / before) * 100, 2) if before else None
    return {"before": before, "after": after, "change": change, "change_pct": pct}

def compare_snapshots(from_date: str, to_date: str) -> dict:
    try:
        from_day, to_day = date.fromisoformat(from_date), date.fromisoformat(to_date)
    except ValueError as exc:
        raise ValueError("Dates must use YYYY-MM-DD format.") from exc
    if from_day >= to_day:
        raise ValueError("from_date must be earlier than to_date.")
    before, after = _snapshot_row(from_date), _snapshot_row(to_date)
    if before is None or after is None:
        return {"status":"unavailable","reason":"Both dates must correspond to verified registered snapshots.","from_date":from_date,"to_date":to_date}

    left, right = _states(before["id"]).set_index("state_ut"), _states(after["id"]).set_index("state_ut")
    common = left.index.intersection(right.index)
    aggregate = {column:_delta(int(left.loc[common,column].sum()),int(right.loc[common,column].sum())) for column in STATE_COLUMNS}
    state_changes=[]
    for state in sorted(common):
        state_changes.append({"state_ut":state,**{column:_delta(int(left.at[state,column]),int(right.at[state,column])) for column in STATE_COLUMNS}})
    return {
        "status":"ok",
        "from":{k:before[k] for k in ("id","snapshot_date","reporting_period","source_url","record_count","dataset_sha256")},
        "to":{k:after[k] for k in ("id","snapshot_date","reporting_period","source_url","record_count","dataset_sha256")},
        "coverage":{"common_states_ut":len(common),"added_states_ut":sorted(set(right.index)-set(left.index)),"removed_states_ut":sorted(set(left.index)-set(right.index))},
        "aggregate":aggregate,
        "state_changes":state_changes,
        "note":"Changes are descriptive differences between two verified snapshots; they do not establish causes or performance rankings.",
    }

def state_history(state_ut: str) -> dict:
    snapshots=list_history()
    if len(snapshots)<2:
        return {"status":"unavailable","reason":"State history requires at least two verified snapshots.","snapshot_count":len(snapshots),"state_ut":state_ut}
    timeline=[]
    for snap in snapshots:
        df=_states(snap["id"])
        matches=df[df["state_ut"].str.casefold()==state_ut.strip().casefold()]
        if matches.empty:
            continue
        row=matches.iloc[0]
        timeline.append({"snapshot_date":snap["snapshot_date"],"reporting_period":snap["reporting_period"],"state_ut":row["state_ut"],**{column:int(row[column]) for column in STATE_COLUMNS}})
    if len(timeline)<2:
        return {"status":"unavailable","reason":"The requested State/UT is not present in at least two verified snapshots.","snapshot_count":len(snapshots),"state_ut":state_ut}
    return {"status":"ok","state_ut":timeline[0]["state_ut"],"timeline":timeline,"note":"Timeline values are direct records from verified snapshots; no interpolation is performed."}

def latest_comparison() -> dict:
    snapshots=list_history()
    if len(snapshots)<2:
        return {"status":"unavailable","reason":"Historical comparison requires at least two verified snapshots.","snapshot_count":len(snapshots)}
    return compare_snapshots(snapshots[-2]["snapshot_date"],snapshots[-1]["snapshot_date"])
