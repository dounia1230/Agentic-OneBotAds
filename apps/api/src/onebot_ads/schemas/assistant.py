from pydantic import BaseModel, Field


class OrchestrationPlan(BaseModel):
    intent: str
    agents_to_call: list[str]
    final_format: str


class AssistantRequest(BaseModel):
    message: str = Field(min_length=3)
    run_all_agents: bool = False
    save_output: bool = False
    export_report: bool = False


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
    provider: str
    backend: str | None = None
    space_id: str | None = None
    background_image_path: str | None = None
    publication_image_path: str | None = None
    image_path: str | None = None
    image_url: str | None = None
    status: str
    error: str | None = None
    notes: list[str] = Field(default_factory=list)
    fallback_used: bool = False
    fallback_attempted: bool = False
    fallback_succeeded: bool = False
    primary_provider: str | None = None
    fallback_provider: str | None = None


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
    image_url: str | None = None
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
    saved_output_path: str | None = None
    artifact_paths: list[str] = Field(default_factory=list)
    status: str = "ready_for_review"
