from fastapi.testclient import TestClient
from backend.app.main import app

import pytest

@pytest.fixture(scope="module")
def client():
    with TestClient(app) as test_client:
        yield test_client

def test_health(client):
    r=client.get("/health"); assert r.status_code==200; assert r.json()["status"]=="ok"

def test_readiness(client):
    r=client.get("/ready"); assert r.status_code==200; assert r.json()["status"]=="ready"

def test_overview(client):
    r=client.get("/api/v1/overview"); assert r.status_code==200; assert r.json()["states_ut_count"]>0

def test_state_search(client):
    r=client.get("/api/v1/states",params={"search":"Tamil Nadu"}); assert r.status_code==200; assert any(x["state_ut"]=="Tamil Nadu" for x in r.json())

def test_ageing(client):
    r=client.get("/api/v1/ageing"); assert r.status_code==200; assert set(r.json())=={"0_60","61_180","181_365","365_plus"}

def test_snapshots(client):
    r=client.get("/api/v1/snapshots"); assert r.status_code==200; assert r.json()[0]["record_count"]>0

def test_history_requires_two_verified_snapshots(client):
    r=client.get("/api/v1/history")
    assert r.status_code==200
    body=r.json()
    assert body["snapshots"]
    assert body["latest_comparison"]["status"] in {"ok","unavailable"}
    if len(body["snapshots"]) < 2:
        assert body["latest_comparison"]["status"]=="unavailable"

def test_history_invalid_date_order(client):
    r=client.get("/api/v1/history/compare",params={"from_date":"2026-09-25","to_date":"2026-09-25"})
    assert r.status_code==400

def test_export_csv(client):
    r=client.get("/api/v1/export/csv"); assert r.status_code==200; assert "state_ut" in r.text

def test_ai_suggestions(client):
    r=client.get("/api/v1/ai/suggestions"); assert r.status_code==200; assert len(r.json()["suggestions"])>=3

def test_deterministic_query_without_gemini(client, monkeypatch):
    from backend.app import ai_routes
    monkeypatch.setattr(ai_routes,"ask_gemini",lambda question,context: context)
    r=client.post("/api/v1/ai/ask",json={"question":"What is the pending workload in Tamil Nadu?"})
    body=r.json(); assert r.status_code==200; assert body["intent"]=="state_metric"; assert body["answer_data"]["state_ut"]=="Tamil Nadu"; assert body["grounding"]=="deterministic_dataset"

def test_deterministic_ageing_query(client, monkeypatch):
    from backend.app import ai_routes
    monkeypatch.setattr(ai_routes,"ask_gemini",lambda question,context: context)
    r=client.post("/api/v1/ai/ask",json={"question":"Which ageing bucket is largest?"})
    assert r.status_code==200; assert r.json()["intent"]=="largest_ageing_bucket"

def test_metrics(client):
    client.get("/health")
    r=client.get("/metrics")
    assert r.status_code==200
    body=r.json()
    assert body["requests_total"]>=1
    assert isinstance(body["routes"],dict)

def test_readiness_has_database_check(client):
    r=client.get("/ready")
    assert r.status_code==200
    assert r.json()["checks"]["dataset"] is True
    assert r.json()["checks"]["database"] is True

def test_ingestion_is_disabled_by_default(client):
    r=client.post("/api/v1/snapshots/ingest",files={"file":("snapshot.csv",b"state_ut,snapshot_date\nTamil Nadu,2026-01-01","text/csv")})
    assert r.status_code==403


def test_historical_ai_endpoint(client):
    r=client.post("/api/v1/ai/historical",params={"question":"What changed since the previous verified snapshot?"})
    assert r.status_code==200
    assert r.json()["intent"] in {"historical_comparison","historical_comparison_unavailable"}

