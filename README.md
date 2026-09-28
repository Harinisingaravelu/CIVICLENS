# CIVICLENS
## India Public Grievance Intelligence & Resolution Analytics

CIVICLENS is a full-stack analytics platform using a verified CPGRAMS State/UT snapshot. It combines data validation, Python analytics, REST APIs, an interactive dashboard, grounded Gemini analysis, automated tests and container support.

### Real-data principles
- Source dataset is stored in data/cpgrams_snapshot.csv.
- Every row preserves the official source URL and snapshot date.
- Analytics are computed from that dataset at runtime.
- Gemini is constrained to supplied dataset context; it is not a source of government facts.
- No production numbers are fabricated.

### Current snapshot
The repository contains a State/UT snapshot dated 2026-09-25, covering 01/01/2026-25/09/2026. Official source: https://pgportal.gov.in/darpgdashboard

### Run locally
PowerShell: python -m venv .venv; .\\.venv\\Scripts\\Activate.ps1; pip install -r backend/requirements.txt; Copy-Item backend/.env.example backend/.env; uvicorn backend.app.main:app --reload

Open another terminal: python -m http.server 5500 --directory frontend
Then open http://localhost:5500

### API
GET /health
GET /api/v1/overview
GET /api/v1/states?search=Tamil%20Nadu
GET /api/v1/ageing
GET /api/v1/insights
POST /api/v1/ai/ask

### Data integrity
The loader rejects missing/non-numeric values, negative measures and ageing totals that do not reconcile. Missing values are never silently converted to zero.

### Interpretation
Disposal rate and pressure index are analytical calculations. pressure_index is a CIVICLENS exploratory metric, not an official government score. Snapshot observations are descriptive and should not be treated as causal explanations or overall performance rankings.

### Docker
Copy backend/.env.example to backend/.env, add your own key, then run: docker compose up --build
