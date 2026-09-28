# Local Runbook

## Backend
PowerShell:
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r backend/requirements.txt

Create backend/.env:
GEMINI_API_KEY=your-new-key
GEMINI_MODEL=gemini-2.5-flash

Run:
uvicorn backend.app.main:app --reload

## Frontend
Open frontend/index.html after the backend starts.

## API
GET /health
GET /api/v1/overview
GET /api/v1/states
GET /api/v1/ageing
POST /api/v1/ai/ask

Never commit .env.
