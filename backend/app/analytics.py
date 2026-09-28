from pathlib import Path
import pandas as pd

DATA_FILE = Path(__file__).resolve().parents[2] / "data" / "cpgrams_snapshot.csv"

def load_data() -> pd.DataFrame:
    df = pd.read_csv(DATA_FILE)
    numeric = [
        "received","disposed","pending_0_60","pending_61_180",
        "pending_181_365","pending_over_365","pending_total"
    ]
    for col in numeric:
        df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0)
    df["disposal_rate"] = (df["disposed"] / df["received"].replace(0, pd.NA) * 100).round(2)
    df["ageing_181_plus"] = df["pending_181_365"] + df["pending_over_365"]
    df["pressure_index"] = ((df["received"] + df["pending_total"]) /
                            df["disposed"].clip(lower=1)).round(3)
    return df

def overview():
    df = load_data()
    received, disposed, pending = df["received"].sum(), df["disposed"].sum(), df["pending_total"].sum()
    return {
        "snapshot_date": str(df["snapshot_date"].iloc[0]),
        "reporting_period": str(df["reporting_period"].iloc[0]),
        "states_ut_count": int(len(df)),
        "received": int(received),
        "disposed": int(disposed),
        "pending": int(pending),
        "disposal_rate": round(disposed / received * 100, 2) if received else 0,
    }

def state_table():
    df = load_data()
    cols = ["state_ut","received","disposed","pending_total","disposal_rate","ageing_181_plus","pressure_index"]
    return df[cols].sort_values("pending_total", ascending=False).to_dict(orient="records")

def ageing():
    df = load_data()
    return {
        "0_60": int(df["pending_0_60"].sum()),
        "61_180": int(df["pending_61_180"].sum()),
        "181_365": int(df["pending_181_365"].sum()),
        "365_plus": int(df["pending_over_365"].sum()),
    }
