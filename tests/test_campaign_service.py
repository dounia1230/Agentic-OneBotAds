from pathlib import Path

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


def test_campaign_service_draft_supports_pollinations_and_composition(
    monkeypatch,
    tmp_path: Path,
) -> None:
    settings = Settings(
        enable_live_llm=False,
        enable_rag=True,
        enable_image_generation=True,
        image_provider="pollinations",
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
                "provider": "pollinations",
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
            image_provider="pollinations",
        )
    )

    assert result.image_prompt is not None
    assert result.image_prompt.provider == "pollinations"
    assert result.image_prompt.publication_image_path == str(publication_path)
    assert result.image_prompt.image_path == str(publication_path)


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
