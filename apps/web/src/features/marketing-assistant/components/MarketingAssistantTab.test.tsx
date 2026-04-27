import { cleanup, fireEvent, render, screen, waitFor } from "@testing-library/react";
import { afterEach, beforeEach, expect, test, vi } from "vitest";

import { MarketingAssistantTab } from "./MarketingAssistantTab";

const fetchMock = vi.fn();

beforeEach(() => {
  vi.stubGlobal("fetch", fetchMock);
});

afterEach(() => {
  cleanup();
  fetchMock.mockReset();
});

test("submits a unified assistant request and renders multi-agent output", async () => {
  fetchMock.mockImplementation(async (input: RequestInfo | URL, init?: RequestInit) => {
    const url = String(input);

    if (url.endsWith("/api/v1/assistant/run")) {
      const payload = JSON.parse(String(init?.body ?? "{}"));
      expect(payload.min_answer_words).toBe(350);

      return new Response(
        JSON.stringify({
          intent: "full_workflow",
          plan: {
            intent: "full_workflow",
            agents_to_call: ["rag_agent", "analyst_agent", "creative_agent", "optimization_agent"],
            final_format: "full_workflow_bundle",
          },
          rag: {
            answer: "Use a direct and credible tone for SME-facing campaigns.",
            relevant_context: [],
            source_documents: [],
            confidence: "medium",
          },
          analysis: {
            summary: {
              ctr: "4.30%",
              conversion_rate: "7.95%",
              cpa: "22.30",
              roas: "3.00",
              roi: "199.50%",
            },
            best_campaign: "CAMP003",
            weakest_campaign: "CAMP001",
            main_problem: "Some campaigns are spending budget without matching conversion efficiency.",
            insights: ["LinkedIn SMEs is the strongest revenue-efficient segment."],
            campaign_breakdown: [],
          },
          optimization: {
            quick_wins: [
              {
                priority: "high",
                recommendation: "Increase budget on CAMP003 by 15-20%.",
                reason: "It is the strongest ROAS campaign.",
              },
            ],
            strategic_changes: [],
            ab_tests: ["Test benefit-focused headline vs. automation-focused headline."],
          },
          creative: {
            headline: "Smarter ads for SMEs",
            primary_text: "Launch grounded ad copy faster.",
            description: "Description",
            slogan: "Smarter ads. Faster decisions.",
            cta: "Discover the solution",
            hashtags: ["#OneBotAds"],
            ab_variants: [
              {
                headline: "Variant A",
                primary_text: "Test a more benefit-led angle.",
              },
            ],
          },
          artifact_paths: [],
          status: "ready_for_review",
        }),
        { status: 200 },
      );
    }

    throw new Error(`Unhandled request: ${url}`);
  });

  render(
    <MarketingAssistantTab
      campaignCsv={null}
      onCampaignCsvChange={() => {}}
    />,
  );

  fireEvent.click(screen.getByRole("button", { name: /Run Marketing Assistant/i }));

  await waitFor(() => {
    expect(screen.getByRole("heading", { name: /Campaign insights/i })).toBeTruthy();
  });

  expect(screen.queryByText(/Grounded context/i)).toBeNull();
  expect(screen.getByText(/Increase budget on CAMP003/i)).toBeTruthy();
  expect(screen.getByText(/Smarter ads for SMEs/i)).toBeTruthy();
});

test("hides visual output when the image is not composed yet", async () => {
  fetchMock.mockImplementation(async (input: RequestInfo | URL) => {
    const url = String(input);

    if (url.endsWith("/api/v1/assistant/run")) {
      return new Response(
        JSON.stringify({
          intent: "full_workflow",
          plan: {
            intent: "full_workflow",
            agents_to_call: ["rag_agent", "creative_agent"],
            final_format: "full_workflow_bundle",
          },
          creative: {
            headline: "Smarter ads for SMEs",
            primary_text: "Launch grounded ad copy faster.",
            description: "Description",
            slogan: "Smarter ads. Faster decisions.",
            cta: "Discover the solution",
            hashtags: ["#OneBotAds"],
            ab_variants: [],
          },
          image: {
            prompt: "Create a clean LinkedIn campaign image.",
            provider: "qwen_image",
            status: "prompt_ready",
            image_path: "outputs\\images\\marketing_assistant_preview.png",
            image_url: null,
            alt_text: "A campaign workspace.",
            notes: [],
            fallback_used: false,
            fallback_attempted: false,
            fallback_succeeded: false,
          },
          artifact_paths: [],
          status: "ready_for_review",
        }),
        { status: 200 },
      );
    }

    throw new Error(`Unhandled request: ${url}`);
  });

  render(
    <MarketingAssistantTab
      campaignCsv={null}
      onCampaignCsvChange={() => {}}
    />,
  );

  fireEvent.click(screen.getByRole("button", { name: /Run Marketing Assistant/i }));

  await waitFor(() => {
    expect(screen.getByText(/Smarter ads for SMEs/i)).toBeTruthy();
  });

  expect(screen.queryByText(/Visual Output/i)).toBeNull();
  expect(screen.queryByText(/prompt_ready/i)).toBeNull();
});
