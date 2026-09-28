from .analytics import load_data

def readiness():
    df = load_data()
    return {
        "status": "ready",
        "dataset_rows": int(len(df)),
        "snapshot_date": str(df["snapshot_date"].iloc[0]),
        "source_available": bool(df["source"].notna().all()),
    }
