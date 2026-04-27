export type AssistantRequest = {
  message: string;
  product_name?: string;
  audience?: string;
  goal?: string;
  platform?: string;
  campaign_csv_content?: string;
  campaign_csv_filename?: string;
  knowledge_scope?: KnowledgeScope;
  run_all_agents?: boolean;
  save_output?: boolean;
  export_report?: boolean;
  use_web_search?: boolean;
  min_answer_words?: number;
};

export type KnowledgeScope = {
  brand_name?: string;
  campaign_name?: string;
};

export type RAGAgentResponse = {
  answer: string;
  relevant_context: string[];
  source_documents: string[];
  confidence: string;
};

export type CampaignAnalysisResponse = {
  summary: {
    ctr: string;
    conversion_rate: string;
    cpa: string;
    roas: string;
    roi: string;
  };
  best_campaign?: string | null;
  weakest_campaign?: string | null;
  main_problem: string;
  insights: string[];
  campaign_breakdown: Record<string, string | number | null>[];
  raw_data_path?: string | null;
};

export type CreativeCopyResponse = {
  headline: string;
  primary_text: string;
  description: string;
  slogan: string;
  cta: string;
  hashtags: string[];
  ab_variants: {
    headline: string;
    primary_text: string;
  }[];
};

export type ImageGenerationResponse = {
  image_prompt: string;
  negative_prompt: string;
  alt_text: string;
  provider: string;
  backend?: string | null;
  space_id?: string | null;
  background_image_path?: string | null;
  publication_image_path?: string | null;
  image_path?: string | null;
  image_url?: string | null;
  status: string;
  error?: string | null;
  notes: string[];
  fallback_used: boolean;
  fallback_attempted: boolean;
  fallback_succeeded: boolean;
  primary_provider?: string | null;
  fallback_provider?: string | null;
};

export type OptimizationItem = {
  priority: string;
  recommendation: string;
  reason: string;
};

export type OptimizationResponse = {
  quick_wins: OptimizationItem[];
  strategic_changes: OptimizationItem[];
  ab_tests: string[];
};

export type ComplianceReviewResponse = {
  approved: boolean;
  issues: string[];
  suggested_fixes: string[];
  final_safe_version: {
    headline: string;
    caption: string;
  };
};

export type PublicationPackage = {
  platform: string;
  headline: string;
  caption: string;
  cta: string;
  hashtags: string[];
  image_prompt?: string | null;
  image_path?: string | null;
  image_url?: string | null;
  alt_text?: string | null;
  recommended_schedule: string;
  compliance_status: string;
  optimization_notes: string[];
  status: string;
};

export type ReportSummary = {
  executive_summary: string;
  kpi_overview: Record<string, string>;
  best_performing_campaign?: string | null;
  weakest_campaign?: string | null;
  key_insights: string[];
  recommended_actions: string[];
  next_experiments: string[];
  report_path?: string | null;
};

export type RuntimeSummary = {
  app_name: string;
  environment: string;
  api_prefix: string;
  ollama_base_url: string;
  ollama_chat_model: string;
  ollama_embedding_model: string;
  rag_enabled: boolean;
  image_generation_enabled: boolean;
  image_provider: string;
  image_model: string;
  knowledge_base_directory: string;
  outputs_directory: string;
};

export type HealthResponse = {
  status: string;
  environment: string;
  live_llm_enabled: boolean;
  rag_enabled: boolean;
};

export type ReindexResponse = {
  documents_indexed: number;
  collection_name: string;
  persist_directory: string;
  notes: string[];
};

export type ContextSnippet = {
  source: string;
  excerpt: string;
  score?: number | null;
};

export type CampaignDraftVariant = {
  channel: string;
  headline: string;
  primary_text: string;
  cta: string;
  rationale: string;
};

export type CampaignDraftImagePrompt = {
  prompt: string;
  provider: string;
  backend?: string | null;
  space_id?: string | null;
  negative_prompt?: string | null;
  status: string;
  background_image_path?: string | null;
  publication_image_path?: string | null;
  image_path?: string | null;
  image_url?: string | null;
  alt_text?: string | null;
  error?: string | null;
  notes: string[];
  fallback_used: boolean;
  fallback_attempted: boolean;
  fallback_succeeded: boolean;
  primary_provider?: string | null;
  fallback_provider?: string | null;
};

export type CampaignBrief = {
  brand_name?: string;
  campaign_name?: string;
  product_name: string;
  audience: string;
  goal: string;
  channels?: string[];
  tone?: string;
  offer?: string;
  key_points?: string[];
  brand_constraints?: string[];
  landing_page_url?: string;
  source_context_query?: string;
  knowledge_scope?: KnowledgeScope;
  generate_image_prompt?: boolean;
  generate_image?: boolean;
  compose_publication_image?: boolean;
  image_provider?: string;
};

export type CampaignDraftResponse = {
  provider: string;
  mode: string;
  summary: string;
  variants: CampaignDraftVariant[];
  image_prompt?: CampaignDraftImagePrompt | null;
  used_context: ContextSnippet[];
  compliance_issues: string[];
  warnings: string[];
  status: string;
};

export type AssistantResponse = {
  intent: string;
  plan: {
    intent: string;
    agents_to_call: string[];
    final_format: string;
  };
  rag?: RAGAgentResponse | null;
  analysis?: CampaignAnalysisResponse | null;
  creative?: CreativeCopyResponse | null;
  image?: ImageGenerationResponse | null;
  optimization?: OptimizationResponse | null;
  compliance?: ComplianceReviewResponse | null;
  publication?: PublicationPackage | null;
  report?: ReportSummary | null;
  saved_output_path?: string | null;
  artifact_paths: string[];
  status: string;
};
