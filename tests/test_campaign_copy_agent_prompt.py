from onebot_ads.agents.campaign_copy_agent import CampaignCopyAgent
from onebot_ads.core.config import Settings
from onebot_ads.schemas.campaigns import CampaignBrief


class EmptyKnowledgeBase:
    def retrieve(self, query: str, top_k: int = 3, scope=None) -> list:
        return []

    def reindex(self):
        raise NotImplementedError


def test_live_llm_prompt_template_formats_without_invalid_braces(monkeypatch) -> None:
    settings = Settings(enable_live_llm=True, enable_rag=False)
    agent = CampaignCopyAgent(settings, EmptyKnowledgeBase())

    class FakeResponse:
        content = (
            '{"summary":"ok summary","variants":[{"channel":"linkedin","headline":"H",'
            '"primary_text":"P","cta":"C","rationale":"R"}],"image_prompt":null}'
        )

    class FakeChatOllama:
        def __init__(self, *args, **kwargs) -> None:
            pass

        def invoke(self, messages):
            return FakeResponse()

    monkeypatch.setattr(
        "langchain_ollama.ChatOllama",
        FakeChatOllama,
    )

    result = agent.draft(
        CampaignBrief(
            product_name="Agentic OneBotAds",
            audience="SME marketing teams",
            goal="Increase qualified leads",
            channels=["linkedin"],
        )
    )

    assert result.mode == "live_llm"
    assert result.provider == "ollama"
