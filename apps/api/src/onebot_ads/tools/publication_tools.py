from onebot_ads.tools.creative_tools import normalize_platform


def recommended_schedule_for_platform(platform: str | None) -> str:
    resolved = normalize_platform(platform)
    schedules = {
        "LinkedIn": "Tuesday or Thursday morning",
        "Instagram": "Weekday lunch hour",
        "Facebook": "Wednesday afternoon",
        "Google Ads": "Run continuously with daily budget checks",
    }
    return schedules.get(resolved, "Tuesday morning")
