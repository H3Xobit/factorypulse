from fastapi.testclient import TestClient

from factorypulse.api.main import app


def test_meta_lists_fault_types():
    client = TestClient(app)
    res = client.get("/meta")
    assert res.status_code == 200
    data = res.json()
    assert data["service"] == "factorypulse-api"
    assert "bearing_degradation" in data["fault_types"]
