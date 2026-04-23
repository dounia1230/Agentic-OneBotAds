from pathlib import Path

from fastapi.testclient import TestClient

from onebot_ads.api.dependencies import get_campaign_service
from onebot_ads.main import app
from onebot_ads.core.config import Settings
from onebot_ads.schemas.campaigns import CampaignBrief, ContextSnippet
from onebot_ads.services.campaign_service import CampaignService


class StubKnowledgeBase:
    def retrieve(self, query: str, top_k: int = 3) -> list[ContextSnippet]:
        return [
            ContextSnippet(
                source="example_brand_playbook.md",
                excerpt="Use direct, credible, efficient language and avoid hype.",
                score=0.93,
            )
        ]

    def reindex(self):
        raise NotImplementedError


def test_campaign_service_fallback_returns_variants() -> None:
    settings = Settings(enable_live_llm=False, enable_rag=True)
    service = CampaignService(settings, knowledge_base=StubKnowledgeBase())

    result = service.draft_campaign(
        CampaignBrief(
            product_name="OneBot Ads",
            audience="SME marketing teams",
            goal="Increase qualified leads",
            channels=["meta", "linkedin"],
            offer="7-day pilot",
            key_points=["faster launches", "brand-safe drafts"],
        )
    )

    assert result.mode == "fallback"
    assert len(result.variants) == 2
    assert result.used_context[0].source == "example_brand_playbook.md"


def test_campaign_service_draft_supports_qwen_image_and_composition(
    monkeypatch,
    tmp_path: Path,
) -> None:
    settings = Settings(
        enable_live_llm=False,
        enable_rag=True,
        enable_image_generation=True,
        image_provider="qwen_image",
        output_image_dir=tmp_path,
    )
    service = CampaignService(settings, knowledge_base=StubKnowledgeBase())

    background_path = tmp_path / "background.png"
    background_path.write_bytes(b"background")
    publication_path = tmp_path / "publication.png"
    publication_path.write_bytes(b"publication")

    class BackgroundToolStub:
        @staticmethod
        def invoke(payload):
            return {
                "status": "generated",
                "provider": "qwen_image",
                "backend": "huggingface_space",
                "space_id": "Qwen/Qwen-Image-2512",
                "background_image_path": str(background_path),
                "image_path": str(background_path),
                "prompt": payload["prompt"],
                "error": None,
            }

    monkeypatch.setattr(
        "onebot_ads.agents.campaign_copy_agent.generate_background_image",
        BackgroundToolStub(),
    )
    monkeypatch.setattr(
        "onebot_ads.agents.campaign_copy_agent.compose_publication_image",
        lambda **kwargs: {"status": "composed", "image_path": str(publication_path)},
    )

    result = service.draft_campaign(
        CampaignBrief(
            product_name="OneBot Ads",
            audience="SME marketing teams",
            goal="Increase qualified leads",
            channels=["meta", "linkedin"],
            offer="7-day pilot",
            key_points=["faster launches", "brand-safe drafts"],
            brand_constraints=["avoid hype", "no guaranteed outcomes"],
            source_context_query="OneBot Ads positioning",
            generate_image_prompt=True,
            generate_image=True,
            compose_publication_image=True,
            image_provider="qwen_image",
        )
    )

    assert result.image_prompt is not None
    assert result.image_prompt.provider == "qwen_image"
    assert result.image_prompt.backend == "huggingface_space"
    assert result.image_prompt.space_id == "Qwen/Qwen-Image-2512"
    assert result.image_prompt.publication_image_path == str(publication_path)
    assert result.image_prompt.image_path == str(publication_path)


