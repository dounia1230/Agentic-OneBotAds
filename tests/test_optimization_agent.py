from onebot_ads.agents.optimization_agent import OptimizationStrategyAgent
from onebot_ads.core.config import Settings
from onebot_ads.schemas.campaigns import (
    CampaignAnalysisResponse,
    CampaignAnalysisSummary,
    CreativeCopyResponse,
    RAGAgentResponse,
)


def test_optimization_agent_uses_analysis_creative_and_brand_context() -> None:
    agent = OptimizationStrategyAgent(Settings(enable_live_llm=False))

    analysis = CampaignAnalysisResponse(
        summary=CampaignAnalysisSummary(
            ctr="3.96%",
            conversion_rate="8.48%",
            cpa="$20.22",
            roas="3.53x",
            roi="252.78%",
        ),
        best_campaign="ALT003",
        weakest_campaign="ALT006",
        main_problem="Some campaigns are spending budget without matching conversion efficiency.",
        insights=["LinkedIn SME messaging is the strongest current performance segment."],
        campaign_breakdown=[
            {
                "campaign_id": "ALT003",
                "platform": "LinkedIn",
                "audience": "SMEs",
                "ctr": "4.20%",
                "conversion_rate": "12.10%",
                "cpa": "$18.40",
                "roas": "4.90x",
                "roi": "390.00%",
            },
            {
                "campaign_id": "ALT006",
                "platform": "Facebook",
                "audience": "Broad SMB interests",
                "ctr": "2.10%",
                "conversion_rate": "5.20%",
                "cpa": "$28.75",
                "roas": "1.80x",
                "roi": "80.00%",
            },
        ],
    )
    creative = CreativeCopyResponse(
        headline="Agentic OneBotAds helps SMEs launch better campaigns faster",
        primary_text="Move from insight to launch-ready ads with grounded automation.",
        description="An AI co-pilot for campaign analysis and publication drafting.",
        slogan="Smarter ads. Faster decisions.",
        cta="Book a demo",
        hashtags=["#AgenticOneBotAds"],
        ab_variants=[],
    )
    rag = RAGAgentResponse(
        answer="Use short sentences, concrete outcomes, and practical operator language.",
        relevant_context=["Avoid hype-heavy claims and keep messaging operational."],
        source_documents=[],
        confidence="high",
    )

    result = agent.run(
        analysis,
        rag,
        audience="SMEs and marketing teams",
        goal="increase qualified leads",
        product_name="Agentic OneBotAds",
        creative=creative,
    )

    assert "LinkedIn" in result.quick_wins[0].reason
    assert "ALT006" in result.quick_wins[1].recommendation
    assert any("Book a demo" in item.recommendation for item in result.strategic_changes)
    assert any(
        "Agentic OneBotAds helps SMEs launch better campaigns faster" in test
        for test in result.ab_tests
    )
