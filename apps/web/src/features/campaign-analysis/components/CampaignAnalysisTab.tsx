import {
  ChangeEvent,
  DragEvent,
  KeyboardEvent,
  useEffect,
  useRef,
  useState,
} from "react";

import { SectionIntro } from "../../../components/ui/SectionIntro";
import { formatCurrency, formatPercent } from "../../../lib/formatters";
import {
  analyzeCampaignCsv,
  type LocalAnalysisResult,
} from "../lib/analyzeCampaignCsv";

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

export function CampaignAnalysisTab() {
  const inputRef = useRef<HTMLInputElement | null>(null);
  const [fileName, setFileName] = useState("");
  const [csvText, setCsvText] = useState("");
  const [result, setResult] = useState<LocalAnalysisResult | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [isAnalyzing, setIsAnalyzing] = useState(false);
  const [isDragActive, setIsDragActive] = useState(false);
  const [lastAnalyzedCsvText, setLastAnalyzedCsvText] = useState<string | null>(null);
  const [isActionVisible, setIsActionVisible] = useState(false);

  const hasUploadedCsv = csvText.length > 0;
  const hasAnalyzedCurrentCsv = hasUploadedCsv && lastAnalyzedCsvText === csvText && result !== null;
  const canAnalyze = hasUploadedCsv && !isAnalyzing && !hasAnalyzedCurrentCsv;

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

  async function loadFile(file: File) {
    if (!file) {
      return;
    }

    setError(null);
    setFileName(file.name);
    setIsDragActive(false);

    try {
      const nextCsvText = await file.text();
      setCsvText(nextCsvText);
      setResult(null);
      setLastAnalyzedCsvText(null);
    } catch (uploadError) {
      setCsvText("");
      setResult(null);
      setLastAnalyzedCsvText(null);
      setError(uploadError instanceof Error ? uploadError.message : "Unable to read the uploaded CSV.");
    }
  }

  async function handleFileChange(event: ChangeEvent<HTMLInputElement>) {
    const file = event.target.files?.[0];
    if (!file) {
      return;
    }

    await loadFile(file);
  }

  function handleDragOver(event: DragEvent<HTMLDivElement>) {
    event.preventDefault();
    setIsDragActive(true);
  }

  function handleDragLeave(event: DragEvent<HTMLDivElement>) {
    event.preventDefault();
    setIsDragActive(false);
  }

  async function handleDrop(event: DragEvent<HTMLDivElement>) {
    event.preventDefault();
    const file = event.dataTransfer.files?.[0];
    if (!file) {
      setIsDragActive(false);
      return;
    }

    await loadFile(file);
  }

  function openFilePicker() {
    inputRef.current?.click();
  }

  function handleDropzoneKeyDown(event: KeyboardEvent<HTMLDivElement>) {
    if (event.key !== "Enter" && event.key !== " ") {
      return;
    }

    event.preventDefault();
    openFilePicker();
  }

  async function handleAnalyze() {
    setError(null);

    if (!csvText) {
      setError("Upload a CSV first, then run the analysis.");
      return;
    }

    setIsAnalyzing(true);

    try {
      await new Promise((resolve) => window.setTimeout(resolve, 160));
      setResult(analyzeCampaignCsv(csvText));
      setLastAnalyzedCsvText(csvText);
    } catch (analysisError) {
      setResult(null);
      setLastAnalyzedCsvText(null);
      setError(analysisError instanceof Error ? analysisError.message : "Unable to analyze the uploaded CSV.");
    } finally {
      setIsAnalyzing(false);
    }
  }

  return (
    <div className="tab-layout">
      <SectionIntro
        eyebrow="Campaign Analysis"
        title="Upload a performance snapshot"
      />

      {error ? (
        <p className="error-banner" role="alert">
          {error}
        </p>
      ) : null}

      <div className="campaign-upload-stack">
        <div
          className={`upload-zone campaign-dropzone ${isDragActive ? "is-drag-active" : ""}`}
          role="button"
          tabIndex={0}
          onClick={openFilePicker}
          onKeyDown={handleDropzoneKeyDown}
          onDragOver={handleDragOver}
          onDragEnter={handleDragOver}
          onDragLeave={handleDragLeave}
          onDrop={handleDrop}
          aria-label="Select campaign CSV"
        >
          <input
            ref={inputRef}
            className="visually-hidden-input"
            type="file"
            accept=".csv"
            onChange={handleFileChange}
            onClick={(event) => {
              event.currentTarget.value = "";
            }}
            aria-label="Campaign CSV file input"
          />
          <UploadCloudIcon />
          <span>Campaign CSV</span>
          <strong>{fileName || "Drop your CSV here or click to browse."}</strong>
          <small>Required columns: campaign_id, impressions, clicks, spend, conversions, revenue</small>
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

      {result ? (
        <div className="result-stack">
          <div className="kpi-grid">
            <article className="kpi-card">
              <span>CTR</span>
              <strong>{formatPercent(result.overall.ctr_percent)}</strong>
            </article>
            <article className="kpi-card">
              <span>Conversion Rate</span>
              <strong>{formatPercent(result.overall.conversion_rate_percent)}</strong>
            </article>
            <article className="kpi-card">
              <span>CPA</span>
              <strong>{formatCurrency(result.overall.cpa)}</strong>
            </article>
            <article className="kpi-card">
              <span>ROAS</span>
              <strong>{result.overall.roas.toFixed(2)}x</strong>
            </article>
            <article className="kpi-card">
              <span>ROI</span>
              <strong>{formatPercent(result.overall.roi_percent)}</strong>
            </article>
          </div>

          <div className="spotlight-grid spotlight-grid-three">
            <article className="spotlight-card success">
              <p className="eyebrow">Best Campaign</p>
              <h3>{result.bestCampaign?.campaign_id ?? "N/A"}</h3>
              <p>
                {result.bestCampaign?.platform ?? "Platform unknown"} with{" "}
                {result.bestCampaign ? `${result.bestCampaign.roas.toFixed(2)}x ROAS` : "no score yet"}
              </p>
            </article>

            <article className="spotlight-card caution">
              <p className="eyebrow">Watch List</p>
              <h3>{result.weakestCampaign?.campaign_id ?? "N/A"}</h3>
              <p>
                {result.weakestCampaign?.platform ?? "Platform unknown"} with{" "}
                {result.weakestCampaign ? `${result.weakestCampaign.roas.toFixed(2)}x ROAS` : "no score yet"}
              </p>
            </article>

            <article className="spotlight-card neutral">
              <p className="eyebrow">Budget Snapshot</p>
              <h3>{formatCurrency(result.overall.total_spend)}</h3>
              <p>{formatCurrency(result.overall.total_revenue)} revenue tracked in this upload.</p>
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
                  {result.campaigns.map((campaign) => (
                    <tr key={campaign.campaign_id}>
                      <td>{campaign.campaign_id}</td>
                      <td>{campaign.platform ?? "N/A"}</td>
                      <td>{campaign.audience ?? "N/A"}</td>
                      <td>{formatPercent(campaign.ctr_percent)}</td>
                      <td>{formatPercent(campaign.conversion_rate_percent)}</td>
                      <td>{formatCurrency(campaign.cpa)}</td>
                      <td>{campaign.roas.toFixed(2)}x</td>
                      <td>{formatPercent(campaign.roi_percent)}</td>
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
              {result.recommendations.map((recommendation) => (
                <li key={recommendation}>{recommendation}</li>
              ))}
            </ul>
          </article>
        </div>
      ) : null}
    </div>
  );
}
