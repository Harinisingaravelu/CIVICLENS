from __future__ import annotations

from pathlib import Path
from threading import Lock
import re
import time

import httpx
import pandas as pd
from lxml import html

# Administrative directory source: Government of India Integrated Government Online Directory
# (NIC) / Local Government Directory. District grievance metrics are kept separate.
IGOD_SOURCE = "https://igod.gov.in/districts"
IGOD_BASE = "https://igod.gov.in/sg/{code}/E042/organizations"
LGD_SOURCE = "https://lgdirectory.gov.in/"
DIRECTORY_REPORT_DATE = "2026-08-10"

STATE_CODES = {
    "Andaman And Nicobar Islands": "AN",
    "Andhra Pradesh": "AP",
    "Arunachal Pradesh": "AR",
    "Assam": "AS",
    "Bihar": "BR",
    "Chandigarh": "CH",
    "Chhattisgarh": "CG",
    "The Dadra And Nagar Haveli And Daman And Diu": "ND",
    "Delhi": "DL",
    "Goa": "GA",
    "Gujarat": "GJ",
    "Haryana": "HR",
    "Himachal Pradesh": "HP",
    "Jammu And Kashmir": "JK",
    "Jharkhand": "JH",
    "Karnataka": "KA",
    "Kerala": "KL",
    "Ladakh": "LA",
    "Lakshadweep": "LD",
    "Madhya Pradesh": "MP",
    "Maharashtra": "MH",
    "Manipur": "MN",
    "Meghalaya": "ML",
    "Mizoram": "MZ",
    "Nagaland": "NL",
    "Odisha": "OD",
    "Puducherry": "PY",
    "Punjab": "PB",
    "Rajasthan": "RJ",
    "Sikkim": "SK",
    "Tamil Nadu": "TN",
    "Telangana": "TS",
    "Tripura": "TR",
    "Uttar Pradesh": "UP",
    "Uttarakhand": "UK",
    "West Bengal": "WB",
}

# Current directory counts observed from the official directory. The live district
# list endpoint below is authoritative for names; these counts keep the dashboard
# useful even when the directory site is temporarily unavailable.
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

UT_NAMES = {
    "Andaman And Nicobar Islands",
    "Chandigarh",
    "Delhi",
    "Jammu And Kashmir",
    "Ladakh",
    "Lakshadweep",
    "Puducherry",
    "The Dadra And Nagar Haveli And Daman And Diu",
}

_CACHE: dict[str, tuple[float, list[dict]]] = {}
_CACHE_LOCK = Lock()
CACHE_SECONDS = 6 * 60 * 60


def canonical_state(name: str) -> str | None:
    clean = " ".join(str(name).strip().split())
    if clean in DISTRICT_COUNTS:
        return clean
    if clean in ALIASES:
        return ALIASES[clean]
    folded = {k.casefold(): k for k in DISTRICT_COUNTS}
    return folded.get(clean.casefold())


def state_type(name: str) -> str:
    return "Union Territory" if name in UT_NAMES else "State"


def district_metrics_available() -> bool:
    return (Path(__file__).resolve().parents[2] / "data" / "cpgrams_district_snapshot.csv").exists()


def coverage() -> dict:
    return {
        "directory_available": True,
        "district_metrics_available": district_metrics_available(),
        "states_ut_with_directory": len(DISTRICT_COUNTS),
        "total_districts": sum(DISTRICT_COUNTS.values()),
        "directory_source": IGOD_SOURCE,
        "lgd_source": LGD_SOURCE,
        "directory_report_date": DIRECTORY_REPORT_DATE,
        "metrics_source": "Official CPGRAMS district-level dataset" if district_metrics_available() else None,
        "note": (
            "District names are resolved from the Government of India directory. "
            "CPGRAMS State/UT totals are never split into districts."
        ),
    }


