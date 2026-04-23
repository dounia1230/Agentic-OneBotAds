import {
  useEffect,
  useLayoutEffect,
  useRef,
  useState,
} from "react";

import { SectionIntro } from "../../../components/ui/SectionIntro";
import { useScrollIntoViewOnChange } from "../../../hooks/useScrollIntoViewOnChange";
import { runAssistant } from "../../../services/api/onebot";
import type {
  AssistantResponse,
  CampaignAnalysisResponse,
  OptimizationResponse,
} from "../../../types/api";
import type { SharedCampaignCsv } from "../../marketing-assistant/components/MarketingAssistantTab";

type CampaignAnalysisTabProps = {
  campaignCsv: SharedCampaignCsv | null;
  onOpenMarketingAssistant: () => void;
};

function UploadCloudIcon() {
  return (
    <svg
      className="upload-zone-icon"
      viewBox="0 0 24 24"
      fill="none"
      aria-hidden="true"
    >
      <path
        d="M7.5 18.5H7A4.5 4.5 0 1 1 8.12 9.64 5.5 5.5 0 0 1 18.37 11a3.75 3.75 0 1 1-.37 7.5H16.5"
        stroke="currentColor"
        strokeWidth="1.7"
        strokeLinecap="round"
        strokeLinejoin="round"
      />
      <path
        d="M12 19V11.25"
        stroke="currentColor"
        strokeWidth="1.7"
        strokeLinecap="round"
      />
      <path
        d="M8.75 14.5 12 11.25l3.25 3.25"
        stroke="currentColor"
        strokeWidth="1.7"
        strokeLinecap="round"
        strokeLinejoin="round"
      />
    </svg>
  );
}

