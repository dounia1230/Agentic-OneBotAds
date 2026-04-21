import type { CampaignBriefPayload, CampaignDraftResponse, RuntimeSummary } from "./types";

const API_BASE_URL = (import.meta.env.VITE_API_BASE_URL ?? "").replace(/\/$/, "");

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const response = await fetch(`${API_BASE_URL}${path}`, {
    ...init,
    headers: {
      "Content-Type": "application/json",
      ...(init?.headers ?? {}),
    },
  });

  if (!response.ok) {
    const message = await response.text();
    throw new Error(message || `Request failed with status ${response.status}`);
  }

  return (await response.json()) as T;
}

export function fetchRuntime(): Promise<RuntimeSummary> {
  return request<RuntimeSummary>("/api/v1/runtime");
}

export function createCampaignDraft(
  payload: CampaignBriefPayload,
): Promise<CampaignDraftResponse> {
  return request<CampaignDraftResponse>("/api/v1/campaigns/draft", {
    method: "POST",
    body: JSON.stringify(payload),
  });
}
