from datetime import datetime
from pathlib import Path

from onebot_ads.core.config import get_settings
from onebot_ads.schemas.campaigns import ReportSummary


def write_markdown_report(report: ReportSummary, request_text: str) -> str:
    settings = get_settings()
    output_dir = Path(settings.output_report_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    filename = output_dir / f"campaign_report_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}.md"

    lines = [
        "# Agentic OneBotAds Report",
        "",
        f"Request: {request_text}",
        "",
        "## Executive Summary",
        report.executive_summary,
        "",
        "## KPI Overview",
    ]
    for key, value in report.kpi_overview.items():
        lines.append(f"- {key}: {value}")
    lines.extend(
        [
            "",
            f"## Best Performing Campaign\n{report.best_performing_campaign or 'N/A'}",
            "",
            f"## Weakest Campaign\n{report.weakest_campaign or 'N/A'}",
            "",
            "## Key Insights",
        ]
    )
    lines.extend(f"- {item}" for item in report.key_insights)
    lines.extend(["", "## Recommended Actions"])
    lines.extend(f"- {item}" for item in report.recommended_actions)
    lines.extend(["", "## Next Experiments"])
    lines.extend(f"- {item}" for item in report.next_experiments)

    filename.write_text("\n".join(lines), encoding="utf-8")
    return str(filename)