export function CampaignAnalysisTab({
  campaignCsv,
  onOpenMarketingAssistant,
}: CampaignAnalysisTabProps) {
  const shellRef = useRef<HTMLDivElement | null>(null);
  const resultsRef = useRef<HTMLDivElement | null>(null);
  const previousShellRectRef = useRef<DOMRect | null>(null);
  const [assistantResponse, setAssistantResponse] = useState<AssistantResponse | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [isAnalyzing, setIsAnalyzing] = useState(false);
  const [lastAnalyzedCsvText, setLastAnalyzedCsvText] = useState<string | null>(null);
  const [isActionVisible, setIsActionVisible] = useState(false);

  const csvText = campaignCsv?.csvText ?? "";
  const fileName = campaignCsv?.fileName ?? "";
  const analysis = assistantResponse?.analysis ?? null;
  const optimization = assistantResponse?.optimization ?? null;
  const hasUploadedCsv = csvText.length > 0;
  const hasAnalyzedCurrentCsv = hasUploadedCsv && lastAnalyzedCsvText === csvText && analysis !== null;
  const canAnalyze = hasUploadedCsv && !isAnalyzing && !hasAnalyzedCurrentCsv;
  const hasCompletedAnalysis = Boolean(analysis) || Boolean(error);

  useScrollIntoViewOnChange(resultsRef, analysis ?? error);

  useLayoutEffect(() => {
    const shell = shellRef.current;
    if (!shell) {
      previousShellRectRef.current = null;
      return;
    }

    const nextRect = shell.getBoundingClientRect();
    const previousRect = previousShellRectRef.current;

    if (previousRect) {
      const deltaX = previousRect.left - nextRect.left;
      const deltaY = previousRect.top - nextRect.top;

      if (Math.abs(deltaX) > 1 || Math.abs(deltaY) > 1) {
        shell.animate(
          [
            {
              transform: `translate(${deltaX}px, ${deltaY}px)`,
              transformOrigin: "top center",
            },
            {
              transform: "translate(0, 0)",
              transformOrigin: "top center",
            },
          ],
          {
            duration: 440,
            easing: "cubic-bezier(0.22, 1, 0.36, 1)",
          },
        );
      }
    }

    previousShellRectRef.current = nextRect;
  }, [hasCompletedAnalysis]);

  useEffect(() => {
    setAssistantResponse(null);
    setError(null);
    setLastAnalyzedCsvText(null);
  }, [csvText]);

  useEffect(() => {
    if (!hasUploadedCsv) {
      setIsActionVisible(false);
      return;
    }

    setIsActionVisible(false);
    const frameId = window.requestAnimationFrame(() => {
      setIsActionVisible(true);
    });

    return () => {
      window.cancelAnimationFrame(frameId);
    };
  }, [csvText, hasUploadedCsv]);

  async function handleAnalyze() {
    setError(null);

    if (!csvText) {
      setError("Upload a CSV first, then run the analysis.");
      return;
    }

    setIsAnalyzing(true);

    try {
      const nextResponse = await runAssistant({
        message:
          "Analyze the uploaded campaign CSV, calculate campaign KPIs, identify the best and weakest campaigns, and recommend optimization actions.",
        campaign_csv_content: csvText,
        campaign_csv_filename: fileName || "campaigns.csv",
      });

      if (!nextResponse.analysis) {
        throw new Error("The assistant responded, but no campaign analysis was returned.");
      }

      setAssistantResponse(nextResponse);
      setLastAnalyzedCsvText(csvText);
    } catch (analysisError) {
      setAssistantResponse(null);
      setLastAnalyzedCsvText(null);
      setError(analysisError instanceof Error ? analysisError.message : "Unable to analyze the uploaded CSV.");
    } finally {
      setIsAnalyzing(false);
    }
  }

  function findCampaignById(
    campaignAnalysis: CampaignAnalysisResponse,
    campaignId: string | null | undefined,
  ): Record<string, string | number | null> | null {
    if (!campaignId) {
      return null;
    }

    return (
      campaignAnalysis.campaign_breakdown.find(
        (campaign) => String(campaign.campaign_id ?? "") === campaignId,
      ) ?? null
    );
  }

  function formatMetricValue(value: string | number | null | undefined, suffix = ""): string {
    if (value === null || value === undefined || value === "") {
      return "N/A";
    }

    return `${value}${suffix}`;
  }

  function formatCurrencyValue(value: string | number | null | undefined): string {
    if (value === null || value === undefined || value === "") {
      return "N/A";
    }

    const numeric = typeof value === "number" ? value : Number(value);
    if (Number.isNaN(numeric)) {
      return String(value);
    }

    return `$${numeric.toFixed(2)}`;
  }

  const bestCampaign = analysis ? findCampaignById(analysis, analysis.best_campaign) : null;
  const weakestCampaign = analysis ? findCampaignById(analysis, analysis.weakest_campaign) : null;
  const totalSpend = analysis
    ? analysis.campaign_breakdown.reduce((sum, campaign) => sum + Number(campaign.spend ?? 0), 0)
    : 0;
  const totalRevenue = analysis
    ? analysis.campaign_breakdown.reduce((sum, campaign) => sum + Number(campaign.revenue ?? 0), 0)
    : 0;
  const optimizationNotes = optimization
    ? [
        ...optimization.quick_wins.map((item) => item.recommendation),
        ...optimization.strategic_changes.map((item) => item.recommendation),
        ...optimization.ab_tests,
      ]
    : [];

  return (
    <div className={`tab-layout staged-tab ${hasCompletedAnalysis ? "is-active" : ""}`}>
      <div className="staged-tab-stage">
        <div ref={shellRef} className="staged-tab-shell">
          <div className="staged-tab-header">
            <SectionIntro
              eyebrow="Campaign Analysis"
              title="Upload a performance snapshot"
            />
          </div>

          <div className="staged-tab-body staged-tab-body-wide">
            <div className="campaign-upload-stack">
              <div className="upload-zone campaign-dropzone">
                <UploadCloudIcon />
                <span>Campaign CSV</span>
                <strong>{fileName || "Upload your CSV once from Marketing Assistant."}</strong>
                <small>
                  {fileName
                    ? "The shared dataset is ready for analysis in this workspace."
                    : "Use the Marketing Assistant tab to upload a campaign CSV, then return here to analyze it."}
                </small>
                {!fileName ? (
                  <button
                    className="secondary-action"
                    type="button"
                    onClick={onOpenMarketingAssistant}
                  >
                    Open Marketing Assistant
                  </button>
                ) : null}
              </div>

              {hasUploadedCsv ? (
                <div className={`analysis-action-reveal ${isActionVisible ? "is-visible" : ""}`}>
                  <button
                    className="primary-action primary-action-pill analysis-action"
                    type="button"
                    onClick={handleAnalyze}
                    disabled={!canAnalyze}
                    aria-live="polite"
                  >
                    {isAnalyzing ? <span className="button-spinner" aria-hidden="true" /> : null}
                    <span>{isAnalyzing ? "Analyzing..." : hasAnalyzedCurrentCsv ? "Done" : "Analyze Campaigns"}</span>
                  </button>
                </div>
              ) : null}
            </div>
          </div>
        </div>

        {error ? (
          <div
            ref={resultsRef}
            className="result-stack staged-tab-results staged-tab-results-narrow result-message-panel"
            role="alert"
          >
            <p className="eyebrow">Analysis not ready</p>
            <h3>We could not finish the campaign analysis</h3>
            <p>{error}</p>
          </div>
        ) : null}

        {analysis ? (
          <div ref={resultsRef} className="result-stack staged-tab-results staged-tab-results-wide">
            <div className="kpi-grid">
              <article className="kpi-card">
                <span>CTR</span>
                <strong>{analysis.summary.ctr}</strong>
              </article>
              <article className="kpi-card">
                <span>Conversion Rate</span>
                <strong>{analysis.summary.conversion_rate}</strong>
              </article>
              <article className="kpi-card">
                <span>CPA</span>
                <strong>{formatCurrencyValue(analysis.summary.cpa)}</strong>
              </article>
              <article className="kpi-card">
                <span>ROAS</span>
                <strong>{analysis.summary.roas}x</strong>
              </article>
              <article className="kpi-card">
                <span>ROI</span>
                <strong>{analysis.summary.roi}</strong>
              </article>
            </div>

            <div className="spotlight-grid spotlight-grid-three">
              <article className="spotlight-card success">
                <p className="eyebrow">Best Campaign</p>
                <h3>{analysis.best_campaign ?? "N/A"}</h3>
                <p>
                  {String(bestCampaign?.platform ?? "Platform unknown")} with{" "}
                  {formatMetricValue(bestCampaign?.roas, "x ROAS")}
                </p>
              </article>

              <article className="spotlight-card caution">
                <p className="eyebrow">Watch List</p>
                <h3>{analysis.weakest_campaign ?? "N/A"}</h3>
                <p>
                  {String(weakestCampaign?.platform ?? "Platform unknown")} with{" "}
                  {formatMetricValue(weakestCampaign?.roas, "x ROAS")}
                </p>
              </article>

              <article className="spotlight-card neutral">
                <p className="eyebrow">Budget Snapshot</p>
                <h3>{formatCurrencyValue(totalSpend)}</h3>
                <p>{formatCurrencyValue(totalRevenue)} revenue tracked in this upload.</p>
              </article>
            </div>

            <article className="detail-card">
              <div className="card-header">
                <div>
                  <p className="eyebrow">Campaign Performance</p>
                  <h3>Performance table</h3>
                </div>
              </div>

              <div className="table-wrap">
                <table className="data-table">
                  <thead>
                    <tr>
                      <th>Campaign</th>
                      <th>Platform</th>
                      <th>Audience</th>
                      <th>CTR</th>
                      <th>CVR</th>
                      <th>CPA</th>
                      <th>ROAS</th>
                      <th>ROI</th>
                    </tr>
                  </thead>
                  <tbody>
                    {analysis.campaign_breakdown.map((campaign) => (
                      <tr key={String(campaign.campaign_id ?? "unknown-campaign")}>
                        <td>{String(campaign.campaign_id ?? "N/A")}</td>
                        <td>{String(campaign.platform ?? "N/A")}</td>
                        <td>{String(campaign.audience ?? "N/A")}</td>
                        <td>{formatMetricValue(campaign.ctr_percent, "%")}</td>
                        <td>{formatMetricValue(campaign.conversion_rate_percent, "%")}</td>
                        <td>{formatCurrencyValue(campaign.cpa)}</td>
                        <td>{formatMetricValue(campaign.roas, "x")}</td>
                        <td>{formatMetricValue(campaign.roi_percent, "%")}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </article>

            <article className="detail-card">
              <div className="card-header">
                <div>
                  <p className="eyebrow">Optimization</p>
                  <h3>Recommendations</h3>
                </div>
              </div>
              <ul className="bullet-list">
                {(optimizationNotes.length > 0 ? optimizationNotes : analysis.insights).map((recommendation) => (
                  <li key={recommendation}>{recommendation}</li>
                ))}
              </ul>
            </article>
          </div>
        ) : null}
      </div>
    </div>
  );
}
