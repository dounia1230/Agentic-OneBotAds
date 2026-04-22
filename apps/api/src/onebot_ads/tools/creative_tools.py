import re


def build_hashtags(product_name: str, platform: str) -> list[str]:
    tokens = [token for token in re.split(r"[^A-Za-z0-9]+", product_name) if token]
    branded = f"#{''.join(token.title() for token in tokens)}" if tokens else "#OneBotAds"
    platform_tag = f"#{platform.replace(' ', '')}"
    return [
        branded,
        "#MarketingAutomation",
        "#AdvertisingAI",
        "#DigitalMarketing",
        platform_tag,
    ]


def normalize_platform(platform: str | None) -> str:
    raw = (platform or "LinkedIn").strip().lower()
    mapping = {
        "linkedin": "LinkedIn",
        "instagram": "Instagram",
        "facebook": "Facebook",
        "google ads": "Google Ads",
        "google": "Google Ads",
        "meta": "Facebook",
    }
    return mapping.get(raw, platform or "LinkedIn")
