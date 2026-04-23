import { request } from "./client";
import type {
  AssistantRequest,
  AssistantResponse,
} from "../../types/api";

export function runAssistant(payload: AssistantRequest): Promise<AssistantResponse> {
  return request<AssistantResponse>("/api/v1/assistant/run", {
    method: "POST",
    body: JSON.stringify(payload),
  });
}
