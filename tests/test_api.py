from fastapi.testclient import TestClient
from backend.app.main import app

client=TestClient(app)

def test_health():
    r=client.get("/health"); assert r.status_code==200; assert r.json()["status"]=="ok"

def test_readiness():
    r=client.get("/ready"); assert r.status_code==200; assert r.json()["status"]=="ready"

def test_overview():
    r=client.get("/api/v1/overview"); assert r.status_code==200; assert r.json()["states_ut_count"]>0

def test_state_search():
    r=client.get("/api/v1/states",params={"search":"Tamil Nadu"}); assert r.status_code==200; assert any(x["state_ut"]=="Tamil Nadu" for x in r.json())

def test_ageing():
    r=client.get("/api/v1/ageing"); assert r.status_code==200; assert set(r.json())=={"0_60","61_180","181_365","365_plus"}

def test_snapshots():
    r=client.get("/api/v1/snapshots"); assert r.status_code==200; assert r.json()[0]["record_count"]>0

def test_history_requires_two_verified_snapshots():
    r=client.get("/api/v1/history")
    assert r.status_code==200
    body=r.json()
    assert body["snapshots"]
    assert body["latest_comparison"]["status"] in {"ok","unavailable"}
    if len(body["snapshots"]) < 2:
        assert body["latest_comparison"]["status"]=="unavailable"

def test_history_invalid_date_order():
    r=client.get("/api/v1/history/compare",params={"from_date":"2026-09-25","to_date":"2026-09-25"})
    assert r.status_code==400

def test_export_csv():
    r=client.get("/api/v1/export/csv"); assert r.status_code==200; assert "state_ut" in r.text

def test_ai_suggestions():
    r=client.get("/api/v1/ai/suggestions"); assert r.status_code==200; assert len(r.json()["suggestions"])>=3

def test_deterministic_query_without_gemini(monkeypatch):
    from backend.app import ai_routes
    monkeypatch.setattr(ai_routes,"ask_gemini",lambda question,context: context)
    r=client.post("/api/v1/ai/ask",json={"question":"What is the pending workload in Tamil Nadu?"})
    body=r.json(); assert r.status_code==200; assert body["intent"]=="state_metric"; assert body["answer_data"]["state_ut"]=="Tamil Nadu"; assert body["grounding"]=="deterministic_dataset"

def test_deterministic_ageing_query(monkeypatch):
    from backend.app import ai_routes
    monkeypatch.setattr(ai_routes,"ask_gemini",lambda question,context: context)
    r=client.post("/api/v1/ai/ask",json={"question":"Which ageing bucket is largest?"})
    assert r.status_code==200; assert r.json()["intent"]=="largest_ageing_bucket"

def test_metrics():
    client.get("/health")
    r=client.get("/metrics")
    assert r.status_code==200
    body=r.json()
    assert body["requests_total"]>=1
    assert isinstance(body["routes"],dict)

def test_readiness_has_database_check():
    r=client.get("/ready")
    assert r.status_code==200
    assert r.json()["checks"]["dataset"] is True
    assert r.json()["checks"]["database"] is True

def test_ingestion_is_disabled_by_default():
    r=client.post("/api/v1/snapshots/ingest",files={"file":("snapshot.csv",b"state_ut,snapshot_date\nTamil Nadu,2026-01-01","text/csv")})
    assert r.status_code==403


def test_historical_ai_endpoint():
    r=client.post("/api/v1/ai/historical",params={"question":"What changed since the previous verified snapshot?"})
    assert r.status_code==200
    assert r.json()["intent"] in {"historical_comparison","historical_comparison_unavailable"}

def test_historical_state_endpoint():
    r=client.post("/api/v1/ai/historical",params={"question":"Show Tamil Nadu historical changes."})
    assert r.status_code==200
    assert r.json()["intent"] in {"historical_state_change","historical_state_unavailable"}

