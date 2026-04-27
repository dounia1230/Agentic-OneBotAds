from onebot_ads.agents.rag_agent import RAGMarketingKnowledgeAgent
from onebot_ads.core.config import Settings
from onebot_ads.schemas.campaigns import ContextSnippet, ConversationTurn, RAGAgentResponse


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

    def fail_json_summary(
        question: str,
        snippets,
        min_answer_words: int | None,
        *,
        conversation_history,
    ):
        raise ValueError("Model response did not contain a JSON object.")

    def plain_summary(
        question: str,
        snippets,
        *,
        conversation_history,
        min_answer_words: int | None,
    ) -> RAGAgentResponse:
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


def test_rag_agent_uses_conversation_history_in_retrieval_query() -> None:
    captured: dict[str, str] = {}

    class CapturingKnowledgeBase:
        def retrieve(self, query: str, top_k: int = 4, scope=None) -> list[ContextSnippet]:
            captured["query"] = query
            return [
                ContextSnippet(
                    source="pricing.md",
                    excerpt="The recommended offer framing is discovery-first rather than discount-first.",
                    score=0.91,
                )
            ]

    settings = Settings(enable_live_llm=False, enable_rag=True)
    agent = RAGMarketingKnowledgeAgent(settings, CapturingKnowledgeBase())

    result = agent.run(
        "What about the offer?",
        conversation_history=[
            ConversationTurn(role="user", content="How should I position Atlas Glow?"),
            ConversationTurn(
                role="assistant",
                content="Lead with premium skincare ritual language and keep the tone grounded.",
            ),
        ],
    )

    assert "How should I position Atlas Glow?" in captured["query"]
    assert "Lead with premium skincare ritual language" in captured["query"]
    assert "Current user question: What about the offer?" in captured["query"]
    assert result.answer


def test_rag_agent_builds_company_aware_web_search_query() -> None:
    query = RAGMarketingKnowledgeAgent._build_web_search_query(
        "Create a LinkedIn publication for this company.",
        company_name="HubSpot",
        company_website="https://www.hubspot.com",
        conversation_history=[
            ConversationTurn(role="user", content="I want publication ideas for HubSpot."),
        ],
    )

    assert 'Company name: "HubSpot".' in query
    assert "Website domain: hubspot.com." in query
    assert "site:hubspot.com" in query
    assert "publication ideas" in query.lower()
