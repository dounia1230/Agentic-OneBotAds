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
    generate_image: bool = False
    compose_publication_image: bool = False
    image_provider: str | None = Field(default="qwen_image", max_length=80)

    @field_validator("channels")
    @classmethod
    def normalize_channels(cls, value: list[str]) -> list[str]:
        normalized = [item.strip().lower().replace(" ", "_") for item in value if item.strip()]
        return normalized or ["meta"]

    @field_validator("image_provider")
    @classmethod
    def normalize_image_provider(cls, value: str | None) -> str:
        return "qwen_image"


class ContextSnippet(BaseModel):
    source: str
    excerpt: str
    score: float | None = None


class ImagePrompt(BaseModel):
    prompt: str
    provider: str
    backend: str | None = None
    space_id: str | None = None
    negative_prompt: str | None = None
    status: str = "prompt_only"
    background_image_path: str | None = None
    publication_image_path: str | None = None
    image_path: str | None = None
    image_url: str | None = None
    alt_text: str | None = None
    error: str | None = None
    notes: list[str] = Field(default_factory=list)
    fallback_used: bool = False
    fallback_attempted: bool = False
    fallback_succeeded: bool = False
    primary_provider: str | None = None
    fallback_provider: str | None = None


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
    compliance_issues: list[str] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)
    status: str = "ready_for_review"
