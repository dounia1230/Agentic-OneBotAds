from onebot_ads.agents.rag_agent import RAGMarketingKnowledgeAgent
from onebot_ads.core.config import Settings
from onebot_ads.schemas.campaigns import ContextSnippet, RAGAgentResponse


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


def test_rag_agent_fallback_cleans_markdown_heavy_context() -> None:
    class MarkdownKnowledgeBase:
        def retrieve(self, query: str, top_k: int = 4, scope=None) -> list[ContextSnippet]:
            return [
                ContextSnippet(
                    source="previous_ads_examples.md",
                    excerpt=(
                        "# Previous Ads Examples\n"
                        "## Purpose\n"
                        "This file stores reusable ad examples and message patterns in a retrieval-friendly format. "
                        "Use it to help the assistant answer with concrete patterns instead of generic ad copy."
                    ),
                    score=0.94,
                ),
                ContextSnippet(
                    source="platform_ads_rules.md",
                    excerpt=(
                        "# Platform Ads Rules\n"
                        "## Global Rules\n"
                        "- No false, misleading, or unrealistic claims.\n"
                        "- Use business language that sounds reviewable and reliable."
                    ),
                    score=0.89,
                ),
            ]

    settings = Settings(enable_live_llm=False, enable_rag=True)
    agent = RAGMarketingKnowledgeAgent(settings, MarkdownKnowledgeBase())

    result = agent.run("How should I market this product?")

    assert "# Previous Ads Examples" not in result.answer
    assert "## Purpose" not in result.answer
    assert "I found the following information:" not in result.answer
    assert "Positioning:" in result.answer or "Proof:" in result.answer


def test_rag_agent_uses_plain_llm_summary_when_json_summary_fails(monkeypatch) -> None:
    settings = Settings(enable_live_llm=True, enable_rag=True)
    agent = RAGMarketingKnowledgeAgent(settings, StubKnowledgeBase())

    def fail_json_summary(question: str, snippets, min_answer_words: int | None):
        raise ValueError("Model response did not contain a JSON object.")

    def plain_summary(question: str, snippets, *, min_answer_words: int | None) -> RAGAgentResponse:
        return RAGAgentResponse(
            answer="Use a direct, proof-led positioning with a lower-friction CTA.",
            relevant_context=["Direct tone", "Proof-led messaging"],
            source_documents=["brand_guidelines.md", "audience_personas.md"],
            confidence="medium",
        )

    monkeypatch.setattr(agent, "_summarize_with_llm", fail_json_summary)
    monkeypatch.setattr(agent, "_summarize_with_plain_llm", plain_summary)

    result = agent.run("How should I position this offer?", min_answer_words=1200)

    assert result.answer == "Use a direct, proof-led positioning with a lower-friction CTA."
