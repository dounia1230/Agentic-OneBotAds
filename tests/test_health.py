import logging

from fastapi.testclient import TestClient

from onebot_ads.api.dependencies import get_campaign_service
from onebot_ads.core.config import Settings
from onebot_ads.main import app
from onebot_ads.services.campaign_service import CampaignService


class _StubKnowledgeBase:
    def retrieve(self, query: str, top_k: int = 3, scope=None):
        return []

    def reindex(self):
        raise NotImplementedError


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
    settings = Settings(
        image_provider="qwen_image",
        enable_image_generation=True,
    )
    service = CampaignService(settings, knowledge_base=_StubKnowledgeBase())
    app.dependency_overrides[get_campaign_service] = lambda: service
    client = TestClient(app)

    try:
        response = client.get("/api/v1/runtime")
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 200
    payload = response.json()
    assert payload["image_provider"] == "qwen_image"
    assert payload["image_model"] == "Qwen/Qwen-Image-2512"
    assert payload["knowledge_base_directory"] == "data/knowledge_base"
    assert payload["outputs_directory"] == "outputs"
