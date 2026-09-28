from fastapi.testclient import TestClient
from backend.app.main import app

client = TestClient(app)

def test_health():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"

def test_readiness():
    response = client.get("/ready")
    assert response.status_code == 200
    assert response.json()["status"] == "ready"

def test_overview():
    response = client.get("/api/v1/overview")
    assert response.status_code == 200
    body = response.json()
    assert body["states_ut_count"] > 0
    assert body["received"] >= body["disposed"]

def test_state_search():
    response = client.get("/api/v1/states", params={"search": "Tamil Nadu"})
    assert response.status_code == 200
    rows = response.json()
    assert any(row["state_ut"] == "Tamil Nadu" for row in rows)

def test_ageing():
    response = client.get("/api/v1/ageing")
    assert response.status_code == 200
    assert set(response.json()) == {"0_60","61_180","181_365","365_plus"}

def test_snapshots():
    response = client.get("/api/v1/snapshots")
    assert response.status_code == 200
    rows = response.json()
    assert len(rows) >= 1
    assert rows[0]["record_count"] > 0

def test_export_csv():
    response = client.get("/api/v1/export/csv")
    assert response.status_code == 200
    assert "text/csv" in response.headers["content-type"]
    assert "state_ut" in response.text
