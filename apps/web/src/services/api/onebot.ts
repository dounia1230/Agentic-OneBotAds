import { request } from "./client";
import type {
  AssistantRequest,
  AssistantResponse,
  CampaignBrief,
  CampaignDraftResponse,
  HealthResponse,
  ReindexResponse,
  RuntimeSummary,
} from "../../types/api";

export function runAssistant(payload: AssistantRequest): Promise<AssistantResponse> {
  return request<AssistantResponse>("/api/v1/assistant/run", {
    method: "POST",
    body: JSON.stringify(payload),
  });
}

export function draftCampaign(payload: CampaignBrief): Promise<CampaignDraftResponse> {
  return request<CampaignDraftResponse>("/api/v1/campaigns/draft", {
    method: "POST",
    body: JSON.stringify(payload),
  });
}

export function getRuntimeSummary(): Promise<RuntimeSummary> {
  return request<RuntimeSummary>("/api/v1/runtime");
}

export function getHealth(): Promise<HealthResponse> {
  return request<HealthResponse>("/api/v1/health");
}

export function reindexKnowledgeBase(): Promise<ReindexResponse> {
  return request<ReindexResponse>("/api/v1/rag/reindex", {
    method: "POST",
  });
}