def test_main_ai_uses_historical_grounding(client, monkeypatch):
    from backend.app import ai_routes
    monkeypatch.setattr(ai_routes,"ask_gemini",lambda question,context: context)
    r=client.post("/api/v1/ai/ask",json={"question":"What changed since the previous verified snapshot?"})
    assert r.status_code==200
    assert r.json()["grounding"]=="verified_snapshot_history"

def test_historical_state_endpoint(client):
    r=client.post("/api/v1/ai/historical",params={"question":"Show Tamil Nadu historical changes."})
    assert r.status_code==200
    assert r.json()["intent"] in {"historical_state_change","historical_state_unavailable"}
def test_invalid_state_limit_is_rejected(client):
    r=client.get("/api/v1/states",params={"limit":0})
    assert r.status_code==422

def test_invalid_history_date_format_is_rejected(client):
    r=client.get("/api/v1/history/compare",params={"from_date":"bad","to_date":"2026-09-25"})
    assert r.status_code==422

def test_ai_question_length_is_validated(client):
    r=client.post("/api/v1/ai/ask",json={"question":"x"})
    assert r.status_code==422
def test_ingestion_rejects_malformed_csv_when_enabled(client, monkeypatch):
    monkeypatch.setenv("ENABLE_SNAPSHOT_INGESTION", "true")
    r=client.post("/api/v1/snapshots/ingest",files={"file":("snapshot.csv",b"not,a,valid,dataset\n1,2,3,4","text/csv")})
    assert r.status_code==400

def test_ingestion_rejects_oversized_upload_when_enabled(client, monkeypatch):
    monkeypatch.setenv("ENABLE_SNAPSHOT_INGESTION", "true")
    oversized=b"x"*(5*1024*1024+1)
    r=client.post("/api/v1/snapshots/ingest",files={"file":("snapshot.csv",oversized,"text/csv")})
    assert r.status_code==400

def test_ingestion_accepts_valid_snapshot_when_enabled(client, monkeypatch):
    monkeypatch.setenv("ENABLE_SNAPSHOT_INGESTION", "true")
    csv = """state_ut,snapshot_date,reporting_period,received,disposed,pending_0_60,pending_61_180,pending_181_365,pending_over_365,pending_total,source
API Test State,2099-01-01,01/01/2099-01/01/2099,10,12,1,1,1,1,4,https://example.gov.in/data
"""
    r=client.post("/api/v1/snapshots/ingest",files={"file":("snapshot.csv",csv,"text/csv")})
    assert r.status_code==200
    body=r.json()
    assert body["validation"]["status"]=="passed"
    assert body["validation"]["record_count"]==1
def test_unknown_state_history_returns_not_found(client):
    r=client.get("/api/v1/history/state/Definitely%20Not%20A%20State")
    assert r.status_code==404
def test_metrics_normalize_dynamic_state_history_path(client):
    client.get("/api/v1/history/state/Tamil%20Nadu")
    r=client.get("/metrics")
    assert r.status_code==200
    assert "GET /api/v1/history/state/{state_ut}" in r.json()["routes"]
def test_ingestion_unexpected_error_is_sanitized(client, monkeypatch):
    monkeypatch.setenv("ENABLE_SNAPSHOT_INGESTION", "true")
    from backend.app import main
    monkeypatch.setattr(main, "ingest_csv_bytes", lambda content: (_ for _ in ()).throw(RuntimeError("secret internal detail")))
    r=client.post("/api/v1/snapshots/ingest",files={"file":("snapshot.csv",b"state_ut", "text/csv")})
    assert r.status_code==500
    assert r.json()["detail"]=="Snapshot ingestion failed unexpectedly. Check server logs for details."
    assert "secret internal detail" not in r.text

def test_ai_question_rejects_whitespace_only(client):
    r=client.post("/api/v1/ai/ask",json={"question":"   "})
    assert r.status_code==422


def test_state_search_treats_special_characters_as_literal(client):
    r = client.get("/api/v1/states", params={"search": "["})
    assert r.status_code == 200
    assert r.json() == []
