from pathlib import Path
import pandas as pd

DATA_FILE = Path(__file__).resolve().parents[2] / "data" / "cpgrams_snapshot.csv"
REQUIRED_COLUMNS = [
    "state_ut", "snapshot_date", "reporting_period", "received", "disposed",
    "pending_0_60", "pending_61_180", "pending_181_365", "pending_over_365",
    "pending_total", "source"
]
NUMERIC_COLUMNS = REQUIRED_COLUMNS[3:10]


def validate_dataframe(df: pd.DataFrame) -> pd.DataFrame:
    missing = [c for c in REQUIRED_COLUMNS if c not in df.columns]
    if missing:
        raise ValueError(f"Dataset is missing required columns: {', '.join(missing)}.")
    if df.empty:
        raise ValueError("Dataset is empty.")

    df = df[REQUIRED_COLUMNS].copy()
    for col in NUMERIC_COLUMNS:
        df[col] = pd.to_numeric(df[col], errors="coerce")

    if df[NUMERIC_COLUMNS].isna().any().any():
        raise ValueError("Dataset contains missing/non-numeric values.")
    if (df[NUMERIC_COLUMNS] < 0).any().any():
        raise ValueError("Dataset contains negative numeric values.")
    if df["state_ut"].astype(str).str.strip().eq("").any():
        raise ValueError("Dataset contains blank State/UT names.")
    if df["state_ut"].duplicated().any():
        raise ValueError("Dataset contains duplicate State/UT records.")

    # CPGRAMS states that disposals can include carry-forward receipts from
    # previous year(s), so disposed is not required to be <= current receipts.
    ageing_sum = df[
        ["pending_0_60", "pending_61_180", "pending_181_365", "pending_over_365"]
    ].sum(axis=1)
    if not ageing_sum.eq(df["pending_total"]).all():
        raise ValueError("Pending ageing buckets do not reconcile with pending_total.")

    if df["source"].astype(str).str.strip().eq("").any():
        raise ValueError("Dataset contains blank source URLs.")
    if not df["source"].astype(str).str.startswith("https://").all():
        raise ValueError("Every source URL must use HTTPS.")

    if (
        df["snapshot_date"].nunique() != 1
        or df["reporting_period"].nunique() != 1
        or df["source"].nunique() != 1
    ):
        raise ValueError(
            "A snapshot CSV must contain exactly one snapshot date, reporting period and source URL."
        )

    snapshot_dates = pd.to_datetime(
        df["snapshot_date"], format="%Y-%m-%d", errors="coerce"
    )
    if snapshot_dates.isna().any():
        raise ValueError("Snapshot date must use YYYY-MM-DD format.")

    periods = df["reporting_period"].astype(str).str.strip()
    parts = periods.str.extract(
        r"^(\d{2}/\d{2}/\d{4})-(\d{2}/\d{2}/\d{4})$"
    )
    if parts.isna().any().any():
        raise ValueError("Reporting period must use START-END format.")

    start_dates = pd.to_datetime(parts[0], format="%d/%m/%Y", errors="coerce")
    end_dates = pd.to_datetime(parts[1], format="%d/%m/%Y", errors="coerce")
    if (
        start_dates.isna().any()
        or end_dates.isna().any()
        or (start_dates > end_dates).any()
    ):
        raise ValueError(
            "Reporting period must contain valid DD/MM/YYYY dates in chronological order."
        )

    return df


def _add_metrics(df: pd.DataFrame) -> pd.DataFrame:
    received = df["received"].replace(0, pd.NA)
    pending = df["pending_total"].replace(0, pd.NA)

    df["disposal_rate"] = (df["disposed"] / received * 100).round(2)
    df["pending_share"] = (df["pending_total"] / received * 100).round(2)
    df["ageing_181_plus"] = df["pending_181_365"] + df["pending_over_365"]
    df["ageing_181_plus_share"] = (
        df["ageing_181_plus"] / pending * 100
    ).round(2)

    # Exploratory project metric only. It is NOT an official CPGRAMS metric.
    df["pressure_index"] = (
        (df["received"] + df["pending_total"])
        / df["disposed"].clip(lower=1)
    ).round(3)

    return df


