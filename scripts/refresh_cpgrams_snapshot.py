"""Refresh the CIVICLENS State/UT snapshot from the official CPGRAMS dashboard.

Usage:
    python scripts/refresh_cpgrams_snapshot.py

The script reads the State/UT table published by DARPG/CPGRAMS, derives
pending_total from the published ageing buckets, validates the result through
the same analytics contract used by the API, and replaces data/cpgrams_snapshot.csv.
"""
from __future__ import annotations

from io import StringIO
from pathlib import Path
import re
import tempfile
import time

import httpx
import pandas as pd

from backend.app.analytics import REQUIRED_COLUMNS, validate_dataframe

SOURCE_URL = "https://pgportal.gov.in/darpgdashboard"
DATA_FILE = Path(__file__).resolve().parents[1] / "data" / "cpgrams_snapshot.csv"

RAW_COLUMNS = [
    "Organization Name",
    "Received",
    "# Disposed",
    "% Disposed",
    "Pending 0-60 Days",
    "Pending 60-180 Days",
    "Pending 180-365 Days",
    "Pending More than 1 Year",
]


def _number(value: object) -> int:
    text = str(value).replace(",", "").strip()
    return int(float(text or "0"))


def _reporting_period(html: str) -> tuple[str, str]:
    matches = re.findall(
        r"between\s+(\d{2}/\d{2}/\d{4})\s+and\s+(\d{2}/\d{2}/\d{4})",
        html,
        flags=re.IGNORECASE,
    )
    if not matches:
        raise ValueError("Could not find the reporting period on the CPGRAMS dashboard.")
    start, end = matches[0]
    return start, end


def parse_state_table(html: str) -> pd.DataFrame:
    start, end = _reporting_period(html)
    tables = pd.read_html(StringIO(html))
    candidates = [
        table for table in tables
        if set(RAW_COLUMNS).issubset({str(column).strip() for column in table.columns})
    ]
    if not candidates:
        raise ValueError("Could not find a CPGRAMS State/UT table with the expected columns.")

    # The State/UT table follows the department-wise table on the official page.
    table = candidates[-1].copy()
    table.columns = [str(column).strip() for column in table.columns]
    table = table[RAW_COLUMNS].rename(
        columns={
            "Organization Name": "state_ut",
            "Received": "received",
            "# Disposed": "disposed",
            "Pending 0-60 Days": "pending_0_60",
            "Pending 60-180 Days": "pending_61_180",
            "Pending 180-365 Days": "pending_181_365",
            "Pending More than 1 Year": "pending_over_365",
        }
    )
    table["state_ut"] = table["state_ut"].astype(str).str.strip()
    numeric = [
        "received",
        "disposed",
        "pending_0_60",
        "pending_61_180",
        "pending_181_365",
        "pending_over_365",
    ]
    for column in numeric:
        table[column] = table[column].map(_number)
    table["pending_total"] = table[
        ["pending_0_60", "pending_61_180", "pending_181_365", "pending_over_365"]
    ].sum(axis=1)

    end_date = pd.to_datetime(end, format="%d/%m/%Y").strftime("%Y-%m-%d")
    table["snapshot_date"] = end_date
    table["reporting_period"] = f"{start}-{end}"
    table["source"] = SOURCE_URL

    result = table[REQUIRED_COLUMNS]
    validate_dataframe(result)
    return result


def refresh() -> pd.DataFrame:
    last_error: Exception | None = None
    for attempt in range(3):
        try:
            response = httpx.get(
                SOURCE_URL,
                timeout=httpx.Timeout(30.0, connect=10.0),
                follow_redirects=True,
                headers={"User-Agent": "CIVICLENS-data-refresh/1.0"},
            )
            response.raise_for_status()
            dataframe = parse_state_table(response.text)

            # Replace the snapshot atomically so an interrupted refresh never
            # leaves a partially-written CSV for the API to consume.
            DATA_FILE.parent.mkdir(parents=True, exist_ok=True)
            with tempfile.NamedTemporaryFile(
                "w", encoding="utf-8", newline="", dir=DATA_FILE.parent,
                delete=False, suffix=".tmp"
            ) as tmp:
                temp_path = Path(tmp.name)
                dataframe.to_csv(tmp, index=False)
            temp_path.replace(DATA_FILE)
            return dataframe
        except (httpx.HTTPError, ValueError) as exc:
            last_error = exc
            if attempt < 2:
                time.sleep(2 ** attempt)

    raise RuntimeError(f"CPGRAMS refresh failed after 3 attempts: {last_error}") from last_error


if __name__ == "__main__":
    refreshed = refresh()
    print(
        f"Refreshed {len(refreshed)} State/UT records: "
        f"{refreshed['snapshot_date'].iloc[0]} "
        f"({refreshed['reporting_period'].iloc[0]})."
    )
