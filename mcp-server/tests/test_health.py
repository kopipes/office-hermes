from fastapi.testclient import TestClient

from main import app


def test_health_unauthorized():
    client = TestClient(app)
    resp = client.get("/health")
    assert resp.status_code in (401, 500)
