from fastapi.testclient import TestClient

from onebot_ads.main import app


def test_health_route_returns_ok() -> None:
    client = TestClient(app)

    response = client.get("/api/v1/health")

    assert response.status_code == 200
    assert response.json()["status"] == "ok"
