from pathlib import Path
import pandas as pd

DATA = Path(__file__).parents[1] / "data" / "cpgrams_snapshot.csv"

def test_dataset_exists():
    assert DATA.exists()

def test_dataset_has_expected_rows_and_columns():
    df = pd.read_csv(DATA)
    required = {
        "state_ut","received","disposed","pending_0_60",
        "pending_61_180","pending_181_365","pending_over_365",
        "pending_total"
    }
    assert required.issubset(df.columns)
    assert len(df) > 0

def test_ageing_reconciles_to_pending():
    df = pd.read_csv(DATA)
    ageing = df[["pending_0_60","pending_61_180","pending_181_365","pending_over_365"]].sum(axis=1)
    assert (ageing == df["pending_total"]).all()
