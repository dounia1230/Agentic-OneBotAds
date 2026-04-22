import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from onebot_ads.api.router import api_router
from onebot_ads.core.config import get_settings

logger = logging.getLogger("uvicorn.error")


def create_app() -> FastAPI:
    settings = get_settings()

    @asynccontextmanager
    async def lifespan(app: FastAPI):
        logger.info(
            "Runtime image config: enabled=%s provider=%s model=%s",
            settings.enable_image_generation,
            settings.image_provider,
            settings.qwen_image_space_id,
        )
        yield

    app = FastAPI(
        title=settings.app_name,
        version="0.1.0",
        description="Local-first campaign generation API for Agentic OneBotAds.",
        lifespan=lifespan,
    )
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    @app.middleware("http")
    async def log_requests(request, call_next):
        response = await call_next(request)
        logger.info("%s %s -> %s", request.method, request.url.path, response.status_code)
        return response

    app.mount("/outputs", StaticFiles(directory=str(settings.outputs_directory)), name="outputs")
    app.include_router(api_router, prefix=settings.api_prefix)
    return app


app = create_app()
