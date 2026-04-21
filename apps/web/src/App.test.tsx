import { render, screen } from "@testing-library/react";
import { afterEach, beforeEach, expect, test, vi } from "vitest";

import App from "./App";

beforeEach(() => {
  vi.stubGlobal(
    "fetch",
    vi.fn(async () => ({
      ok: true,
      json: async () => ({
        app_name: "Agentic OneBotAds",
        environment: "development",
        api_prefix: "/api/v1",
        ollama_base_url: "http://localhost:11434",
        ollama_chat_model: "qwen3:8b",
        ollama_embedding_model: "nomic-embed-text:latest",
        rag_enabled: true,
        image_generation_enabled: false,
        image_provider: "diffusers",
        knowledge_base_directory: "data/knowledge_base",
        outputs_directory: "outputs",
      }),
      text: async () => "",
    })),
  );
});

afterEach(() => {
  vi.unstubAllGlobals();
});

test("renders campaign control room heading", async () => {
  render(<App />);

  expect(screen.getByText(/Campaign Control Room/i)).toBeTruthy();
});
