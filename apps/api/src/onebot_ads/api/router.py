from fastapi import APIRouter

from onebot_ads.api.routes import campaigns, health, runtime

api_router = APIRouter()
api_router.include_router(health.router)
api_router.include_router(runtime.router)
api_router.include_router(campaigns.router)
