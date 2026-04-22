export type CsvCampaignRow = {
  campaign_id: string;
  platform?: string;
  audience?: string;
  impressions: number;
  clicks: number;
  spend: number;
  conversions: number;
  revenue: number;
  ctr_percent: number;
  conversion_rate_percent: number;
  cpa: number;
  roas: number;
  roi_percent: number;
};

export type LocalAnalysisResult = {
  overall: {
    ctr_percent: number;
    conversion_rate_percent: number;
    cpa: number;
    roas: number;
    roi_percent: number;
    total_spend: number;
    total_revenue: number;
    total_impressions: number;
    total_clicks: number;
    total_conversions: number;
  };
  campaigns: CsvCampaignRow[];
  bestCampaign?: CsvCampaignRow;
  weakestCampaign?: CsvCampaignRow;
  recommendations: string[];
};

function safeDivide(numerator: number, denominator: number): number {
  return denominator === 0 ? 0 : numerator / denominator;
}

function parseCsvLine(line: string): string[] {
  const cells: string[] = [];
  let current = "";
  let inQuotes = false;

  for (let index = 0; index < line.length; index += 1) {
    const character = line[index];

    if (character === '"') {
      const nextCharacter = line[index + 1];
      if (inQuotes && nextCharacter === '"') {
        current += '"';
        index += 1;
      } else {
        inQuotes = !inQuotes;
      }
      continue;
    }

    if (character === "," && !inQuotes) {
      cells.push(current.trim());
      current = "";
      continue;
    }

    current += character;
  }

  cells.push(current.trim());
  return cells;
}

export function analyzeCampaignCsv(csvText: string): LocalAnalysisResult {
  const lines = csvText
    .split(/\r?\n/)
    .map((line) => line.trim())
    .filter(Boolean);

  if (lines.length < 2) {
    throw new Error("Add a CSV with headers and at least one campaign row.");
  }

  const headers = parseCsvLine(lines[0]);
  const requiredHeaders = ["campaign_id", "impressions", "clicks", "spend", "conversions", "revenue"];
  const missingHeaders = requiredHeaders.filter((header) => !headers.includes(header));

  if (missingHeaders.length > 0) {
    throw new Error(`Missing required columns: ${missingHeaders.join(", ")}`);
  }

  const campaigns: CsvCampaignRow[] = lines.slice(1).map((line) => {
    const cells = parseCsvLine(line);
    const row = Object.fromEntries(headers.map((header, index) => [header, cells[index] ?? ""]));
    const impressions = Number(row.impressions ?? 0);
    const clicks = Number(row.clicks ?? 0);
    const spend = Number(row.spend ?? 0);
    const conversions = Number(row.conversions ?? 0);
    const revenue = Number(row.revenue ?? 0);

    return {
      campaign_id: row.campaign_id,
      platform: row.platform,
      audience: row.audience,
      impressions,
      clicks,
      spend,
      conversions,
      revenue,
      ctr_percent: Number((safeDivide(clicks, impressions) * 100).toFixed(2)),
      conversion_rate_percent: Number((safeDivide(conversions, clicks) * 100).toFixed(2)),
      cpa: Number(safeDivide(spend, conversions).toFixed(2)),
      roas: Number(safeDivide(revenue, spend).toFixed(2)),
      roi_percent: Number((safeDivide(revenue - spend, spend) * 100).toFixed(2)),
    };
  });

  const totals = campaigns.reduce(
    (accumulator, campaign) => ({
      impressions: accumulator.impressions + campaign.impressions,
      clicks: accumulator.clicks + campaign.clicks,
      spend: accumulator.spend + campaign.spend,
      conversions: accumulator.conversions + campaign.conversions,
      revenue: accumulator.revenue + campaign.revenue,
    }),
    { impressions: 0, clicks: 0, spend: 0, conversions: 0, revenue: 0 },
  );

  const bestCampaign = campaigns.reduce((best, campaign) => (campaign.roas > best.roas ? campaign : best));
  const weakestCampaign = campaigns.reduce((worst, campaign) => (campaign.roas < worst.roas ? campaign : worst));

  const recommendations = [
    bestCampaign.roas >= 3
      ? `Scale ${bestCampaign.campaign_id} by 15-20% because it is the strongest ROAS performer.`
      : `Keep ${bestCampaign.campaign_id} active and test adjacent audiences before scaling budget.`,
    `Reduce spend on ${weakestCampaign.campaign_id} until fresh hooks and visuals are tested.`,
    safeDivide(totals.revenue, totals.spend) < 2
      ? "Overall ROAS is under pressure, so tighten targeting and remove low-intent spend."
      : "ROAS is healthy enough to support more aggressive creative testing.",
  ];

  return {
    overall: {
      ctr_percent: Number((safeDivide(totals.clicks, totals.impressions) * 100).toFixed(2)),
      conversion_rate_percent: Number((safeDivide(totals.conversions, totals.clicks) * 100).toFixed(2)),
      cpa: Number(safeDivide(totals.spend, totals.conversions).toFixed(2)),
      roas: Number(safeDivide(totals.revenue, totals.spend).toFixed(2)),
      roi_percent: Number((safeDivide(totals.revenue - totals.spend, totals.spend) * 100).toFixed(2)),
      total_spend: Number(totals.spend.toFixed(2)),
      total_revenue: Number(totals.revenue.toFixed(2)),
      total_impressions: totals.impressions,
      total_clicks: totals.clicks,
      total_conversions: totals.conversions,
    },
    campaigns,
    bestCampaign,
    weakestCampaign,
    recommendations,
  };
}
