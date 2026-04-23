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


def test_analyze_campaign_performance_supports_uploaded_csv_content() -> None:
    csv_content = "\n".join(
        [
            "campaign_id,platform,audience,impressions,clicks,spend,conversions,revenue",
            "CAMP100,LinkedIn,SMEs,1000,50,200,5,800",
            "CAMP200,Instagram,Founders,1500,45,180,3,360",
        ]
    )

    result = analyze_campaign_performance.invoke(
        {
            "csv_content": csv_content,
            "source_label": "uploaded_campaigns.csv",
        }
    )

    assert result["source_path"] == "uploaded_campaigns.csv"
    assert result["overall"]["ctr_percent"] == 3.8
    assert result["best_campaign_by_roas"]["campaign_id"] == "CAMP100"
