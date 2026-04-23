import { cleanup, fireEvent, render, screen, waitFor } from "@testing-library/react";
import { afterEach, beforeEach, expect, test, vi } from "vitest";

import { CampaignAnalysisTab } from "./CampaignAnalysisTab";

const fetchMock = vi.fn();

beforeEach(() => {
  vi.stubGlobal("fetch", fetchMock);
});

afterEach(() => {
  cleanup();
  fetchMock.mockReset();
});

const sharedCampaignCsv = {
  fileName: "campaigns.csv",
  csvText: [
    "campaign_id,platform,audience,impressions,clicks,spend,conversions,revenue",
    "launch-1,LinkedIn,Marketing leads,1000,50,200,5,900",
  ].join("\n"),
};

test("shows a single shared-upload call to action when no csv is available", () => {
  render(<CampaignAnalysisTab campaignCsv={null} onOpenMarketingAssistant={() => {}} />);

  expect(screen.queryByRole("button", { name: /Analyze Campaigns/i })).toBeNull();
  expect(screen.getByRole("button", { name: /Open Marketing Assistant/i })).toBeTruthy();
});

test("reveals the analyze button when a shared csv exists and marks it done after analysis", async () => {
  fetchMock.mockImplementation(async (input: RequestInfo | URL) => {
    const url = String(input);

    if (url.endsWith("/api/v1/assistant/run")) {
      return new Response(
        JSON.stringify({
          intent: "campaign_analysis",
          plan: {
            intent: "campaign_analysis",
            agents_to_call: ["analyst_agent", "optimization_agent"],
            final_format: "campaign_analysis",
          },
          analysis: {
            summary: {
              ctr: "5.00%",
              conversion_rate: "10.00%",
              cpa: "18.00",
              roas: "4.20",
              roi: "220.00%",
            },
            best_campaign: "launch-1",
            weakest_campaign: "launch-1",
            main_problem: "Some campaigns are spending budget without matching conversion efficiency.",
            insights: ["LinkedIn campaigns are currently the strongest performers."],
            campaign_breakdown: [
              {
                campaign_id: "launch-1",
                platform: "LinkedIn",
                audience: "Marketing leads",
                ctr_percent: 5,
                conversion_rate_percent: 10,
                cpa: 18,
                roas: 4.2,
                roi_percent: 220,
                spend: 200,
                revenue: 840,
              },
            ],
          },
          optimization: {
            quick_wins: [
              {
                priority: "high",
                recommendation: "Increase budget on launch-1 by 15-20%.",
                reason: "It is the strongest ROAS campaign.",
              },
            ],
            strategic_changes: [],
            ab_tests: [],
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
    <CampaignAnalysisTab
      campaignCsv={sharedCampaignCsv}
      onOpenMarketingAssistant={() => {}}
    />,
  );

  const analyzeButton = await screen.findByRole("button", { name: /Analyze Campaigns/i });
  expect(analyzeButton).toBeTruthy();

  fireEvent.click(analyzeButton);

  await waitFor(() => {
    const doneButton = screen.getByRole("button", { name: /^Done$/i }) as HTMLButtonElement;
    expect(doneButton.disabled).toBe(true);
  });

  expect(screen.getByRole("heading", { name: /Performance table/i })).toBeTruthy();
  expect(screen.getByText(/Increase budget on launch-1/i)).toBeTruthy();
});
