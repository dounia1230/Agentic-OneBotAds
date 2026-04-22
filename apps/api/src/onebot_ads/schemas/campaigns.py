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


class OrchestrationPlan(BaseModel):
    intent: str
    agents_to_call: list[str]
    final_format: str


class AssistantRequest(BaseModel):
    message: str = Field(min_length=3)


class RAGAgentResponse(BaseModel):
    answer: str
    relevant_context: list[str] = Field(default_factory=list)
    source_documents: list[str] = Field(default_factory=list)
    confidence: str = "low"


class CampaignAnalysisSummary(BaseModel):
    ctr: str
    conversion_rate: str
    cpa: str
    roas: str
    roi: str


class CampaignAnalysisResponse(BaseModel):
    summary: CampaignAnalysisSummary
    best_campaign: str | None = None
    weakest_campaign: str | None = None
    main_problem: str
    insights: list[str] = Field(default_factory=list)
    campaign_breakdown: list[dict] = Field(default_factory=list)
    raw_data_path: str | None = None


class ABVariant(BaseModel):
    headline: str
    primary_text: str


class CreativeCopyResponse(BaseModel):
    headline: str
    primary_text: str
    description: str
    slogan: str
    cta: str
    hashtags: list[str] = Field(default_factory=list)
    ab_variants: list[ABVariant] = Field(default_factory=list)


class ImageGenerationResponse(BaseModel):
    image_prompt: str
    negative_prompt: str
    alt_text: str
    image_path: str | None = None
    status: str
    notes: list[str] = Field(default_factory=list)


class ComplianceSafeVersion(BaseModel):
    headline: str
    caption: str


class ComplianceReviewResponse(BaseModel):
    approved: bool
    issues: list[str] = Field(default_factory=list)
    suggested_fixes: list[str] = Field(default_factory=list)
    final_safe_version: ComplianceSafeVersion


class OptimizationItem(BaseModel):
    priority: str
    recommendation: str
    reason: str


class OptimizationResponse(BaseModel):
    quick_wins: list[OptimizationItem] = Field(default_factory=list)
    strategic_changes: list[OptimizationItem] = Field(default_factory=list)
    ab_tests: list[str] = Field(default_factory=list)


class PublicationPackage(BaseModel):
    platform: str
    headline: str
    caption: str
    cta: str
    hashtags: list[str] = Field(default_factory=list)
    image_prompt: str | None = None
    image_path: str | None = None
    alt_text: str | None = None
    recommended_schedule: str
    compliance_status: str
    optimization_notes: list[str] = Field(default_factory=list)
    status: str


class ReportSummary(BaseModel):
    executive_summary: str
    kpi_overview: dict[str, str] = Field(default_factory=dict)
    best_performing_campaign: str | None = None
    weakest_campaign: str | None = None
    key_insights: list[str] = Field(default_factory=list)
    recommended_actions: list[str] = Field(default_factory=list)
    next_experiments: list[str] = Field(default_factory=list)
    report_path: str | None = None


class AssistantResponse(BaseModel):
    intent: str
    plan: OrchestrationPlan
    rag: RAGAgentResponse | None = None
    analysis: CampaignAnalysisResponse | None = None
    creative: CreativeCopyResponse | None = None
    image: ImageGenerationResponse | None = None
    optimization: OptimizationResponse | None = None
    compliance: ComplianceReviewResponse | None = None
    publication: PublicationPackage | None = None
    report: ReportSummary | None = None
    status: str = "ready_for_review"
