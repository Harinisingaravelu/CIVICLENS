# CIVICLENS API

Base URL: `http://localhost:8000`

## Health
`GET /health`

Returns service status.

## Readiness
`GET /ready`

Loads and validates the dataset and checks the SQLite registry.

## Overview
`GET /api/v1/overview`

Returns snapshot metadata and aggregate received, disposed, pending and disposal-rate calculations.

## State Explorer
`GET /api/v1/states?search=Tamil%20Nadu&limit=100`

Search is case-insensitive. Results are descriptive snapshot records.

## Ageing
`GET /api/v1/ageing`

Returns pending workload by ageing bucket.

## Insights
`GET /api/v1/insights`

Returns descriptive workload observations from the current snapshot.

## Snapshots
`GET /api/v1/snapshots`

Lists verified snapshots and provenance metadata, including SHA-256 dataset fingerprints.

`POST /api/v1/snapshots/register`

Registers the current repository CSV. Registration is idempotent.

## Historical intelligence
`GET /api/v1/history`

Returns the verified snapshot registry plus the latest comparison. If fewer than two verified snapshots exist, the comparison returns `status=unavailable`.

`GET /api/v1/history/compare?from_date=YYYY-MM-DD&to_date=YYYY-MM-DD`

Compares two registered snapshots. The response includes aggregate deltas, percentage changes where calculable, State/UT coverage differences and per-State/UT changes.

`GET /api/v1/history/state/{state_ut}`

Returns the verified timeline for one State/UT. Values are direct snapshot records; no interpolation is performed.

Historical changes are descriptive differences, not causal findings or performance rankings.

## Controlled snapshot ingestion
`POST /api/v1/snapshots/ingest`

Accepts one validated CSV snapshot as multipart upload.

This endpoint is **disabled by default**. Set `ENABLE_SNAPSHOT_INGESTION=true` only for a controlled local/admin workflow. The service enforces:
- CSV parsing
- 5 MB upload limit
- required schema
- numeric and non-negative measures
- ageing reconciliation
- unique State/UT records
- `disposed <= received`
- one snapshot date/reporting period/source per file
- HTTPS source URLs
- duplicate snapshot identity/fingerprint protection

Do not expose this endpoint publicly without adding an authentication/authorization layer.

## AI
`POST /api/v1/ai/ask`

Body:
```json
{"question":"What is the pending workload in Tamil Nadu?"}
```

Gemini answers are grounded in deterministic CIVICLENS results or a compact dataset context.

## Export
`GET /api/v1/export/csv`

Downloads the validated current dataset used by the application.

## Monitoring
`GET /metrics`

Returns lightweight in-process request counts and recent timing metadata. Request bodies, API keys and user questions are not stored.

## Interpretation
Disposal rate and pressure index are analytical calculations. `pressure_index` is a CIVICLENS exploratory metric, not an official government score. Snapshot and historical observations should not be treated as causal explanations or overall performance rankings.
