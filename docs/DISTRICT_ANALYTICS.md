# District Analytics

## Administrative directory

CIVICLENS uses the Government of India Local Government Directory (LGD) as the authoritative administrative directory for current State/UT-to-district counts.

Source: https://lgdirectory.gov.in/
Reference report date used by the current directory layer: 2026-07-14.

The directory layer currently exposes the State/UT district count and lets the UI drill into a selected State/UT.

## Grievance metric integrity

The public CPGRAMS dashboard currently exposes department and State/UT tables. DARPG/IIT Kanpur materials document district-wise analysis in analytical systems, but a current public district grievance table is not exposed on the public dashboard.

Therefore CIVICLENS does **not** estimate district grievance metrics by splitting State/UT totals.

A future verified district snapshot must contain at least:

- state_ut
- district
- snapshot_date
- reporting_period
- received
- disposed
- pending_0_60
- pending_61_180
- pending_181_365
- pending_over_365
- pending_total
- source

Validation must enforce non-negative numeric values, unique State/UT + district pairs per snapshot, HTTPS source, and ageing-bucket reconciliation.

Once that dataset is supplied, the same architecture can expose:

- district overview
- received/disposed/pending KPIs
- disposal rate
- ageing buckets
- 181+ day workload
- district comparison
- district history
- district insights
- district CSV export
- deterministic district questions
- Gemini grounded district explanations

No district value is fabricated from a State/UT aggregate.
