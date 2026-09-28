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
The repository contains a State/UT snapshot dated 2026-09-25, covering 01/01/2026-25/09/2026. Official source: https://pgportal.gov.in/darpgdashboard

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

Then open http://localhost:5500

### API
- `GET /health`
- `GET /ready`
- `GET /api/v1/overview`
- `GET /api/v1/states?search=Tamil%20Nadu`
- `GET /api/v1/ageing`
- `GET /api/v1/insights`
- `GET /api/v1/snapshots`
- `GET /api/v1/history`
- `GET /api/v1/history/compare?from_date=YYYY-MM-DD&to_date=YYYY-MM-DD`
- `POST /api/v1/ai/ask`
- `GET /api/v1/export/csv`

### Controlled ingestion
Snapshot upload is available at `POST /api/v1/snapshots/ingest`, but `ENABLE_SNAPSHOT_INGESTION=false` by default. Enable it only for a controlled local/admin workflow and add authentication before any external deployment.

### Data integrity
The loader and ingestion pipeline reject missing/non-numeric values, negative measures, duplicate State/UT records, disposed values above received values, invalid HTTPS sources and ageing totals that do not reconcile. Missing values are never silently converted to zero.

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
