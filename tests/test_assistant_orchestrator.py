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