def district_table(search: str | None = None, limit: int = 100) -> list[dict]:
    rows = [
        {
            "state_ut": state,
            "administrative_type": state_type(state),
            "district_count": count,
            "metrics_available": district_metrics_available(),
            "directory_source": IGOD_SOURCE,
            "directory_report_date": DIRECTORY_REPORT_DATE,
        }
        for state, count in DISTRICT_COUNTS.items()
    ]
    if search:
        needle = search.strip().casefold()
        rows = [r for r in rows if needle in r["state_ut"].casefold()]
    return rows[:limit]


def _clean_district_name(value: str) -> str:
    value = re.sub(r"\s+", " ", value or "").strip()
    return value


def _parse_igod_districts(markup: str, expected: int | None = None) -> list[str]:
    tree = html.fromstring(markup)
    names: list[str] = []

    for sub_link in tree.xpath("//a[normalize-space()='Sub Districts']"):
        previous = sub_link.xpath("./preceding-sibling::*[1]")
        if previous:
            name = " ".join(previous[0].itertext())
        else:
            previous_text = sub_link.xpath("./preceding-sibling::text()[normalize-space()][1]")
            name = previous_text[0] if previous_text else ""

        name = _clean_district_name(name)
        if name and name.lower() not in {"blocks", "sub districts"}:
            names.append(name)

    # Some directory entries are represented by a text node followed by the
    # Sub Districts link, while others use an anchor. Deduplicate without
    # changing the official directory order.
    output: list[str] = []
    seen: set[str] = set()
    for name in names:
        key = name.casefold()
        if key not in seen:
            seen.add(key)
            output.append(name)

    if expected is not None and len(output) != expected:
        raise ValueError(f"IGOD district parser found {len(output)} records; expected {expected}.")
    return output


def district_items(state_ut: str, search: str | None = None) -> list[dict]:
    canonical = canonical_state(state_ut)
    if canonical is None:
        raise KeyError(state_ut)

    expected = DISTRICT_COUNTS[canonical]
    now = time.time()
    with _CACHE_LOCK:
        cached = _CACHE.get(canonical)
    if cached and now - cached[0] < CACHE_SECONDS:
        names = cached[1]
    else:
        code = STATE_CODES[canonical]
        url = IGOD_BASE.format(code=code)
        try:
            response = httpx.get(
                url,
                headers={"User-Agent": "CIVICLENS/1.0 (+https://github.com/Harinisingaravelu/CIVICLENS)"},
                timeout=20.0,
                follow_redirects=True,
            )
            response.raise_for_status()
            names = _parse_igod_districts(response.text, expected=expected)
        except (httpx.HTTPError, ValueError, IndexError) as exc:
            raise RuntimeError(f"Official district directory is temporarily unavailable for {canonical}.") from exc
        with _CACHE_LOCK:
            _CACHE[canonical] = (now, names)

    needle = search.strip().casefold() if search else ""
    if needle:
        names = [name for name in names if needle in name.casefold()]

    return [
        {
            "state_ut": canonical,
            "administrative_type": state_type(canonical),
            "district": name,
            "metrics_available": district_metrics_available(),
            "directory_source": IGOD_SOURCE,
            "directory_report_date": DIRECTORY_REPORT_DATE,
        }
        for name in names
    ]


def state_district_detail(state_ut: str) -> dict:
    canonical = canonical_state(state_ut)
    if canonical is None:
        return {
            "status": "not_found",
            "state_ut": state_ut,
            "reason": "The State/UT is not present in the current Government of India directory.",
        }

    return {
        "status": "ok",
        "state_ut": canonical,
        "administrative_type": state_type(canonical),
        "district_count": DISTRICT_COUNTS[canonical],
        "metrics_available": district_metrics_available(),
        "directory_source": IGOD_SOURCE,
        "directory_report_date": DIRECTORY_REPORT_DATE,
        "metrics_source": "Verified CPGRAMS district snapshot" if district_metrics_available() else None,
        "note": (
            "District names are available from the Government of India directory. "
            "Grievance metrics are not inferred from State/UT totals."
        ),
    }


def export_directory_csv() -> bytes:
    df = pd.DataFrame(district_table(limit=1000))
    return df.to_csv(index=False).encode("utf-8")