def test_campaign_service_prompt_only_does_not_call_image_generation(monkeypatch) -> None:
    settings = Settings(enable_live_llm=False, enable_rag=True, enable_image_generation=True)
    service = CampaignService(settings, knowledge_base=StubKnowledgeBase())

    class BackgroundToolStub:
        @staticmethod
        def invoke(payload):
            raise AssertionError("Image generation should not be called for prompt-only drafts.")

    monkeypatch.setattr(
        "onebot_ads.agents.campaign_copy_agent.generate_background_image",
        BackgroundToolStub(),
    )

    result = service.draft_campaign(
        CampaignBrief(
            product_name="OneBot Ads",
            audience="SME marketing teams",
            goal="Increase qualified leads",
            channels=["meta", "linkedin"],
            generate_image_prompt=True,
            generate_image=False,
            compose_publication_image=False,
        )
    )

    assert result.image_prompt is not None
    assert result.image_prompt.status == "prompt_ready"
    assert result.image_prompt.image_path is None


def test_campaign_service_draft_warns_when_rag_query_returns_no_context() -> None:
    class EmptyKnowledgeBase:
        def retrieve(self, query: str, top_k: int = 3) -> list[ContextSnippet]:
            return []

        def reindex(self):
            raise NotImplementedError

    settings = Settings(enable_live_llm=False, enable_rag=True)
    service = CampaignService(settings, knowledge_base=EmptyKnowledgeBase())

    result = service.draft_campaign(
        CampaignBrief(
            product_name="OneBot Ads",
            audience="SME marketing teams",
            goal="Increase qualified leads",
            channels=["linkedin"],
            source_context_query="OneBot Ads tone",
        )
    )

    assert "RAG context was requested but no context was retrieved." in result.warnings


def test_runtime_summary_normalizes_paths_and_exposes_image_runtime(
    tmp_path: Path,
) -> None:
    settings = Settings(
        enable_live_llm=False,
        enable_rag=True,
        enable_image_generation=True,
        image_provider="qwen_image",
        knowledge_base_path=Path("data/knowledge_base"),
        outputs_directory=tmp_path,
    )
    service = CampaignService(settings, knowledge_base=StubKnowledgeBase())

    result = service.runtime_summary()

    assert result.image_generation_enabled is True
    assert result.image_provider == "qwen_image"
    assert result.image_model == "Qwen/Qwen-Image-2512"
    assert result.knowledge_base_directory == "data/knowledge_base"
    assert result.outputs_directory == tmp_path.as_posix()


def test_campaign_draft_route_returns_200_when_image_generation_fails(
    monkeypatch,
    tmp_path: Path,
) -> None:
    settings = Settings(
        enable_live_llm=False,
        enable_rag=True,
        enable_image_generation=True,
        output_image_dir=tmp_path,
    )
    service = CampaignService(settings, knowledge_base=StubKnowledgeBase())

    class BackgroundToolStub:
        @staticmethod
        def invoke(payload):
            return {
                "status": "generation_failed",
                "provider": "qwen_image",
                "backend": "huggingface_space",
                "space_id": "Qwen/Qwen-Image-2512",
                "background_image_path": None,
                "image_path": None,
                "prompt": payload["prompt"],
                "error": "qwen_image failed: rate limit",
                "notes": ["No fallback provider is configured in the simplified local-first setup."],
                "fallback_used": False,
                "primary_provider": "qwen_image",
                "fallback_provider": None,
            }

    monkeypatch.setattr(
        "onebot_ads.agents.campaign_copy_agent.generate_background_image",
        BackgroundToolStub(),
    )
    app.dependency_overrides[get_campaign_service] = lambda: service
    client = TestClient(app)

    try:
        response = client.post(
            "/api/v1/campaigns/draft",
            json={
                "product_name": "OneBot Ads",
                "audience": "small business owners who run Facebook ads",
                "goal": "increase signups",
                "channels": ["facebook", "instagram"],
                "generate_image_prompt": True,
                "generate_image": True,
                "compose_publication_image": False,
            },
        )
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 200
    payload = response.json()
    assert payload["image_prompt"]["status"] == "generation_failed"
    assert payload["image_prompt"]["fallback_used"] is False
    assert "qwen_image failed: rate limit" in payload["image_prompt"]["error"]
