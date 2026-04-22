import { expect, test } from "vitest";

import { analyzeCampaignCsv } from "./analyzeCampaignCsv";

test("analyzes campaign metrics from a csv upload", () => {
  const csv = [
    "campaign_id,platform,audience,impressions,clicks,spend,conversions,revenue",
    "launch-1,LinkedIn,Marketing leads,1000,50,200,5,900",
    "retargeting-1,Meta,Site visitors,1500,45,180,3,300",
  ].join("\n");

  const result = analyzeCampaignCsv(csv);

  expect(result.campaigns).toHaveLength(2);
  expect(result.bestCampaign?.campaign_id).toBe("launch-1");
  expect(result.weakestCampaign?.campaign_id).toBe("retargeting-1");
  expect(result.overall.roas).toBeCloseTo(3.16, 2);
});

test("throws when a required column is missing", () => {
  const csv = [
    "campaign_id,impressions,clicks,spend,revenue",
    "launch-1,1000,50,200,900",
  ].join("\n");

  expect(() => analyzeCampaignCsv(csv)).toThrow(/Missing required columns/i);
});
