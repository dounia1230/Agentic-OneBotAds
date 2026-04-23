import { cleanup, fireEvent, render, screen, waitFor } from "@testing-library/react";
import { afterEach, beforeEach, expect, test, vi } from "vitest";

import { KnowledgeBaseTab } from "./KnowledgeBaseTab";

const fetchMock = vi.fn();

afterEach(() => {
  cleanup();
  fetchMock.mockReset();
});

beforeEach(() => {
  vi.stubGlobal("fetch", fetchMock);
});

test("loads runtime details and can trigger knowledge-base reindexing", async () => {
  fetchMock.mockImplementation(async (input: RequestInfo | URL, init?: RequestInit) => {
    const url = String(input);

    if (url.endsWith("/api/v1/health")) {
      return new Response(
        JSON.stringify({
          status: "ok",
          environment: "development",
          live_llm_enabled: false,
          rag_enabled: true,
        }),
        { status: 200 },
      );
    }

    if (url.endsWith("/api/v1/runtime")) {
      return new Response(
        JSON.stringify({
          app_name: "Agentic OneBotAds",
          environment: "development",
          api_prefix: "/api/v1",
          ollama_base_url: "http://localhost:11434",
          ollama_chat_model: "qwen3:8b",
          ollama_embedding_model: "nomic-embed-text:latest",
          rag_enabled: true,
          image_generation_enabled: true,
          image_provider: "qwen_image",
          image_model: "Qwen/Qwen-Image-2512",
          knowledge_base_directory: "data/knowledge_base",
          outputs_directory: "outputs",
        }),
        { status: 200 },
      );
    }

    if (url.endsWith("/api/v1/rag/reindex") && init?.method === "POST") {
      return new Response(
        JSON.stringify({
          documents_indexed: 7,
          collection_name: "onebot_ads_kb",
          persist_directory: "vector_store/chroma",
          notes: [],
        }),
        { status: 200 },
      );
    }

    throw new Error(`Unhandled request: ${url}`);
  });

  render(<KnowledgeBaseTab />);

  await waitFor(() => {
    expect(screen.getByText(/RAG ready/i)).toBeTruthy();
  });

  fireEvent.click(screen.getByRole("button", { name: /Reindex KB/i }));

  await waitFor(() => {
    expect(screen.getByText(/Reindex complete: 7 documents/i)).toBeTruthy();
  });
});
