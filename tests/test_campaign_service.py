from pathlib import Path

from fastapi.testclient import TestClient

from onebot_ads.api.dependencies import get_campaign_service
from onebot_ads.core.config import Settings
from onebot_ads.main import app
from onebot_ads.schemas.campaigns import (
    AssistantResponse,
    CampaignBrief,
    ContextSnippet,
    OrchestrationPlan,
)
from onebot_ads.services.campaign_service import CampaignService


class StubKnowledgeBase:
    def retrieve(self, query: str, top_k: int = 3, scope=None) -> list[ContextSnippet]:
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
        def retrieve(self, query: str, top_k: int = 3, scope=None) -> list[ContextSnippet]:
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

    assert (
        "Draft context query returned no snippets; fallback copy used only the brief."
        in result.warnings
    )


def test_campaign_service_reports_specific_live_llm_fallback_reason_once(monkeypatch) -> None:
    settings = Settings(enable_live_llm=True, enable_rag=True)
    service = CampaignService(settings, knowledge_base=StubKnowledgeBase())

    def fail_live_copy(*args, **kwargs):
        raise ValueError("Model response did not contain a JSON object.")

    monkeypatch.setattr(service.campaign_agent.creative_agent, "_generate_with_llm", fail_live_copy)

    result = service.draft_campaign(
        CampaignBrief(
            product_name="OneBot Ads",
            audience="SME marketing teams",
            goal="Increase qualified leads",
            channels=["linkedin"],
        )
    )

    assert (
        "Live LLM creative generation failed; deterministic fallback returned: "
        "ValueError: Model response did not contain a JSON object."
    ) in result.warnings
    assert not any("unavailable or not provisioned" in warning for warning in result.warnings)


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
                "notes": [
                    "No fallback provider is configured in the simplified "
                    "local-first setup."
                ],
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


def test_assistant_route_uses_uploaded_campaign_csv_for_analysis() -> None:
    settings = Settings(enable_live_llm=False, enable_rag=True)
    service = CampaignService(settings, knowledge_base=StubKnowledgeBase())
    app.dependency_overrides[get_campaign_service] = lambda: service
    client = TestClient(app)

    try:
        response = client.post(
            "/api/v1/assistant/run",
            json={
                "message": "Analyze these campaigns and recommend optimizations.",
                "campaign_csv_content": "\n".join(
                    [
                        "campaign_id,platform,audience,impressions,clicks,spend,conversions,revenue",
                        "CAMP100,LinkedIn,SMEs,1000,50,200,5,800",
                        "CAMP200,Instagram,Founders,1500,45,180,3,360",
                    ]
                ),
                "campaign_csv_filename": "uploaded_campaigns.csv",
            },
        )
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 200
    payload = response.json()
    assert payload["analysis"]["raw_data_path"] == "uploaded_campaigns.csv"
    assert payload["analysis"]["best_campaign"] == "CAMP100"
    assert (
        "Increase budget on CAMP100 by 15-20%"
        in payload["optimization"]["quick_wins"][0]["recommendation"]
    )
    assert "LinkedIn" in payload["optimization"]["quick_wins"][0]["reason"]


def test_campaign_service_passes_min_answer_words_to_orchestrator(monkeypatch) -> None:
    settings = Settings(enable_live_llm=False, enable_rag=True)
    service = CampaignService(settings, knowledge_base=StubKnowledgeBase())
    captured: dict[str, object] = {}

    def fake_run(user_message: str, **kwargs) -> AssistantResponse:
        captured["user_message"] = user_message
        captured.update(kwargs)
        return AssistantResponse(
            intent="brand_advice",
            plan=OrchestrationPlan(
                intent="brand_advice",
                agents_to_call=["rag_agent"],
                final_format="grounded_brand_guidance",
            ),
        )

    monkeypatch.setattr(service.orchestrator_agent, "run", fake_run)

    service.handle_request(
        "Give me a detailed answer about positioning.",
        company_name="HubSpot",
        company_website="https://www.hubspot.com",
        use_web_search=True,
        min_answer_words=800,
    )

    assert captured["user_message"] == "Give me a detailed answer about positioning."
    assert captured["company_name"] == "HubSpot"
    assert captured["company_website"] == "https://www.hubspot.com"
    assert captured["use_web_search"] is True
    assert captured["min_answer_words"] == 800
