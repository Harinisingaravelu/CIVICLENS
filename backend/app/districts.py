from __future__ import annotations

from pathlib import Path
import pandas as pd

# Official Local Government Directory (LGD) district counts.
# Source: Ministry of Panchayati Raj, Government of India.
# These are administrative-directory counts, not CPGRAMS grievance counts.
LGD_SOURCE = "https://lgdirectory.gov.in/"
LGD_REPORT_DATE = "2026-07-14"

DISTRICT_COUNTS = {
    "Andaman And Nicobar Islands": 3,
    "Andhra Pradesh": 28,
    "Arunachal Pradesh": 27,
    "Assam": 35,
    "Bihar": 38,
    "Chandigarh": 1,
    "Chhattisgarh": 33,
    "Delhi": 13,
    "Goa": 3,
    "Gujarat": 34,
    "Haryana": 23,
    "Himachal Pradesh": 12,
    "Jammu And Kashmir": 20,
    "Jharkhand": 24,
    "Karnataka": 31,
    "Kerala": 14,
    "Ladakh": 2,
    "Lakshadweep": 1,
    "Madhya Pradesh": 55,
    "Maharashtra": 36,
    "Manipur": 16,
    "Meghalaya": 12,
    "Mizoram": 11,
    "Nagaland": 17,
    "Odisha": 30,
    "Puducherry": 2,
    "Punjab": 23,
    "Rajasthan": 41,
    "Sikkim": 6,
    "Tamil Nadu": 38,
    "Telangana": 33,
    "The Dadra And Nagar Haveli And Daman And Diu": 3,
    "Tripura": 8,
    "Uttar Pradesh": 75,
    "Uttarakhand": 13,
    "West Bengal": 23,
}

ALIASES = {
    "NCT of Delhi": "Delhi",
    "Union Territory of Delhi": "Delhi",
    "Union Territory of Andaman & Nicobar": "Andaman And Nicobar Islands",
    "Union Territory of Chandigarh": "Chandigarh",
    "Union Territory of Ladakh": "Ladakh",
    "Union Territory of Lakshadweep": "Lakshadweep",
    "Union Territory of Puducherry": "Puducherry",
    "Union Territory of Jammu & Kashmir": "Jammu And Kashmir",
    "Dadra And Nagar Haveli": "The Dadra And Nagar Haveli And Daman And Diu",
    "Daman & Diu": "The Dadra And Nagar Haveli And Daman And Diu",
    "Union Territory of Dadra & Nagar Haveli": "The Dadra And Nagar Haveli And Daman And Diu",
    "Union Territory of Daman & Diu": "The Dadra And Nagar Haveli And Daman And Diu",
    "Chattisgarh": "Chhattisgarh",
}


def canonical_state(name: str) -> str | None:
    clean = " ".join(str(name).strip().split())
    if clean in DISTRICT_COUNTS:
        return clean
    if clean in ALIASES:
        return ALIASES[clean]
    folded = {k.casefold(): k for k in DISTRICT_COUNTS}
    return folded.get(clean.casefold())


def _metrics_dataset_path() -> Path:
    return Path(__file__).resolve().parents[2] / "data" / "cpgrams_district_snapshot.csv"


def district_metrics_available() -> bool:
    return _metrics_dataset_path().exists()


def coverage() -> dict:
    total = sum(DISTRICT_COUNTS.values())
    return {
        "directory_available": True,
        "district_metrics_available": district_metrics_available(),
        "states_ut_with_directory": len(DISTRICT_COUNTS),
        "total_districts": total,
        "directory_source": LGD_SOURCE,
        "directory_report_date": LGD_REPORT_DATE,
        "metrics_source": (
            "Official CPGRAMS district-level dataset"
            if district_metrics_available()
            else None
        ),
        "note": (
            "The public CPGRAMS dashboard currently exposes department and State/UT "
            "tables. CIVICLENS does not manufacture district grievance metrics. "
            "District analytics activate only when a verified district-level CPGRAMS "
            "snapshot is supplied."
        ),
    }


def district_table(search: str | None = None, limit: int = 100) -> list[dict]:
    rows = [
        {
            "state_ut": state,
            "district_count": count,
            "metrics_available": district_metrics_available(),
            "directory_source": LGD_SOURCE,
            "directory_report_date": LGD_REPORT_DATE,
        }
        for state, count in DISTRICT_COUNTS.items()
    ]
    if search:
        needle = search.strip().casefold()
        rows = [r for r in rows if needle in r["state_ut"].casefold()]
    return rows[:limit]


def state_district_detail(state_ut: str) -> dict:
    canonical = canonical_state(state_ut)
    if canonical is None:
        return {
            "status": "not_found",
            "state_ut": state_ut,
            "reason": "The State/UT is not present in the current LGD directory snapshot.",
        }

    return {
        "status": "ok",
        "state_ut": canonical,
        "district_count": DISTRICT_COUNTS[canonical],
        "metrics_available": district_metrics_available(),
        "directory_source": LGD_SOURCE,
        "directory_report_date": LGD_REPORT_DATE,
        "metrics_source": (
            "Verified CPGRAMS district snapshot"
            if district_metrics_available()
            else None
        ),
        "metric_fields": [
            "received",
            "disposed",
            "pending_total",
            "pending_0_60",
            "pending_61_180",
            "pending_181_365",
            "pending_over_365",
            "disposal_rate",
            "ageing_181_plus",
            "ageing_181_plus_share",
        ] if district_metrics_available() else [],
        "note": (
            "Administrative district count comes from LGD. Grievance metrics are "
            "not inferred from the State/UT totals."
        ),
    }


def export_directory_csv() -> bytes:
    df = pd.DataFrame(district_table(limit=1000))
    return df.to_csv(index=False).encode("utf-8")
