from functools import lru_cache
from pathlib import Path

from pydantic import AliasChoices, Field
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
    llm_model: str = Field(
        default="qwen3:8b",
        validation_alias=AliasChoices("LLM_MODEL", "OLLAMA_CHAT_MODEL"),
    )
    embed_model: str = Field(
        default="nomic-embed-text:latest",
        validation_alias=AliasChoices("EMBED_MODEL", "OLLAMA_EMBEDDING_MODEL"),
    )
    enable_live_llm: bool = True
    llm_temperature: float = 0.2
    llm_request_timeout_seconds: float = 90.0

    enable_rag: bool = True
    chroma_path: Path = Field(
        default=PROJECT_ROOT / "vector_store" / "chroma",
        validation_alias=AliasChoices("CHROMA_PATH", "CHROMA_PERSIST_DIRECTORY"),
    )
    chroma_collection: str = Field(
        default="onebotads_kb",
        validation_alias=AliasChoices("CHROMA_COLLECTION", "CHROMA_COLLECTION_NAME"),
    )
    knowledge_base_path: Path = Field(
        default=PROJECT_ROOT / "data" / "knowledge_base",
        validation_alias=AliasChoices("KNOWLEDGE_BASE_PATH", "KNOWLEDGE_BASE_DIRECTORY"),
    )
    campaigns_csv_path: Path = Field(
        default=PROJECT_ROOT / "data" / "campaigns.csv",
        validation_alias="CAMPAIGNS_CSV_PATH",
    )

    enable_image_generation: bool = False
    image_provider: str = "qwen_image"
    qwen_image_space_id: str = Field(
        default="Qwen/Qwen-Image-2512",
        validation_alias="QWEN_IMAGE_SPACE_ID",
    )
    hf_token: str | None = Field(default=None, validation_alias="HF_TOKEN")
    outputs_directory: Path = PROJECT_ROOT / "outputs"
    output_image_dir: Path = Field(
        default=PROJECT_ROOT / "outputs" / "images",
        validation_alias="OUTPUT_IMAGE_DIR",
    )
    output_report_dir: Path = Field(
        default=PROJECT_ROOT / "outputs" / "reports",
        validation_alias="OUTPUT_REPORT_DIR",
    )
    output_post_dir: Path = PROJECT_ROOT / "outputs" / "posts"

    def model_post_init(self, __context: object) -> None:
        self.image_provider = str(self.image_provider).lower()
        self.chroma_path.mkdir(parents=True, exist_ok=True)
        self.knowledge_base_path.mkdir(parents=True, exist_ok=True)
        self.outputs_directory.mkdir(parents=True, exist_ok=True)
        self.output_post_dir.mkdir(parents=True, exist_ok=True)
        self.output_image_dir.mkdir(parents=True, exist_ok=True)
        self.output_report_dir.mkdir(parents=True, exist_ok=True)

    @property
    def cors_origins(self) -> list[str]:
        return [origin.strip() for origin in self.cors_origins_raw.split(",") if origin.strip()]

    @property
    def ollama_chat_model(self) -> str:
        return self.llm_model

    @property
    def ollama_embedding_model(self) -> str:
        return self.embed_model

    @property
    def chroma_persist_directory(self) -> Path:
        return self.chroma_path

    @property
    def chroma_collection_name(self) -> str:
        return self.chroma_collection

    @property
    def knowledge_base_directory(self) -> Path:
        return self.knowledge_base_path

    @property
    def image_model_id(self) -> str:
        return self.qwen_image_space_id


@lru_cache
def get_settings() -> Settings:
    return Settings()
