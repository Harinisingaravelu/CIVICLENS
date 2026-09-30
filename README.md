# CIVICLENS
## India Public Grievance Intelligence & Resolution Analytics

CIVICLENS is a full-stack analytics platform using verified CPGRAMS State/UT snapshots. It combines data validation, Python analytics, a SQLite snapshot registry, historical comparison, REST APIs, an interactive dashboard, grounded Gemini analysis, automated tests and container support.

### Real-data principles
- Source dataset is stored in `data/cpgrams_snapshot.csv`.
- Every row preserves the official source URL and snapshot date.
- Analytics are computed from validated data at runtime.
- Gemini is constrained to supplied dataset context; it is not a source of government facts.
- No production numbers are fabricated.
- Historical trends appear only after multiple verified snapshots are registered.

### Current snapshot
The repository contains a State/UT snapshot dated 2026-09-25, covering 01/01/2026-25/09/2026. The official CPGRAMS dashboard is the source: https://pgportal.gov.in/darpgdashboard

### Refresh the real government snapshot
The repository includes a reproducible refresh script that reads the official CPGRAMS State/UT table and validates it using the same data contract as the API.

PowerShell:
```powershell
pip install -r backend/requirements.txt
python scripts/refresh_cpgrams_snapshot.py
python analytics/analyse.py
pytest -q
```

Run the refresh whenever a new official dashboard snapshot is available. The script does not invent missing history and does not silently coerce invalid records.

### Run locally
PowerShell:
```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r backend/requirements.txt
Copy-Item backend/.env.example backend/.env
uvicorn backend.app.main:app --reload
```

Open another terminal:
```powershell
python -m http.server 5500 --directory frontend
```

Then open http://localhost:5500. The dashboard automatically uses the local API on localhost and the Render API on the hosted dashboard.

### API
- `GET /health`
- `GET /ready`
- `GET /api/v1/overview`
- `GET /api/v1/states?search=Tamil%20Nadu`
- `GET /api/v1/ageing`
- `GET /api/v1/insights`
- `GET /api/v1/data-quality`
- `GET /api/v1/snapshots`
- `GET /api/v1/history`
- `GET /api/v1/history/compare?from_date=YYYY-MM-DD&to_date=YYYY-MM-DD`
- `POST /api/v1/ai/ask`
- `GET /api/v1/export/csv`

### Controlled ingestion
Snapshot upload is available at `POST /api/v1/snapshots/ingest`, but `ENABLE_SNAPSHOT_INGESTION=false` by default. Enable it only for a controlled local/admin workflow and add authentication before any external deployment.

### Data integrity
The loader and ingestion pipeline reject missing/non-numeric values, negative measures, duplicate State/UT records, invalid HTTPS sources and ageing totals that do not reconcile. Missing values are never silently converted to zero.

### Historical intelligence
The snapshot registry stores dataset fingerprints and State/UT records. Once two verified snapshots exist, CIVICLENS calculates descriptive changes between them. It does not manufacture historical values.

### Interpretation
Disposal rate and pressure index are analytical calculations. `pressure_index` is a CIVICLENS exploratory metric, not an official government score. Snapshot observations and historical changes are descriptive and should not be treated as causal explanations or overall performance rankings.

### Docker
Copy `backend/.env.example` to `backend/.env`, add your own key if needed, then run:
```powershell
docker compose up --build
```

### Reliability and monitoring
- `GET /health` provides liveness.
- `GET /ready` checks the dataset and SQLite database.
- `GET /metrics` exposes lightweight in-process request counts and recent timing metadata.
- Docker and Compose include healthchecks.
- The container runs as a non-root user.
- Monitoring does not store request bodies, API keys or user questions.

### CPGRAMS disposal caveat
The official dashboard notes that disposals can include grievances carried forward from earlier periods. Therefore CIVICLENS does not reject a record merely because disposed exceeds current-period received; it validates non-negative values and the pending-ageing reconciliation instead.


## Geographic intelligence

CIVICLENS now includes a State/UT → District information architecture.

- State Explorer includes the current administrative district count.
- District Directory is sourced from the Government of India Local Government Directory (LGD).
- District coverage and directory export APIs are available.
- District grievance metrics are **not fabricated** from State/UT aggregates.
- A verified district CPGRAMS snapshot can later activate district received/disposed/pending, ageing, history, comparison, export and grounded AI features through the documented district data contract.

The public CPGRAMS dashboard currently exposes department and State/UT tables, while DARPG/IIT Kanpur materials document district-wise analysis in analytical dashboards. CIVICLENS keeps the public-data layer and the district-directory layer separate so every displayed metric remains traceable.
