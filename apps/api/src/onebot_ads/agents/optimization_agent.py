from onebot_ads.core.config import Settings
from onebot_ads.schemas.campaigns import (
    CampaignAnalysisResponse,
    OptimizationItem,
    OptimizationResponse,
    RAGAgentResponse,
)

SYSTEM_PROMPT = """
You are the Optimization Strategy Agent of Agentic OneBotAds.

Your role is to turn campaign insights into practical optimization recommendations.

Use campaign analytics when provided.
Use RAG brand/marketing context when provided.

You must recommend:
- what to scale
- what to reduce
- what to test
- what audience to keep
- what audience to exclude
- how to improve copy
- how to improve visuals
- how to improve CTA
- what next experiment to run

Rules:
1. Recommendations must be specific and actionable.
2. Do not recommend increasing budget without a performance reason.
3. Use ROAS, CPA, CTR, and conversion rate to justify campaign decisions.
4. Separate quick wins from strategic changes.
5. Return priority levels: high, medium, low.
""".strip()


class OptimizationStrategyAgent:
    def __init__(self, settings: Settings) -> None:
        self.settings = settings

    def run(
        self,
        analysis: CampaignAnalysisResponse | None,
        rag_context: RAGAgentResponse | None = None,
    ) -> OptimizationResponse:
        if analysis is None:
            return OptimizationResponse(
                quick_wins=[
                    OptimizationItem(
                        priority="medium",
                        recommendation=(
                            "Review the latest campaign data before changing "
                            "budget allocation."
                        ),
                        reason=(
                            "Grounded optimization requires current CTR, CPA, "
                            "ROAS, and ROI inputs."
                        ),
                    )
                ],
                strategic_changes=[],
                ab_tests=["Test a benefit-led headline against an automation-led headline."],
            )

        quick_wins: list[OptimizationItem] = []
        strategic_changes: list[OptimizationItem] = []
        ab_tests = [
            "Test benefit-focused headline vs. automation-focused headline.",
            "Test dashboard visual vs. team-at-work visual.",
        ]

        summary = analysis.summary
        roas_value = float(summary.roas)
        cpa_value = float(summary.cpa)

        if analysis.best_campaign and roas_value >= 3:
            quick_wins.append(
                OptimizationItem(
                    priority="high",
                    recommendation=f"Increase budget on {analysis.best_campaign} by 15-20%.",
                    reason="It is the strongest ROAS campaign in the current dataset.",
                )
            )
        if analysis.weakest_campaign:
            quick_wins.append(
                OptimizationItem(
                    priority="high",
                    recommendation=(
                        f"Reduce spend on {analysis.weakest_campaign} until "
                        "fresh creative is tested."
                    ),
                    reason=analysis.main_problem,
                )
            )
        if cpa_value > 20:
            strategic_changes.append(
                OptimizationItem(
                    priority="medium",
                    recommendation="Tighten audience targeting and remove low-intent segments.",
                    reason="CPA is elevated relative to the current conversion efficiency.",
                )
            )

        strategic_changes.append(
            OptimizationItem(
                priority="medium",
                recommendation="Create a second creative focused on time savings for SMEs.",
                reason=(
                    rag_context.answer
                    if rag_context
                    else "SME-oriented efficiency messaging fits the current product positioning."
                ),
            )
        )

        return OptimizationResponse(
            quick_wins=quick_wins,
            strategic_changes=strategic_changes,
            ab_tests=ab_tests,
        )
