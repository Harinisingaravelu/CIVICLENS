# CIVICLENS Data Pipeline

## Source
Primary source: CPGRAMS DARPG dashboard.

## Current model
Official source snapshot → CSV provenance layer → validation → SQLite snapshot registry → historical comparison → Python analytics → API → dashboard / AI / BI export.

## Validation gates
1. Required columns exist.
2. Numeric fields are numeric.
3. Numeric measures are non-negative.
4. `disposed <= received`.
5. Ageing buckets reconcile to `pending_total`.
6. State/UT names are present and unique.
7. Source URL is present and HTTPS.
8. A snapshot file contains exactly one snapshot date, reporting period and source URL.
9. Duplicate snapshot fingerprints and snapshot identities are not re-registered.

## Snapshot lifecycle
1. Obtain a new official CPGRAMS snapshot.
2. Preserve the source URL, snapshot date and reporting period.
3. Save it as a separate verified snapshot file.
4. Run the validation/test suite.
5. Register it through the controlled ingestion workflow or repository update.
6. The registry stores a SHA-256 fingerprint and State/UT records.
7. Historical comparison becomes available only after at least two verified snapshots are registered.

## Historical methodology
For two verified snapshots, CIVICLENS computes:
- absolute change: later value minus earlier value
- percentage change: absolute change divided by earlier value, when the earlier value is non-zero
- State/UT coverage differences
- per-State/UT changes for received, disposed, pending and ageing buckets

These are descriptive dataset differences. They do not establish causes, service quality, intent or policy effectiveness.

## Important limitation
The repository currently contains one real production snapshot. CIVICLENS must not fabricate historical values to create a trend. The dashboard explicitly shows historical comparison as unavailable until a second verified snapshot exists.

## Security
Snapshot ingestion is disabled by default. If enabled for local/admin use, protect the service with an appropriate authentication/authorization layer before exposing it outside a trusted environment.
