import { cleanup, fireEvent, render, screen, waitFor } from "@testing-library/react";
import { afterEach, beforeEach, expect, test, vi } from "vitest";

import { PublicationGeneratorTab } from "./PublicationGeneratorTab";

const fetchMock = vi.fn();

afterEach(() => {
  cleanup();
  fetchMock.mockReset();
});

beforeEach(() => {
  vi.stubGlobal("fetch", fetchMock);
});

test("renders campaign draft output alongside the publication package", async () => {
  fetchMock.mockImplementation(async (input: RequestInfo | URL) => {
    const url = String(input);

    if (url.endsWith("/api/v1/assistant/run")) {
      return new Response(
        JSON.stringify({
          intent: "generate_publication",
          plan: {
            intent: "generate_publication",
            agents_to_call: ["rag_agent", "creative_agent", "image_agent", "compliance_agent", "publication_agent"],
            final_format: "publication_package",
          },
          compliance: {
            approved: true,
            issues: [],
            suggested_fixes: [],
            final_safe_version: {
              headline: "Launch smarter campaigns",
              caption: "Create compliant publication packages faster.",
            },
          },
          publication: {
            platform: "LinkedIn",
            headline: "Launch smarter campaigns",
            caption: "Create compliant publication packages faster.",
            cta: "Discover the solution",
            hashtags: ["#OneBotAds", "#MarketingAutomation"],
            image_prompt: "Editorial SaaS campaign visual.",
            image_path: null,
            image_url: null,
            alt_text: "A campaign planning workspace.",
            recommended_schedule: "Tuesday morning",
            compliance_status: "approved",
            optimization_notes: ["Reuse the best-performing proof point in the next test."],
            status: "ready_for_review",
          },
          artifact_paths: [],
          status: "ready_for_review",
        }),
        { status: 200 },
      );
    }

    if (url.endsWith("/api/v1/campaigns/draft")) {
      return new Response(
        JSON.stringify({
          provider: "fallback",
          mode: "fallback",
          summary: "Drafted one LinkedIn-ready campaign variant.",
          variants: [
            {
              channel: "linkedin",
              headline: "Sharper campaign launches for lean teams",
              primary_text: "Move from brief to launch-ready assets with less overhead.",
              cta: "Book a walkthrough",
              rationale: "Focuses LinkedIn copy on clarity, speed, and reviewability.",
            },
          ],
          image_prompt: {
            prompt: "Professional B2B marketing workspace with clean hierarchy.",
            provider: "qwen_image",
            status: "prompt_ready",
            notes: [],
            fallback_used: false,
            fallback_attempted: false,
            fallback_succeeded: false,
          },
          used_context: [],
          compliance_issues: [],
          warnings: [],
          status: "ready_for_review",
        }),
        { status: 200 },
      );
    }

    throw new Error(`Unhandled request: ${url}`);
  });

  render(<PublicationGeneratorTab />);

  fireEvent.click(screen.getByRole("button", { name: /Generate Publication/i }));

  await waitFor(() => {
    expect(screen.getByRole("heading", { name: /Channel-ready variants/i })).toBeTruthy();
  });

  expect(screen.getByText(/Drafted one LinkedIn-ready campaign variant/i)).toBeTruthy();
  expect(screen.getByText(/Sharper campaign launches for lean teams/i)).toBeTruthy();
  expect(screen.getByText(/Ready-to-publish copy/i)).toBeTruthy();
  expect(fetchMock).toHaveBeenCalledTimes(2);
});
