from pathlib import Path

from onebot_ads.core.config import Settings
from onebot_ads.schemas.campaigns import ContextSnippet
from onebot_ads.services.campaign_service import CampaignService


class StubKnowledgeBase:
    def retrieve(self, query: str, top_k: int = 3) -> list[ContextSnippet]:
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
