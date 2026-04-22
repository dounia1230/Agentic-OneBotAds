import csv
from pathlib import Path

from langchain.tools import tool

from onebot_ads.core.config import get_settings


def _safe_divide(numerator: float, denominator: float) -> float:
    return numerator / denominator if denominator else 0.0


@tool
def analyze_campaign_performance(csv_path: str | None = None) -> dict:
    """
    Analyze campaign performance from a CSV file.

    Expected columns:
    campaign_id, platform, audience, impressions, clicks, spend, conversions, revenue
    """
    settings = get_settings()
    source_path = Path(csv_path or settings.campaigns_csv_path)
    if not source_path.exists():
        return {
            "error": "file_not_found",
            "message": f"Campaign CSV not found: {source_path}",
        }

    try:
        import pandas as pd

        df = pd.read_csv(source_path)
        rows = df.to_dict(orient="records")
        columns = set(df.columns)
    except ImportError:
        with source_path.open("r", encoding="utf-8", newline="") as handle:
            reader = csv.DictReader(handle)
            rows = list(reader)
            columns = set(reader.fieldnames or [])

    required_columns = {
        "campaign_id",
        "impressions",
        "clicks",
        "spend",
        "conversions",
        "revenue",
    }

    missing = required_columns - columns
    if missing:
        return {
            "error": "missing_required_columns",
            "missing_columns": sorted(missing),
            "source_path": str(source_path),
        }

    normalized_rows = []
    for row in rows:
        normalized_rows.append(
            {
                "campaign_id": row["campaign_id"],
                "platform": row.get("platform"),
                "audience": row.get("audience"),
                "impressions": float(row["impressions"]),
                "clicks": float(row["clicks"]),
                "spend": float(row["spend"]),
                "conversions": float(row["conversions"]),
                "revenue": float(row["revenue"]),
            }
        )

    total_impressions = sum(row["impressions"] for row in normalized_rows)
    total_clicks = sum(row["clicks"] for row in normalized_rows)
    total_spend = sum(row["spend"] for row in normalized_rows)
    total_conversions = sum(row["conversions"] for row in normalized_rows)
    total_revenue = sum(row["revenue"] for row in normalized_rows)

    campaign_rows = []
    for row in normalized_rows:
        campaign_rows.append(
            {
                "campaign_id": row["campaign_id"],
                "platform": row.get("platform"),
                "audience": row.get("audience"),
                "ctr_percent": round(_safe_divide(row["clicks"], row["impressions"]) * 100, 2),
                "conversion_rate_percent": round(
                    _safe_divide(row["conversions"], row["clicks"]) * 100, 2
                ),
                "cpa": round(_safe_divide(row["spend"], row["conversions"]), 2),
                "roas": round(_safe_divide(row["revenue"], row["spend"]), 2),
                "roi_percent": round(
                    _safe_divide(row["revenue"] - row["spend"], row["spend"]) * 100,
                    2,
                ),
                "spend": round(float(row["spend"]), 2),
                "revenue": round(float(row["revenue"]), 2),
                "clicks": int(row["clicks"]),
                "conversions": int(row["conversions"]),
                "impressions": int(row["impressions"]),
            }
        )

    best_by_roas = max(campaign_rows, key=lambda item: item["roas"], default=None)
    weakest_by_roas = min(campaign_rows, key=lambda item: item["roas"], default=None)

    return {
        "overall": {
            "ctr_percent": round(_safe_divide(total_clicks, total_impressions) * 100, 2),
            "conversion_rate_percent": round(
                _safe_divide(total_conversions, total_clicks) * 100,
                2,
            ),
            "cpa": round(_safe_divide(total_spend, total_conversions), 2),
            "roas": round(_safe_divide(total_revenue, total_spend), 2),
            "roi_percent": round(_safe_divide(total_revenue - total_spend, total_spend) * 100, 2),
            "total_spend": round(total_spend, 2),
            "total_revenue": round(total_revenue, 2),
            "total_impressions": int(total_impressions),
            "total_clicks": int(total_clicks),
            "total_conversions": int(total_conversions),
        },
        "campaigns": campaign_rows,
        "best_campaign_by_roas": best_by_roas,
        "weakest_campaign_by_roas": weakest_by_roas,
        "source_path": str(source_path),
    }
