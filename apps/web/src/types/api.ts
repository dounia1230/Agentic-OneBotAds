export type CampaignBriefPayload = {
  product_name: string;
  audience: string;
  goal: string;
  channels: string[];
  tone: string;
  offer?: string;
  key_points: string[];
  brand_constraints: string[];
  landing_page_url?: string;
  source_context_query?: string;
  generate_image_prompt: boolean;
};

export type ContextSnippet = {
  source: string;
  excerpt: string;
  score?: number | null;
};

export type AdVariant = {
  channel: string;
  headline: string;
  primary_text: string;
  cta: string;
  rationale: string;
};

export type ImagePrompt = {
  prompt: string;
  provider: string;
};

export type CampaignDraftResponse = {
  provider: string;
  mode: string;
  summary: string;
  variants: AdVariant[];
  image_prompt?: ImagePrompt | null;
  used_context: ContextSnippet[];
  warnings: string[];
};

export type AssistantRequest = {
  message: string;
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
};

export type ImageGenerationResponse = {
  image_prompt: string;
  negative_prompt: string;
  alt_text: string;
  image_path?: string | null;
  status: string;
  notes: string[];
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
  alt_text?: string | null;
  recommended_schedule: string;
  compliance_status: string;
  optimization_notes: string[];
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
  status: string;
};
