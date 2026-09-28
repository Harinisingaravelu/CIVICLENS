# Power BI Integration

CIVICLENS exposes the validated dataset through:

`GET /api/v1/export/csv`

Recommended Power BI flow:
1. Run the CIVICLENS API.
2. Use **Get Data → Web** with the CSV endpoint.
3. Load the returned table.
4. Build cards for received, disposed and pending.
5. Build ageing visuals from the four pending-ageing columns.
6. Keep snapshot_date and reporting_period visible on the report.
7. Add the source URL as a provenance field.

Do not create historical trend visuals until multiple verified snapshots exist.

Suggested report pages:
- Executive Overview
- State Explorer
- Pending Ageing
- Data Provenance

CIVICLENS calculations should be labelled as project analytics, not official government scores.
