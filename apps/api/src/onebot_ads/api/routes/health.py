from typing import Annotated

from fastapi import APIRouter, Depends

from onebot_ads.api.dependencies import get_app_settings
from onebot_ads.core.config import Settings
from onebot_ads.schemas.campaigns import HealthResponse

router = APIRouter(tags=["health"])
SettingsDep = Annotated[Settings, Depends(get_app_settings)]


@router.get("/health", response_model=HealthResponse)
def health(settings: SettingsDep) -> HealthResponse:
    return HealthResponse(
        status="ok",
        environment=settings.environment,
        live_llm_enabled=settings.enable_live_llm,
        rag_enabled=settings.enable_rag,
    )
