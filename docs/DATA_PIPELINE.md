# CIVICLENS Data Pipeline

## Source
Primary source: CPGRAMS DARPG dashboard.

## Current model
Source snapshot → CSV provenance layer → validation → analytics → API → dashboard / AI / BI export.

## Validation gates
1. Required columns exist.
2. Numeric fields are numeric.
3. Numeric measures are non-negative.
4. Ageing buckets reconcile to pending_total.
5. Source URL is present.
6. The application never silently converts missing source values to zero.

## Refresh process
A new official snapshot should be saved as a new version after manual verification of:
- snapshot date
- reporting period
- State/UT coverage
- column definitions
- source URL
- ageing reconciliation

Do not overwrite historical evidence without recording the new snapshot date.

## Important limitation
The current repository contains a snapshot, not a fabricated time series. Trend analysis must wait for multiple verified time periods.
