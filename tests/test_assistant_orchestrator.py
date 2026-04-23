from pathlib import Path

from onebot_ads.core.config import Settings
from onebot_ads.schemas.campaigns import ContextSnippet
from onebot_ads.services.campaign_service import CampaignService


class StubKnowledgeBase:
    def retrieve(self, query: str, top_k: int = 3, scope=None) -> list[ContextSnippet]:
        return [
            ContextSnippet(
                source="brand_guidelines.md",
                excerpt="Use a professional, modern, helpful, and direct tone.",
                score=0.95,
            ),
            ContextSnippet(
                source="marketing_strategy.md",
                excerpt="Position the product as an AI-powered advertising co-pilot.",
                score=0.92,
            ),
        ]

    def reindex(self):
        raise NotImplementedError


def test_assistant_publication_flow_returns_ready_package() -> None:
    settings = Settings(enable_live_llm=False, enable_rag=True, enable_image_generation=False)
    service = CampaignService(settings, knowledge_base=StubKnowledgeBase())

    result = service.handle_request(
        "Create a LinkedIn publication with image for Agentic OneBotAds targeting SMEs."
    )

    assert result.intent == "generate_publication"
    assert result.publication is not None
    assert result.publication.platform == "LinkedIn"
    assert result.publication.status == "ready_for_review"
    assert result.compliance is not None
    assert result.compliance.approved is True
    assert result.image is not None
    assert "Brand guidance:" in result.image.image_prompt
    assert "CTA such as" in result.image.image_prompt


def test_assistant_full_workflow_can_save_output_bundle(tmp_path: Path) -> None:
    settings = Settings(
        enable_live_llm=False,
        enable_rag=True,
        enable_image_generation=False,
        outputs_directory=tmp_path,
        output_post_dir=tmp_path / "posts",
        output_report_dir=tmp_path / "reports",
        output_image_dir=tmp_path / "images",
    )
    service = CampaignService(settings, knowledge_base=StubKnowledgeBase())

    result = service.handle_request(
        (
            "Create a LinkedIn publication with image and a report for "
            "Agentic OneBotAds targeting SMEs."
        ),
        run_all_agents=True,
        save_output=True,
        export_report=True,
    )

    assert result.intent == "full_workflow"
    assert result.publication is not None
    assert result.report is not None
    assert result.saved_output_path is not None
    assert Path(result.saved_output_path).exists()
    assert result.report.report_path is not None
    assert Path(result.report.report_path).exists()
    assert result.saved_output_path in result.artifact_paths


def test_assistant_image_prompt_language_triggers_real_image_generation(
    monkeypatch,
) -> None:
    settings = Settings(enable_live_llm=False, enable_rag=True, enable_image_generation=True)
    service = CampaignService(settings, knowledge_base=StubKnowledgeBase())

    captured: dict[str, object] = {}

    def fake_image_run(**kwargs):
        captured.update(kwargs)
        from onebot_ads.schemas.campaigns import ImageGenerationResponse

        return ImageGenerationResponse(
            image_prompt="Prompt",
            negative_prompt="Negative",
            alt_text="Alt",
            provider="qwen_image",
            image_path="outputs/images/test.png",
            image_url="/outputs/images/test.png",
            status="generated",
            notes=[],
            fallback_used=False,
            fallback_attempted=False,
            fallback_succeeded=False,
        )

    monkeypatch.setattr(service.orchestrator_agent.image_agent, "run", fake_image_run)

    result = service.handle_request(
        "Create an image prompt for Agentic OneBotAds. Generate the image if the stack allows it."
    )

    assert result.image is not None
    assert result.image.status == "generated"
    assert captured["request_image_generation"] is True
