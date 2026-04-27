from typing import Annotated

from fastapi import APIRouter, Depends

from onebot_ads.api.dependencies import get_campaign_service
from onebot_ads.schemas.campaigns import (
    AssistantRequest,
    AssistantResponse,
    CampaignBrief,
    CampaignDraftResponse,
    ReindexResponse,
)
from onebot_ads.services.campaign_service import CampaignService

router = APIRouter(tags=["campaigns"])
CampaignServiceDep = Annotated[CampaignService, Depends(get_campaign_service)]


@router.post("/campaigns/draft", response_model=CampaignDraftResponse)
def draft_campaign(brief: CampaignBrief, service: CampaignServiceDep) -> CampaignDraftResponse:
    return service.draft_campaign(brief)


@router.post("/assistant/run", response_model=AssistantResponse)
def run_assistant(request: AssistantRequest, service: CampaignServiceDep) -> AssistantResponse:
    return service.handle_request(
        request.message,
        product_name=request.product_name,
        audience=request.audience,
        goal=request.goal,
        platform=request.platform,
        campaign_csv_content=request.campaign_csv_content,
        campaign_csv_filename=request.campaign_csv_filename,
        knowledge_scope=request.knowledge_scope,
        run_all_agents=request.run_all_agents,
        save_output=request.save_output,
        export_report=request.export_report,
        use_web_search=request.use_web_search,
        min_answer_words=request.min_answer_words,
    )


@router.post("/rag/reindex", response_model=ReindexResponse)
def reindex_knowledge_base(service: CampaignServiceDep) -> ReindexResponse:
    return service.reindex_knowledge_base()
