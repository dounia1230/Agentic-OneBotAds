from pydantic import BaseModel, Field, HttpUrl, field_validator


class CampaignBrief(BaseModel):
    product_name: str = Field(min_length=2, max_length=120)
    audience: str = Field(min_length=3, max_length=240)
    goal: str = Field(min_length=3, max_length=240)
    channels: list[str] = Field(default_factory=lambda: ["meta", "linkedin"])
    tone: str = Field(default="clear, credible, conversion-focused", max_length=120)
    offer: str | None = Field(default=None, max_length=240)
    key_points: list[str] = Field(default_factory=list)
    brand_constraints: list[str] = Field(default_factory=list)
    landing_page_url: HttpUrl | None = None
    source_context_query: str | None = Field(default=None, max_length=240)
    generate_image_prompt: bool = True

    @field_validator("channels")
    @classmethod
    def normalize_channels(cls, value: list[str]) -> list[str]:
        normalized = [item.strip().lower().replace(" ", "_") for item in value if item.strip()]
        return normalized or ["meta"]


class ContextSnippet(BaseModel):
    source: str
    excerpt: str
    score: float | None = None


class ImagePrompt(BaseModel):
    prompt: str
    provider: str


class AdVariant(BaseModel):
    channel: str
    headline: str
    primary_text: str
    cta: str
    rationale: str


class CampaignDraftResponse(BaseModel):
    provider: str
    mode: str
    summary: str
    variants: list[AdVariant]
    image_prompt: ImagePrompt | None = None
    used_context: list[ContextSnippet] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)


class RuntimeSummary(BaseModel):
    app_name: str
    environment: str
    api_prefix: str
    ollama_base_url: str
    ollama_chat_model: str
    ollama_embedding_model: str
    rag_enabled: bool
    image_generation_enabled: bool
    image_provider: str
    knowledge_base_directory: str
    outputs_directory: str


class HealthResponse(BaseModel):
    status: str
    environment: str
    live_llm_enabled: bool
    rag_enabled: bool


class ReindexResponse(BaseModel):
    documents_indexed: int
    collection_name: str
    persist_directory: str
    notes: list[str] = Field(default_factory=list)
