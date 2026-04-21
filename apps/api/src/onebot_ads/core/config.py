from functools import lru_cache
from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

PROJECT_ROOT = Path(__file__).resolve().parents[5]


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
        case_sensitive=False,
    )

    app_name: str = "Agentic OneBotAds"
    environment: str = "development"
    api_prefix: str = "/api/v1"
    cors_origins_raw: str = Field(
        default="http://localhost:5173,http://127.0.0.1:5173",
        validation_alias="CORS_ORIGINS",
    )

    ollama_base_url: str = "http://localhost:11434"
    ollama_chat_model: str = "qwen3:8b"
    ollama_embedding_model: str = "nomic-embed-text:latest"
    enable_live_llm: bool = True
    llm_temperature: float = 0.2
    llm_request_timeout_seconds: float = 90.0

    enable_rag: bool = True
    chroma_persist_directory: Path = PROJECT_ROOT / "data" / "chroma"
    chroma_collection_name: str = "onebot_ads_campaigns"
    knowledge_base_directory: Path = PROJECT_ROOT / "data" / "knowledge_base"

    enable_image_generation: bool = False
    image_provider: str = "diffusers"
    image_model_id: str = "runwayml/stable-diffusion-v1-5"
    outputs_directory: Path = PROJECT_ROOT / "outputs"

    def model_post_init(self, __context: object) -> None:
        self.chroma_persist_directory.mkdir(parents=True, exist_ok=True)
        self.knowledge_base_directory.mkdir(parents=True, exist_ok=True)
        self.outputs_directory.mkdir(parents=True, exist_ok=True)
        (self.outputs_directory / "ad_copy").mkdir(parents=True, exist_ok=True)
        (self.outputs_directory / "images").mkdir(parents=True, exist_ok=True)

    @property
    def cors_origins(self) -> list[str]:
        return [origin.strip() for origin in self.cors_origins_raw.split(",") if origin.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()
