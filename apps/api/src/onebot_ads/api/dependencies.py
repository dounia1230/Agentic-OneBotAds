from functools import lru_cache

from onebot_ads.core.config import Settings, get_settings
from onebot_ads.services.campaign_service import CampaignService


@lru_cache
def get_campaign_service() -> CampaignService:
    return CampaignService(get_settings())


def get_app_settings() -> Settings:
    return get_settings()
