from typing import Annotated

from fastapi import APIRouter, Depends

from onebot_ads.api.dependencies import get_campaign_service
from onebot_ads.schemas.campaigns import CampaignBrief, CampaignDraftResponse, ReindexResponse
from onebot_ads.services.campaign_service import CampaignService

router = APIRouter(tags=["campaigns"])
CampaignServiceDep = Annotated[CampaignService, Depends(get_campaign_service)]


@router.post("/campaigns/draft", response_model=CampaignDraftResponse)
def draft_campaign(brief: CampaignBrief, service: CampaignServiceDep) -> CampaignDraftResponse:
    return service.draft_campaign(brief)


@router.post("/rag/reindex", response_model=ReindexResponse)
def reindex_knowledge_base(service: CampaignServiceDep) -> ReindexResponse:
    return service.reindex_knowledge_base()
