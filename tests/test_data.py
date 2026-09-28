from pathlib import Path
import pandas as pd

DATA = Path(__file__).parents[1] / "data" / "cpgrams_snapshot.csv"

def test_dataset_exists(): assert DATA.exists()

def test_dataset_has_expected_columns_and_rows():
    df = pd.read_csv(DATA)
    required = {"state_ut","snapshot_date","reporting_period","received","disposed","pending_0_60","pending_61_180","pending_181_365","pending_over_365","pending_total","source"}
    assert required.issubset(df.columns)
    assert len(df) > 0

def test_ageing_reconciles_to_pending():
    df = pd.read_csv(DATA)
    ageing = df[["pending_0_60","pending_61_180","pending_181_365","pending_over_365"]].sum(axis=1)
    assert (ageing == df["pending_total"]).all()

def test_numeric_fields_are_non_negative_and_complete():
    df = pd.read_csv(DATA)
    numeric = ["received","disposed","pending_0_60","pending_61_180","pending_181_365","pending_over_365","pending_total"]
    assert not df[numeric].isna().any().any()
    assert (df[numeric] >= 0).all().all()

def test_current_snapshot_has_expected_disposal_relationship():
    df = pd.read_csv(DATA)
    assert (df["disposed"] >= 0).all()
    assert (df["received"] >= 0).all()

def test_validation_allows_carry_forward_disposals():
    from backend.app.analytics import validate_dataframe
    row = {
        "state_ut": "Example State",
        "snapshot_date": "2026-09-25",
        "reporting_period": "01/01/2026-25/09/2026",
        "received": 100,
        "disposed": 120,
        "pending_0_60": 10,
        "pending_61_180": 5,
        "pending_181_365": 3,
        "pending_over_365": 2,
        "pending_total": 20,
        "source": "https://example.gov.in/data",
    }
    validated = validate_dataframe(pd.DataFrame([row]))
    assert int(validated.loc[0, "disposed"]) == 120

def test_source_is_present_and_https():
    df = pd.read_csv(DATA)
    assert df["source"].notna().all()
    assert df["source"].str.startswith("https://").all()

def test_state_names_are_unique():
    df = pd.read_csv(DATA)
    assert df["state_ut"].is_unique
def test_ingestion_returns_validation_audit_summary():
    from backend.app.ingestion import ingest_csv_bytes
    csv = """state_ut,snapshot_date,reporting_period,received,disposed,pending_0_60,pending_61_180,pending_181_365,pending_over_365,pending_total,source
Example State,2026-09-25,01/01/2026-25/09/2026,100,120,10,5,3,2,20,https://example.gov.in/data
"""
    result = ingest_csv_bytes(csv.encode("utf-8"))
    assert result["validation"]["status"] == "passed"
    assert result["validation"]["record_count"] == 1
def test_duplicate_snapshot_registration_is_idempotent():
    from backend.app.snapshot import register_dataframe
    row = {
        "state_ut": "Concurrency Test State",
        "snapshot_date": "2098-01-01",
        "reporting_period": "01/01/2098-01/01/2098",
        "received": 10,
        "disposed": 12,
        "pending_0_60": 1,
        "pending_61_180": 1,
        "pending_181_365": 1,
        "pending_over_365": 1,
        "pending_total": 4,
        "source": "https://example.gov.in/data",
    }
    df = pd.DataFrame([row])
    first = register_dataframe(df)
    second = register_dataframe(df)
    assert first["status"] in {"registered", "already_registered"}
    assert second["status"] == "already_registered"
def test_validation_rejects_invalid_snapshot_date():
    from backend.app.analytics import validate_dataframe
    row = {
        "state_ut": "Invalid Date State",
        "snapshot_date": "2026-99-99",
        "reporting_period": "01/01/2026-25/09/2026",
        "received": 1,
        "disposed": 1,
        "pending_0_60": 1,
        "pending_61_180": 0,
        "pending_181_365": 0,
        "pending_over_365": 0,
        "pending_total": 1,
        "source": "https://example.gov.in/data",
    }
    with pytest.raises(ValueError, match="Snapshot date"):
        validate_dataframe(pd.DataFrame([row]))

def test_validation_rejects_reversed_reporting_period():
    from backend.app.analytics import validate_dataframe
    row = {
        "state_ut": "Reversed Period State",
        "snapshot_date": "2026-09-25",
        "reporting_period": "25/09/2026-01/01/2026",
        "received": 1,
        "disposed": 1,
        "pending_0_60": 1,
        "pending_61_180": 0,
        "pending_181_365": 0,
        "pending_over_365": 0,
        "pending_total": 1,
        "source": "https://example.gov.in/data",
    }
    with pytest.raises(ValueError, match="Reporting period"):
        validate_dataframe(pd.DataFrame([row]))
