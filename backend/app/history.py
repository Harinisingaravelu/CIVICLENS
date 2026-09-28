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
    "pending_total",
]


def _snapshot_row(snapshot_date: str):
    init_db()
    with connect() as conn:
        return conn.execute(
            "SELECT id, snapshot_date, reporting_period, source_url, retrieved_at, record_count, dataset_sha256 "
            "FROM snapshots WHERE snapshot_date=? ORDER BY id DESC LIMIT 1",
            (snapshot_date,),
        ).fetchone()


def _states(snapshot_id: int) -> pd.DataFrame:
    with connect() as conn:
        rows = conn.execute(
            "SELECT state_ut, received, disposed, pending_0_60, pending_61_180, "
            "pending_181_365, pending_over_365, pending_total "
            "FROM snapshot_states WHERE snapshot_id=? ORDER BY state_ut",
            (snapshot_id,),
        ).fetchall()
    return pd.DataFrame([dict(r) for r in rows])


def list_history() -> list[dict]:
    init_db()
    with connect() as conn:
        rows = conn.execute(
            "SELECT id, snapshot_date, reporting_period, source_url, retrieved_at, "
            "record_count, dataset_sha256 FROM snapshots ORDER BY snapshot_date ASC, id ASC"
        ).fetchall()
    return [dict(r) for r in rows]


def _delta(before: int | float, after: int | float) -> dict:
    change = after - before
    pct = round((change / before) * 100, 2) if before else None
    return {"before": before, "after": after, "change": change, "change_pct": pct}


def compare_snapshots(from_date: str, to_date: str) -> dict:
    try:
        from_day = date.fromisoformat(from_date)
        to_day = date.fromisoformat(to_date)
    except ValueError as exc:
        raise ValueError("Dates must use YYYY-MM-DD format.") from exc
    if from_day >= to_day:
        raise ValueError("from_date must be earlier than to_date.")

    before = _snapshot_row(from_date)
    after = _snapshot_row(to_date)
    if before is None or after is None:
        return {
            "status": "unavailable",
            "reason": "Both dates must correspond to verified registered snapshots.",
            "from_date": from_date,
            "to_date": to_date,
        }

    left = _states(before["id"]).set_index("state_ut")
    right = _states(after["id"]).set_index("state_ut")
    common = left.index.intersection(right.index)
    added = sorted(set(right.index) - set(left.index))
    removed = sorted(set(left.index) - set(right.index))

    aggregate = {}
    for column in STATE_COLUMNS:
        before_total = int(left.loc[common, column].sum())
        after_total = int(right.loc[common, column].sum())
        aggregate[column] = _delta(before_total, after_total)

    state_changes = []
    for state in sorted(common):
        row = {"state_ut": state}
        for column in STATE_COLUMNS:
            row[column] = _delta(int(left.at[state, column]), int(right.at[state, column]))
        state_changes.append(row)

    return {
        "status": "ok",
        "from": {k: before[k] for k in ("id", "snapshot_date", "reporting_period", "source_url", "record_count", "dataset_sha256")},
        "to": {k: after[k] for k in ("id", "snapshot_date", "reporting_period", "source_url", "record_count", "dataset_sha256")},
        "coverage": {
            "common_states_ut": len(common),
            "added_states_ut": added,
            "removed_states_ut": removed,
        },
        "aggregate": aggregate,
        "state_changes": state_changes,
        "note": "Changes are descriptive differences between two verified snapshots; they do not establish causes or performance rankings.",
    }


def latest_comparison() -> dict:
    snapshots = list_history()
    if len(snapshots) < 2:
        return {
            "status": "unavailable",
            "reason": "Historical comparison requires at least two verified snapshots.",
            "snapshot_count": len(snapshots),
        }
    return compare_snapshots(snapshots[-2]["snapshot_date"], snapshots[-1]["snapshot_date"])
