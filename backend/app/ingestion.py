from __future__ import annotations

from io import BytesIO
import pandas as pd

from .analytics import REQUIRED_COLUMNS, validate_dataframe
from .snapshot import register_dataframe


def ingest_csv_bytes(content: bytes) -> dict:
    if not content:
        raise ValueError("Uploaded CSV is empty.")
    if len(content) > 5 * 1024 * 1024:
        raise ValueError("Uploaded CSV exceeds the 5 MB safety limit.")
    try:
        df = pd.read_csv(BytesIO(content))
    except Exception as exc:
        raise ValueError("Uploaded file is not a readable CSV dataset.") from exc

    validated = validate_dataframe(df)
    result = register_dataframe(validated)
    result["validation"] = {
        "status": "passed",
        "required_columns": len(REQUIRED_COLUMNS),
        "record_count": int(len(validated)),
        "snapshot_date": str(validated["snapshot_date"].iloc[0]),
        "reporting_period": str(validated["reporting_period"].iloc[0]),
        "source_url": str(validated["source"].iloc[0]),
    }
    return result
