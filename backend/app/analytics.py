from pathlib import Path
import pandas as pd

DATA_FILE = Path(__file__).resolve().parents[2] / "data" / "cpgrams_snapshot.csv"
REQUIRED_COLUMNS = ["state_ut", "snapshot_date", "reporting_period", "received", "disposed", "pending_0_60", "pending_61_180", "pending_181_365", "pending_over_365", "pending_total", "source"]
NUMERIC_COLUMNS = REQUIRED_COLUMNS[3:10]

def load_data() -> pd.DataFrame:
    df = pd.read_csv(DATA_FILE)
    missing = [c for c in REQUIRED_COLUMNS if c not in df.columns]
    if missing: raise ValueError(f"Dataset is missing required columns: {', '.join(missing)}")
    for col in NUMERIC_COLUMNS: df[col] = pd.to_numeric(df[col], errors="coerce")
    if df[NUMERIC_COLUMNS].isna().any().any(): raise ValueError("Dataset contains missing/non-numeric values.")
    if (df[NUMERIC_COLUMNS] < 0).any().any(): raise ValueError("Dataset contains negative numeric values.")
    ageing_sum = df[["pending_0_60","pending_61_180","pending_181_365","pending_over_365"]].sum(axis=1)
    if not (ageing_sum == df["pending_total"]).all(): raise ValueError("Pending ageing buckets do not reconcile with pending_total.")
    df["disposal_rate"] = (df["disposed"] / df["received"].replace(0, pd.NA) * 100).round(2)
    df["pending_share"] = (df["pending_total"] / df["received"].replace(0, pd.NA) * 100).round(2)
    df["ageing_181_plus"] = df["pending_181_365"] + df["pending_over_365"]
    df["pressure_index"] = ((df["received"] + df["pending_total"]) / df["disposed"].clip(lower=1)).round(3)
    return df

def overview():
    df = load_data(); received=int(df.received.sum()); disposed=int(df.disposed.sum()); pending=int(df.pending_total.sum())
    return {"snapshot_date":str(df.snapshot_date.iloc[0]),"reporting_period":str(df.reporting_period.iloc[0]),"source":str(df.source.iloc[0]),"states_ut_count":int(len(df)),"received":received,"disposed":disposed,"pending":pending,"disposal_rate":round(disposed/received*100,2) if received else 0,"pending_share":round(pending/received*100,2) if received else 0}

def state_table(search=None, limit=100):
    df=load_data()
    if search: df=df[df.state_ut.str.contains(search.strip(),case=False,na=False)]
    cols=["state_ut","received","disposed","pending_total","disposal_rate","pending_share","ageing_181_plus","pressure_index"]
    return df[cols].sort_values("pending_total",ascending=False).head(limit).to_dict(orient="records")

def ageing():
    df=load_data(); return {"0_60":int(df.pending_0_60.sum()),"61_180":int(df.pending_61_180.sum()),"181_365":int(df.pending_181_365.sum()),"365_plus":int(df.pending_over_365.sum())}

def insights():
    df=load_data()
    return {"snapshot_date":str(df.snapshot_date.iloc[0]),"reporting_period":str(df.reporting_period.iloc[0]),"largest_pending_workloads":df.nlargest(5,"pending_total")[["state_ut","pending_total"]].to_dict(orient="records"),"largest_181_plus_workloads":df.nlargest(5,"ageing_181_plus")[["state_ut","ageing_181_plus"]].to_dict(orient="records"),"note":"Descriptive workload observations from this snapshot; not performance rankings or causal findings."}