import { request } from "./client";
import type {
  AssistantRequest,
  AssistantResponse,
  CampaignBriefPayload,
  CampaignDraftResponse,
} from "../../types/api";

export function createCampaignDraft(
  payload: CampaignBriefPayload,
): Promise<CampaignDraftResponse> {
  return request<CampaignDraftResponse>("/api/v1/campaigns/draft", {
    method: "POST",
    body: JSON.stringify(payload),
  });
}

export function runAssistant(payload: AssistantRequest): Promise<AssistantResponse> {
  return request<AssistantResponse>("/api/v1/assistant/run", {
    method: "POST",
    body: JSON.stringify(payload),
  });
}
