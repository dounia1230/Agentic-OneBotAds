from onebot_ads.core.config import Settings
from onebot_ads.schemas.campaigns import CampaignAnalysisResponse, CampaignAnalysisSummary
from onebot_ads.tools.analytics_tools import analyze_campaign_performance

SYSTEM_PROMPT = """
You are the Campaign Data Analyst Agent of Agentic OneBotAds.

Your job is to analyze advertising campaign performance data.

You work with CSV files that may contain:
- campaign_id
- platform
- audience
- impressions
- clicks
- spend
- conversions
- revenue

You must calculate:
- CTR
- conversion rate
- CPA
- ROAS
- ROI
- total spend
- total revenue
- campaign-level performance

Rules:
1. Use the analytics tool when campaign data is requested.
2. Never guess numeric metrics.
3. If a required column is missing, explain the missing field.
4. Highlight the biggest performance problem.
5. Highlight the best campaign or audience.
6. Return clear optimization insights.
""".strip()


class CampaignDataAnalystAgent:
    def __init__(self, settings: Settings) -> None:
        self.settings = settings

    def run(self, csv_path: str | None = None) -> CampaignAnalysisResponse:
        result = analyze_campaign_performance.invoke({"csv_path": csv_path} if csv_path else {})
        if result.get("error"):
            message = result.get("message") or (
                "Missing required columns: " + ", ".join(result.get("missing_columns", []))
            )
            return CampaignAnalysisResponse(
                summary=CampaignAnalysisSummary(
                    ctr="0.00%",
                    conversion_rate="0.00%",
                    cpa="0.00",
                    roas="0.00",
                    roi="0.00%",
                ),
                main_problem=message,
                insights=["Provide a valid campaign CSV to enable grounded performance analysis."],
                raw_data_path=result.get("source_path"),
            )

        overall = result["overall"]
        best = result.get("best_campaign_by_roas")
        weakest = result.get("weakest_campaign_by_roas")
        best_audience = best.get("audience") if best else None
        insights = []
        if best and best_audience:
            insights.append(
                f"{best['platform']} {best_audience} is the strongest revenue-efficient segment."
            )
        if weakest and weakest["ctr_percent"] < overall["ctr_percent"]:
            insights.append("Improve the weakest campaign with a sharper, benefit-led hook.")
        if overall["roas"] < 2:
            insights.append("Overall ROAS is under pressure; reduce spend on underperforming ads.")

        main_problem = (
            "Some campaigns are spending budget without matching conversion efficiency."
            if weakest and weakest["roas"] < best["roas"]
            else "Performance is stable, but stronger creative testing would improve efficiency."
        )

        return CampaignAnalysisResponse(
            summary=CampaignAnalysisSummary(
                ctr=f"{overall['ctr_percent']:.2f}%",
                conversion_rate=f"{overall['conversion_rate_percent']:.2f}%",
                cpa=f"{overall['cpa']:.2f}",
                roas=f"{overall['roas']:.2f}",
                roi=f"{overall['roi_percent']:.2f}%",
            ),
            best_campaign=best["campaign_id"] if best else None,
            weakest_campaign=weakest["campaign_id"] if weakest else None,
            main_problem=main_problem,
            insights=insights,
            campaign_breakdown=result["campaigns"],
            raw_data_path=result.get("source_path"),
        )
