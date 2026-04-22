from onebot_ads.core.config import Settings
from onebot_ads.schemas.campaigns import (
    CampaignAnalysisResponse,
    OptimizationResponse,
    ReportSummary,
)
from onebot_ads.tools.reporting_tools import write_markdown_report

SYSTEM_PROMPT = """
You are the Reporting Agent of Agentic OneBotAds.

Your role is to transform analytics and optimization outputs into a clear marketing report.

A report must include:
- executive summary
- KPI overview
- best performing campaign
- weakest campaign
- key insights
- recommended actions
- next experiments

Rules:
1. Keep reports clear for business users.
2. Explain metrics simply.
3. Include numbers only when provided by analytics.
4. Write the report in the same language as the user unless instructed otherwise.
5. If requested, export the report as Markdown inside outputs/reports/.
""".strip()


class ReportingAgent:
    def __init__(self, settings: Settings) -> None:
        self.settings = settings

    def run(
        self,
        *,
        analysis: CampaignAnalysisResponse,
        optimization: OptimizationResponse | None,
        request_text: str,
        export_markdown: bool = False,
    ) -> ReportSummary:
        recommended_actions = []
        next_experiments = []
        if optimization:
            recommended_actions = [item.recommendation for item in optimization.quick_wins]
            recommended_actions.extend(
                item.recommendation for item in optimization.strategic_changes
            )
            next_experiments = optimization.ab_tests

        report = ReportSummary(
            executive_summary=(
                f"The account is currently led by {analysis.best_campaign or 'the top campaign'} "
                f"while {analysis.weakest_campaign or 'the weakest campaign'} needs attention."
            ),
            kpi_overview={
                "CTR": analysis.summary.ctr,
                "Conversion Rate": analysis.summary.conversion_rate,
                "CPA": analysis.summary.cpa,
                "ROAS": analysis.summary.roas,
                "ROI": analysis.summary.roi,
            },
            best_performing_campaign=analysis.best_campaign,
            weakest_campaign=analysis.weakest_campaign,
            key_insights=analysis.insights,
            recommended_actions=recommended_actions,
            next_experiments=next_experiments,
        )
        if export_markdown:
            report.report_path = write_markdown_report(report, request_text=request_text)
        return report
