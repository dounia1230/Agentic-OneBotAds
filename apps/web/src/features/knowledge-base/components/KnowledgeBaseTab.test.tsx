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
  window.localStorage.clear();
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

test("keeps a multi-turn knowledge conversation and sends prior turns to the backend", async () => {
  const assistantBodies: unknown[] = [];

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
          image_generation_enabled: false,
          image_provider: "qwen_image",
          image_model: "Qwen/Qwen-Image-2512",
          knowledge_base_directory: "data/knowledge_base",
          outputs_directory: "outputs",
        }),
        { status: 200 },
      );
    }

    if (url.endsWith("/api/v1/assistant/run") && init?.method === "POST") {
      const body = JSON.parse(String(init.body));
      assistantBodies.push(body);

      return new Response(
        JSON.stringify({
          intent: "brand_advice",
          plan: {
            intent: "brand_advice",
            agents_to_call: ["rag_agent"],
            final_format: "grounded_brand_guidance",
          },
          rag: {
            answer:
              assistantBodies.length === 1
                ? "Atlas Glow should use premium but grounded skincare language."
                : "Keep the follow-up offer discovery-led and avoid discount-heavy framing.",
            relevant_context: [],
            source_documents: ["brand_guidelines.md"],
            confidence: "medium",
          },
          artifact_paths: [],
          status: "ready_for_review",
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

  fireEvent.change(screen.getByLabelText("Question"), {
    target: { value: "How should I position Atlas Glow?" },
  });
  fireEvent.click(screen.getByRole("button", { name: /^Ask$/i }));

  await waitFor(() => {
    expect(
      screen.getByText(/Atlas Glow should use premium but grounded skincare language/i),
    ).toBeTruthy();
  });

  fireEvent.change(screen.getByLabelText("Question"), {
    target: { value: "What about the offer?" },
  });
  fireEvent.click(screen.getByRole("button", { name: /Ask question/i }));

  await waitFor(() => {
    expect(
      screen.getByText(/Keep the follow-up offer discovery-led/i),
    ).toBeTruthy();
  });

  expect(screen.getByText(/How should I position Atlas Glow\?/i)).toBeTruthy();
  expect(screen.getByText(/What about the offer\?/i)).toBeTruthy();

  expect(assistantBodies).toHaveLength(2);
  expect(assistantBodies[0]).toMatchObject({
    knowledge_base_only: true,
    conversation_history: [],
    message: "How should I position Atlas Glow?",
  });
  expect(assistantBodies[1]).toMatchObject({
    knowledge_base_only: true,
    message: "What about the offer?",
    conversation_history: [
      { role: "user", content: "How should I position Atlas Glow?" },
      {
        role: "assistant",
        content: "Atlas Glow should use premium but grounded skincare language.",
      },
    ],
  });
});

test("restores the knowledge conversation after remount", async () => {
  fetchMock.mockImplementation(async (input: RequestInfo | URL) => {
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
          image_generation_enabled: false,
          image_provider: "qwen_image",
          image_model: "Qwen/Qwen-Image-2512",
          knowledge_base_directory: "data/knowledge_base",
          outputs_directory: "outputs",
        }),
        { status: 200 },
      );
    }

    throw new Error(`Unhandled request: ${url}`);
  });

  window.localStorage.setItem(
    "onebotads.knowledge-chat",
    JSON.stringify({
      conversation: [
        {
          id: "turn-1",
          question: "What tone should I use?",
          answer: "Use a grounded, direct, and professional tone.",
          confidence: "medium",
        },
      ],
      useWebSearch: false,
      longAnswer: true,
    }),
  );

  render(<KnowledgeBaseTab />);

  await waitFor(() => {
    expect(screen.getByText(/What tone should I use\?/i)).toBeTruthy();
  });

  expect(screen.getByText(/Use a grounded, direct, and professional tone/i)).toBeTruthy();
  expect(screen.getByRole("button", { name: /New chat/i })).toBeTruthy();
});
