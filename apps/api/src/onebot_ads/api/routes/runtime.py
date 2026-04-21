from typing import Annotated

from fastapi import APIRouter, Depends

from onebot_ads.api.dependencies import get_campaign_service
from onebot_ads.schemas.campaigns import RuntimeSummary
from onebot_ads.services.campaign_service import CampaignService

router = APIRouter(tags=["runtime"])
CampaignServiceDep = Annotated[CampaignService, Depends(get_campaign_service)]


@router.get("/runtime", response_model=RuntimeSummary)
def runtime_summary(service: CampaignServiceDep) -> RuntimeSummary:
    return service.runtime_summary()
