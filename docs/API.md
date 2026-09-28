# CIVICLENS API

Base URL: `http://localhost:8000`

## Health
`GET /health`

Returns service status.

## Readiness
`GET /ready`

Loads and validates the dataset before returning readiness.

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

## AI
`POST /api/v1/ai/ask`

Body:
```json
{"question":"What is the pending workload in Tamil Nadu?"}
```

Gemini answers are grounded in the CIVICLENS dataset context.

## Export
`GET /api/v1/export/csv`

Downloads the validated dataset used by the application.

## Interpretation
CIVICLENS calculations are independent analytics. The exploratory `pressure_index` is not an official government metric.
