import pandas as pd
from .analytics import ageing, load_data, overview


def _meta(df: pd.DataFrame) -> dict:
    return {
        "snapshot_date": str(df["snapshot_date"].iloc[0]),
        "reporting_period": str(df["reporting_period"].iloc[0]),
        "source": str(df["source"].iloc[0]),
    }


def answer_question(question: str) -> dict | None:
    q = question.strip().lower()
    df = load_data()
    meta = _meta(df)

    state = None
    for name in sorted(df["state_ut"].astype(str).tolist(), key=len, reverse=True):
        if name.lower() in q:
            state = name
            break

    if state:
        row = df[df["state_ut"].eq(state)].iloc[0]
        fields = {
            "pending": ("pending_total", "pending workload", int),
            "received": ("received", "received grievances", int),
            "disposed": ("disposed", "disposed grievances", int),
            "disposal rate": ("disposal_rate", "disposal rate", float),
            "181": ("ageing_181_plus", "181+ day pending workload", int),
            "ageing": ("ageing_181_plus", "181+ day pending workload", int),
        }
        for token, (column, label, cast) in fields.items():
            if token in q:
                value = cast(row[column])
                display = f"{value:.2f}%" if column == "disposal_rate" else f"{value:,}"
                return {**meta, "intent": "state_metric", "answer_data": {"state_ut": state, "metric": label, "value": value}, "calculation": f"{state}: {label} = {display}.", "grounding": "deterministic_dataset"}

    a = ageing()
    if "ageing bucket" in q or ("largest" in q and "ageing" in q):
        label, value = max(a.items(), key=lambda x: x[1])
        labels = {"0_60": "0–60 days", "61_180": "61–180 days", "181_365": "181–365 days", "365_plus": "365+ days"}
        return {**meta, "intent": "largest_ageing_bucket", "answer_data": {"bucket": labels[label], "value": value}, "calculation": f"The largest current pending ageing bucket is {labels[label]} with {value:,} records.", "grounding": "deterministic_dataset"}

    if "total pending" in q or ("pending workload" in q and not state):
        o = overview()
        return {**meta, "intent": "total_pending", "answer_data": {"pending": o["pending"]}, "calculation": f"Total pending workload across {o['states_ut_count']} State/UT records is {o['pending']:,}.", "grounding": "deterministic_dataset"}

    if ("how many" in q or "number of" in q) and ("state" in q or "ut" in q):
        o = overview()
        return {**meta, "intent": "record_count", "answer_data": {"states_ut_count": o["states_ut_count"]}, "calculation": f"The snapshot contains {o['states_ut_count']} State/UT records.", "grounding": "deterministic_dataset"}

    if "explain this dataset" in q or q in {"dataset", "explain dataset"}:
        o = overview()
        return {**meta, "intent": "dataset_summary", "answer_data": o, "calculation": f"The snapshot records {o['received']:,} received, {o['disposed']:,} disposed and {o['pending']:,} pending grievances.", "grounding": "deterministic_dataset"}

    return None


def compact_context(question: str, max_rows: int = 12) -> str:
    df = load_data()
    q = question.lower()
    state = next((n for n in sorted(df["state_ut"].astype(str), key=len, reverse=True) if n.lower() in q), None)
    rows = df[df["state_ut"].eq(state)] if state else df.nlargest(max_rows, "pending_total")
    cols = ["state_ut", "received", "disposed", "pending_total", "disposal_rate", "ageing_181_plus"]
    return rows[cols].to_csv(index=False)
