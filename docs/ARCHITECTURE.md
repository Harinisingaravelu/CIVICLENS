# CIVICLENS Architecture

## Layers
1. Source — official CPGRAMS dashboard snapshot.
2. Data — CSV snapshot with provenance.
3. Analytics — Pandas calculations and validation.
4. API — FastAPI REST layer.
5. Experience — web dashboard.
6. AI — Gemini grounded analytics copilot.
7. BI — Power BI-ready dataset.
8. Quality — automated data tests and CI.

## AI request flow
Dashboard question → FastAPI → analytics context → Gemini → grounded answer → source period shown to user.

## Security
Secrets are environment variables. No API key is committed to GitHub. Frontend never receives the Gemini secret.
