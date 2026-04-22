from pathlib import Path

from onebot_ads.tools.analytics_tools import analyze_campaign_performance


def test_analyze_campaign_performance_returns_expected_metrics() -> None:
    csv_path = Path(__file__).resolve().parents[1] / "data" / "campaigns.csv"

    result = analyze_campaign_performance.invoke({"csv_path": str(csv_path)})

    assert result["overall"]["ctr_percent"] == 3.96
    assert result["overall"]["conversion_rate_percent"] == 8.48
    assert result["overall"]["cpa"] == 20.22
    assert result["overall"]["roas"] == 3.53
    assert result["best_campaign_by_roas"]["campaign_id"] == "CAMP003"
