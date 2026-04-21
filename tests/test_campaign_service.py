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
