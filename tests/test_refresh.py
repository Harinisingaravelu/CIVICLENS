from pathlib import Path
import sys

import pandas as pd

sys.path.insert(0, str(Path(__file__).parents[1]))

from scripts.refresh_cpgrams_snapshot import parse_state_table


def test_parse_state_table_from_official_style_html():
    html = """
    <html>
      <h3>Status of Grievances Department-wise/State/UT between 01/01/2026 and 25/09/2026</h3>
      <table>
        <tr><th>Organization Name</th><th>Received</th><th># Disposed</th><th>% Disposed</th>
        <th>Pending 0-60 Days</th><th>Pending 60-180 Days</th>
        <th>Pending 180-365 Days</th><th>Pending More than 1 Year</th></tr>
        <tr><td>Department A</td><td>10</td><td>9</td><td>90.00</td><td>1</td><td>0</td><td>0</td><td>0</td></tr>
      </table>
      <table>
        <tr><th>Organization Name</th><th>Received</th><th># Disposed</th><th>% Disposed</th>
        <th>Pending 0-60 Days</th><th>Pending 60-180 Days</th>
        <th>Pending 180-365 Days</th><th>Pending More than 1 Year</th></tr>
        <tr><td>Tamil Nadu</td><td>25,081</td><td>18,819</td><td>75.03</td><td>3127</td><td>2233</td><td>902</td><td>0</td></tr>
      </table>
    </html>
    """
    df = parse_state_table(html)
    assert len(df) == 1
    assert df.loc[0, "state_ut"] == "Tamil Nadu"
    assert int(df.loc[0, "pending_total"]) == 6262
    assert df.loc[0, "snapshot_date"] == "2026-09-25"
    assert df.loc[0, "reporting_period"] == "01/01/2026-25/09/2026"
    assert df.loc[0, "source"] == "https://pgportal.gov.in/darpgdashboard"


def test_refresh_parser_preserves_required_schema():
    html = """
    <h3>Status of Grievances State/UT between 01/01/2026 and 25/09/2026</h3>
    <table>
      <tr><th>Organization Name</th><th>Received</th><th># Disposed</th><th>% Disposed</th>
      <th>Pending 0-60 Days</th><th>Pending 60-180 Days</th>
      <th>Pending 180-365 Days</th><th>Pending More than 1 Year</th></tr>
      <tr><td>Example UT</td><td>100</td><td>120</td><td>120.00</td><td>10</td><td>5</td><td>3</td><td>2</td></tr>
    </table>
    """
    df = parse_state_table(html)
    assert list(df.columns) == [
        "state_ut", "snapshot_date", "reporting_period", "received", "disposed",
        "pending_0_60", "pending_61_180", "pending_181_365",
        "pending_over_365", "pending_total", "source"
    ]
    assert int(df.loc[0, "pending_total"]) == 20
