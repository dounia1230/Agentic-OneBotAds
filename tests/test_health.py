import logging

from fastapi.testclient import TestClient

from onebot_ads.main import app


def test_health_route_returns_ok() -> None:
    client = TestClient(app)

    response = client.get("/api/v1/health")

    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_request_logging_emits_path_and_status(caplog) -> None:
    client = TestClient(app)

    with caplog.at_level(logging.INFO, logger="uvicorn.error"):
        response = client.get("/api/v1/runtime")

    assert response.status_code == 200
    assert "GET /api/v1/runtime -> 200" in caplog.text


def test_runtime_route_exposes_normalized_runtime_summary() -> None:
    client = TestClient(app)

    response = client.get("/api/v1/runtime")

    assert response.status_code == 200
    payload = response.json()
    assert payload["image_provider"] == "qwen_image"
    assert payload["image_model"] == "Qwen/Qwen-Image-2512"
    assert payload["knowledge_base_directory"] == "data/knowledge_base"
    assert payload["outputs_directory"] == "outputs"
