import json
import re
from textwrap import dedent

from onebot_ads.agents._llm import build_chat_model, extract_json_payload
from onebot_ads.core.config import Settings
from onebot_ads.schemas.campaigns import (
    CampaignAnalysisResponse,
    CreativeCopyResponse,
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
        *,
        user_request: str | None = None,
        platform: str | None = None,
        audience: str | None = None,
        goal: str | None = None,
        product_name: str | None = None,
        creative: CreativeCopyResponse | None = None,
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

        if self.settings.enable_live_llm:
            try:
                return self._generate_with_llm(
                    analysis=analysis,
                    rag_context=rag_context,
                    user_request=user_request,
                    platform=platform,
                    audience=audience,
                    goal=goal,
                    product_name=product_name,
                    creative=creative,
                )
            except Exception:
                pass

        return self._build_fallback_response(
            analysis=analysis,
            rag_context=rag_context,
            platform=platform,
            audience=audience,
            goal=goal,
            product_name=product_name,
            creative=creative,
        )

    def _generate_with_llm(
        self,
        *,
        analysis: CampaignAnalysisResponse,
        rag_context: RAGAgentResponse | None,
        user_request: str | None,
        platform: str | None,
        audience: str | None,
        goal: str | None,
        product_name: str | None,
        creative: CreativeCopyResponse | None,
    ) -> OptimizationResponse:
        from langchain_core.prompts import ChatPromptTemplate

        prompt = ChatPromptTemplate.from_messages(
            [
                ("system", SYSTEM_PROMPT),
                (
                    "human",
                    dedent(
                        """
                        User request: {user_request}
                        Product: {product_name}
                        Platform: {platform}
                        Audience: {audience}
                        Goal: {goal}
                        Campaign analysis: {analysis_json}
                        Creative output: {creative_json}
                        RAG context: {rag_json}

                        Return only valid JSON with keys:
                        quick_wins, strategic_changes, ab_tests

                        quick_wins and strategic_changes must be arrays of objects with:
                        priority, recommendation, reason

                        Keep recommendations specific to the provided campaigns, audiences,
                        creative direction, and brand guidance.
                        """
                    ).strip(),
                ),
            ]
        )
        llm = build_chat_model(self.settings)
        response = llm.invoke(
            prompt.format_messages(
                user_request=user_request or "No additional user request provided.",
                product_name=product_name or "Unknown product",
                platform=platform or "Unknown platform",
                audience=audience or "Unknown audience",
                goal=goal or "Improve campaign performance",
                analysis_json=json.dumps(analysis.model_dump(mode="json"), indent=2),
                creative_json=(
                    json.dumps(creative.model_dump(mode="json"), indent=2)
                    if creative is not None
                    else "null"
                ),
                rag_json=(
                    json.dumps(rag_context.model_dump(mode="json"), indent=2)
                    if rag_context is not None
                    else "null"
                ),
            )
        )
        payload = extract_json_payload(getattr(response, "content", str(response)))
        return OptimizationResponse.model_validate(payload)

    def _build_fallback_response(
        self,
        *,
        analysis: CampaignAnalysisResponse,
        rag_context: RAGAgentResponse | None,
        platform: str | None,
        audience: str | None,
        goal: str | None,
        product_name: str | None,
        creative: CreativeCopyResponse | None,
    ) -> OptimizationResponse:
        quick_wins: list[OptimizationItem] = []
        strategic_changes: list[OptimizationItem] = []

        summary = analysis.summary
        roas_value = self._metric_value(summary.roas)
        cpa_value = self._metric_value(summary.cpa)
        best_row = self._find_campaign_row(analysis, analysis.best_campaign)
        weakest_row = self._find_campaign_row(analysis, analysis.weakest_campaign)
        resolved_audience = audience or best_row.get("audience") or "high-intent segments"
        resolved_goal = goal or "improve campaign performance"
        resolved_product = product_name or "the product"

        if analysis.best_campaign and roas_value >= 3:
            best_platform = best_row.get("platform")
            best_audience = best_row.get("audience")
            best_metrics = []
            if best_row.get("roas"):
                best_metrics.append(f"{best_row['roas']} ROAS")
            if best_row.get("conversion_rate"):
                best_metrics.append(f"{best_row['conversion_rate']} conversion rate")
            performance_reason = (
                f"{best_platform} for {best_audience} is leading with "
                f"{' and '.join(best_metrics)}."
                if best_platform and best_audience and best_metrics
                else "It is the strongest ROAS campaign in the current dataset."
            )
            quick_wins.append(
                OptimizationItem(
                    priority="high",
                    recommendation=(
                        f"Increase budget on {analysis.best_campaign} by 15-20% and keep "
                        "prioritizing the best-performing "
                        f"{best_platform or platform or 'channel'} segments."
                    ),
                    reason=performance_reason,
                )
            )
        if analysis.weakest_campaign:
            weakest_platform = weakest_row.get("platform")
            weakest_audience = weakest_row.get("audience")
            weakest_reason = analysis.main_problem
            weakest_metrics = []
            if weakest_row.get("roas"):
                weakest_metrics.append(f"{weakest_row['roas']} ROAS")
            if weakest_row.get("ctr"):
                weakest_metrics.append(f"{weakest_row['ctr']} CTR")
            if weakest_platform and weakest_audience and weakest_metrics:
                weakest_reason = (
                    f"{weakest_platform} for {weakest_audience} is underperforming at "
                    f"{' and '.join(weakest_metrics)}. {analysis.main_problem}"
                )
            quick_wins.append(
                OptimizationItem(
                    priority="high",
                    recommendation=(
                        f"Reduce spend on {analysis.weakest_campaign} until "
                        "fresh creative is tested."
                    ),
                    reason=weakest_reason,
                )
            )
        if cpa_value > 20:
            weakest_cpa = weakest_row.get("cpa")
            strategic_changes.append(
                OptimizationItem(
                    priority="medium",
                    recommendation=(
                        f"Tighten audience targeting for {resolved_audience} and remove "
                        "low-intent segments from the weakest campaign mix."
                    ),
                    reason=(
                        f"CPA is elevated at {summary.cpa}"
                        + (
                            f", and the weakest row is already at {weakest_cpa}."
                            if weakest_cpa
                            else "."
                        )
                    ),
                )
            )

        strategic_changes.append(
            OptimizationItem(
                priority="medium",
                recommendation=(
                    f"Create a second creative for {resolved_product} focused on "
                    f"{self._build_creative_angle(goal=resolved_goal, creative=creative)}."
                ),
                reason=self._build_creative_reason(
                    rag_context=rag_context,
                    analysis=analysis,
                    creative=creative,
                ),
            )
        )

        if creative is not None:
            strategic_changes.append(
                OptimizationItem(
                    priority="medium",
                    recommendation=(
                        f"Test a sharper CTA against \"{creative.cta}\" and keep the message tied "
                        f"to {resolved_goal.lower()}."
                    ),
                    reason=(
                        f"The current creative is usable, but the CTA can be pushed closer to the "
                        f"campaign goal and strongest audience signal for {resolved_audience}."
                    ),
                )
            )

        ab_tests = self._build_ab_tests(
            creative=creative,
            platform=platform,
            audience=resolved_audience,
            goal=resolved_goal,
            best_row=best_row,
            weakest_row=weakest_row,
        )

        return OptimizationResponse(
            quick_wins=quick_wins,
            strategic_changes=strategic_changes,
            ab_tests=ab_tests,
        )

    @staticmethod
    def _build_creative_reason(
        *,
        rag_context: RAGAgentResponse | None,
        analysis: CampaignAnalysisResponse,
        creative: CreativeCopyResponse | None,
    ) -> str:
        if creative is not None:
            return (
                f"The new creative should stay aligned with the existing headline "
                f"\"{creative.headline}\" while fixing the weakest-performing campaign."
            )

        if rag_context is None:
            return (
                "SME-oriented efficiency messaging fits the current product positioning and "
                f"supports the main issue: {analysis.main_problem.lower()}"
            )

        answer = rag_context.answer.lower()
        if "practical ai-assisted marketing and ads operator" in answer:
            return (
                "The brand is positioned as a practical operator, so a time-savings angle is "
                "more aligned than hype-heavy messaging."
            )
        if "short sentences" in answer or "concrete outcomes" in answer:
            return (
                "Brand guidance favors concrete, operational benefits, and time-savings is a "
                "clear SME-friendly message."
            )
        return (
            "SME-oriented efficiency messaging fits the current product positioning and stays "
            "consistent with the retrieved brand context."
        )

    @staticmethod
    def _build_creative_angle(
        *,
        goal: str,
        creative: CreativeCopyResponse | None,
    ) -> str:
        if creative is not None and creative.description:
            return f"{goal.lower()} with {creative.description.lower()}"
        return f"{goal.lower()} and measurable time savings"

    @staticmethod
    def _find_campaign_row(
        analysis: CampaignAnalysisResponse,
        campaign_id: str | None,
    ) -> dict[str, str]:
        if not campaign_id:
            return {}
        for row in analysis.campaign_breakdown:
            if str(row.get("campaign_id")) == campaign_id:
                return {key: str(value) for key, value in row.items() if value is not None}
        return {}

    @staticmethod
    def _metric_value(value: str | float | int) -> float:
        if isinstance(value, (int, float)):
            return float(value)
        normalized = re.sub(r"[^0-9.\-]", "", value)
        return float(normalized) if normalized else 0.0

    @staticmethod
    def _build_ab_tests(
        *,
        creative: CreativeCopyResponse | None,
        platform: str | None,
        audience: str,
        goal: str,
        best_row: dict[str, str],
        weakest_row: dict[str, str],
    ) -> list[str]:
        tests: list[str] = []
        if creative is not None:
            tests.append(
                "Test the current headline "
                f"\"{creative.headline}\" against a more outcome-led variant "
                f"for {audience}."
            )
            tests.append(
                f"Test CTA \"{creative.cta}\" against a lower-friction CTA "
                f"tied directly to {goal.lower()}."
            )
        else:
            tests.append("Test benefit-focused headline vs. automation-focused headline.")

        best_platform = best_row.get("platform") or platform or "the winning channel"
        best_audience = best_row.get("audience") or audience
        weakest_platform = weakest_row.get("platform") or "the weakest channel"
        tests.append(
            f"Test a {best_platform} visual built around {best_audience} proof "
            "points vs. the current broad campaign composition."
        )
        tests.append(
            "Test the winning audience angle against a fresh creative "
            f"tailored to {weakest_platform} recovery."
        )
        return list(dict.fromkeys(tests))
