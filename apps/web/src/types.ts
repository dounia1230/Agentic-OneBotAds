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
  knowledge_base_directory: string;
  outputs_directory: string;
};

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
