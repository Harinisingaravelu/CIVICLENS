from pathlib import Path
import pandas as pd

DATA = Path(__file__).parents[1] / "data" / "cpgrams_snapshot.csv"

def test_dataset_exists():
    assert DATA.exists()

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

def test_disposed_does_not_exceed_received():
    df = pd.read_csv(DATA)
    assert (df["disposed"] <= df["received"]).all()

def test_source_is_present():
    df = pd.read_csv(DATA)
    assert df["source"].notna().all()
    assert df["source"].str.startswith("https://").all()