def load_data() -> pd.DataFrame:
    return _add_metrics(validate_dataframe(pd.read_csv(DATA_FILE)))


def overview():
    df = load_data()
    received = int(df["received"].sum())
    disposed = int(df["disposed"].sum())
    pending = int(df["pending_total"].sum())
    ageing_181_plus = int(df["ageing_181_plus"].sum())

    return {
        "snapshot_date": str(df["snapshot_date"].iloc[0]),
        "reporting_period": str(df["reporting_period"].iloc[0]),
        "source": str(df["source"].iloc[0]),
        "states_ut_count": int(len(df)),
        "received": received,
        "disposed": disposed,
        "pending": pending,
        "disposal_rate": round(disposed / received * 100, 2) if received else 0,
        "pending_share": round(pending / received * 100, 2) if received else 0,
        "ageing_181_plus": ageing_181_plus,
        "ageing_181_plus_share": (
            round(ageing_181_plus / pending * 100, 2) if pending else 0
        ),
    }


def state_table(search=None, limit=100):
    df = load_data()
    if search:
        df = df[
            df["state_ut"].str.contains(
                search.strip(), case=False, na=False, regex=False
            )
        ]

    cols = [
        "state_ut", "received", "disposed", "pending_total",
        "disposal_rate", "pending_share", "ageing_181_plus",
        "ageing_181_plus_share", "pressure_index"
    ]
    return (
        df[cols]
        .sort_values("pending_total", ascending=False)
        .head(limit)
        .to_dict(orient="records")
    )


def ageing():
    df = load_data()
    return {
        "0_60": int(df["pending_0_60"].sum()),
        "61_180": int(df["pending_61_180"].sum()),
        "181_365": int(df["pending_181_365"].sum()),
        "365_plus": int(df["pending_over_365"].sum()),
    }


def data_quality():
    df = validate_dataframe(pd.read_csv(DATA_FILE))
    ageing_sum = df[
        ["pending_0_60", "pending_61_180", "pending_181_365", "pending_over_365"]
    ].sum(axis=1)

    return {
        "status": "passed",
        "rows": int(len(df)),
        "unique_states_ut": int(df["state_ut"].nunique()),
        "duplicate_states_ut": int(df["state_ut"].duplicated().sum()),
        "missing_numeric_values": int(df[NUMERIC_COLUMNS].isna().sum().sum()),
        "negative_numeric_values": int((df[NUMERIC_COLUMNS] < 0).sum().sum()),
        "ageing_reconciliation_errors": int(
            (~ageing_sum.eq(df["pending_total"])).sum()
        ),
        "source_is_https": bool(
            df["source"].astype(str).str.startswith("https://").all()
        ),
        "snapshot_date": str(df["snapshot_date"].iloc[0]),
        "reporting_period": str(df["reporting_period"].iloc[0]),
    }


def insights():
    df = load_data()
    total_pending = int(df["pending_total"].sum())
    top5_pending = df.nlargest(5, "pending_total")
    top5_pending_total = int(top5_pending["pending_total"].sum())

    return {
        "snapshot_date": str(df["snapshot_date"].iloc[0]),
        "reporting_period": str(df["reporting_period"].iloc[0]),
        "largest_pending_workloads": top5_pending[
            ["state_ut", "pending_total"]
        ].to_dict(orient="records"),
        "largest_181_plus_workloads": df.nlargest(5, "ageing_181_plus")[
            ["state_ut", "ageing_181_plus"]
        ].to_dict(orient="records"),
        "top5_pending_share": (
            round(top5_pending_total / total_pending * 100, 2)
            if total_pending
            else 0
        ),
        "note": (
            "Descriptive workload observations from this snapshot; "
            "not performance rankings or causal findings."
        ),
    }
