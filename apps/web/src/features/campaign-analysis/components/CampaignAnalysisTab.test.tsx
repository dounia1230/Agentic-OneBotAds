import { cleanup, fireEvent, render, screen, waitFor } from "@testing-library/react";
import { afterEach, expect, test } from "vitest";

import { CampaignAnalysisTab } from "./CampaignAnalysisTab";

afterEach(() => {
  cleanup();
});

function createCsvFile() {
  const contents = [
    "campaign_id,platform,audience,impressions,clicks,spend,conversions,revenue",
    "launch-1,LinkedIn,Marketing leads,1000,50,200,5,900",
  ].join("\n");

  const file = new File([contents], "campaigns.csv", { type: "text/csv" });
  Object.defineProperty(file, "text", {
    value: async () => contents,
  });
  return file;
}

test("keeps the analyze button hidden until a csv is uploaded", () => {
  render(<CampaignAnalysisTab />);

  expect(screen.queryByRole("button", { name: /Analyze Campaigns/i })).toBeNull();
});

test("reveals the analyze button after upload and marks it done after analysis", async () => {
  render(<CampaignAnalysisTab />);

  const fileInput = screen.getByLabelText(/Campaign CSV file input/i);
  fireEvent.change(fileInput, { target: { files: [createCsvFile()] } });

  const analyzeButton = await screen.findByRole("button", { name: /Analyze Campaigns/i });
  expect(analyzeButton).toBeTruthy();

  fireEvent.click(analyzeButton);

  await waitFor(() => {
    const doneButton = screen.getByRole("button", { name: /^Done$/i }) as HTMLButtonElement;
    expect(doneButton.disabled).toBe(true);
  });

  expect(screen.getByRole("heading", { name: /Performance table/i })).toBeTruthy();
});
