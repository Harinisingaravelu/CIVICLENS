# Historical AI Intelligence

CIVICLENS now includes a deterministic historical grounding helper in `backend/app/historical_ai.py`.

The helper reads only verified snapshots from the SQLite snapshot registry.

Supported intent:
- historical comparison across the latest two verified snapshots
- State/UT historical timeline when a supported State/UT is named

If fewer than two verified snapshots exist, the helper returns an explicit unavailable result. It never creates or interpolates historical values.

Gemini should receive this deterministic result as context before generating natural-language explanations. Historical observations are descriptive changes, not causal findings or performance rankings.
