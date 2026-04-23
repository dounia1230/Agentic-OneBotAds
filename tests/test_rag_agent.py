from onebot_ads.agents.rag_agent import RAGMarketingKnowledgeAgent
from onebot_ads.core.config import Settings
from onebot_ads.schemas.campaigns import ContextSnippet


class StubKnowledgeBase:
    def retrieve(self, query: str, top_k: int = 4, scope=None) -> list[ContextSnippet]:
        return [
            ContextSnippet(
                source="brand_guidelines.md",
                excerpt="Use a professional, modern, and direct tone in customer-facing copy.",
                score=0.94,
            ),
            ContextSnippet(
                source="audience_personas.md",
                excerpt="Primary buyers are time-constrained marketing managers at smaller teams.",
                score=0.89,
            ),
        ]


def test_rag_agent_fallback_answer_omits_source_mentions() -> None:
    settings = Settings(enable_live_llm=False, enable_rag=True)
    agent = RAGMarketingKnowledgeAgent(settings, StubKnowledgeBase())

    result = agent.run("What tone should I use for the brand?")

    assert "brand_guidelines.md" not in result.answer
    assert "audience_personas.md" not in result.answer
    assert "Sources:" not in result.answer
    assert result.source_documents == ["brand_guidelines.md", "audience_personas.md"]


def test_rag_agent_sanitizes_llm_style_source_blocks() -> None:
    answer = (
        "Use a direct and professional tone.\n"
        "Sources:\n"
        "- brand_guidelines.md\n"
        "- audience_personas.md"
    )

    sanitized = RAGMarketingKnowledgeAgent._sanitize_answer_text(answer)

    assert sanitized == "Use a direct and professional tone."
