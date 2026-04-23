import { ChangeEvent, FormEvent, useRef, useState } from "react";

import { SectionIntro } from "../../../components/ui/SectionIntro";
import { useScrollIntoViewOnChange } from "../../../hooks/useScrollIntoViewOnChange";
import { canPreviewImage, resolveMediaUrl } from "../../../lib/media";
import { PLATFORM_OPTIONS } from "../../../lib/platforms";
import { runAssistant } from "../../../services/api/onebot";
import type { AssistantResponse } from "../../../types/api";

export type SharedCampaignCsv = {
  fileName: string;
  csvText: string;
};

type MarketingAssistantTabProps = {
  campaignCsv: SharedCampaignCsv | null;
  onCampaignCsvChange: (campaignCsv: SharedCampaignCsv | null) => void;
};

type AssistantFormValues = {
  message: string;
  productName: string;
  platform: string;
  audience: string;
  goal: string;
  runAllAgents: boolean;
  exportReport: boolean;
  saveOutput: boolean;
};

const defaultAssistantForm: AssistantFormValues = {
  message: "Analyze this campaign data, recommend optimizations, and draft a LinkedIn ad.",
  productName: "Agentic OneBotAds",
  platform: "LinkedIn",
  audience: "SMEs and marketing teams",
  goal: "Increase qualified leads",
  runAllAgents: false,
  exportReport: true,
  saveOutput: false,
};

function renderTextBlocks(value: string) {
  return value
    .split(/\r?\n/)
    .map((line) => line.trim())
    .filter(Boolean)
    .map((line, index) => <p key={`${line}-${index}`}>{line}</p>);
}

export function MarketingAssistantTab({
  campaignCsv,
  onCampaignCsvChange,
}: MarketingAssistantTabProps) {
  const fileInputRef = useRef<HTMLInputElement | null>(null);
  const resultsRef = useRef<HTMLDivElement | null>(null);
  const [form, setForm] = useState<AssistantFormValues>(defaultAssistantForm);
  const [response, setResponse] = useState<AssistantResponse | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [isSubmitting, setIsSubmitting] = useState(false);

  useScrollIntoViewOnChange(resultsRef, response ?? error);

  function handleFieldChange(event: ChangeEvent<HTMLInputElement | HTMLSelectElement | HTMLTextAreaElement>) {
    const target = event.target;
    const value =
      target instanceof HTMLInputElement && target.type === "checkbox" ? target.checked : target.value;

    setForm((current) => ({
      ...current,
      [target.name]: value,
    }));
  }

  async function handleFileChange(event: ChangeEvent<HTMLInputElement>) {
    const file = event.target.files?.[0];
    if (!file) {
      return;
    }

    try {
      onCampaignCsvChange({
        fileName: file.name,
        csvText: await file.text(),
      });
    } catch (fileError) {
      onCampaignCsvChange(null);
      setError(fileError instanceof Error ? fileError.message : "Unable to read the uploaded CSV.");
    }
  }

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setError(null);
    setIsSubmitting(true);

    try {
      const nextResponse = await runAssistant({
        message: form.message,
        product_name: form.productName,
        platform: form.platform,
        audience: form.audience,
        goal: form.goal,
        campaign_csv_content: campaignCsv?.csvText || undefined,
        campaign_csv_filename: campaignCsv?.fileName || undefined,
        run_all_agents: form.runAllAgents,
        export_report: form.exportReport,
        save_output: form.saveOutput,
      });
      setResponse(nextResponse);
    } catch (submitError) {
      setResponse(null);
      setError(
        submitError instanceof Error ? submitError.message : "Unable to run the marketing assistant.",
      );
    } finally {
      setIsSubmitting(false);
    }
  }

  const previewUrl = resolveMediaUrl(response?.image?.image_url ?? response?.image?.image_path);

  return (
    <div className={`tab-layout staged-tab ${response || error ? "is-active" : ""}`}>
      <div className="staged-tab-stage">
        <div className="staged-tab-shell">
          <div className="staged-tab-header">
            <SectionIntro
              eyebrow="Marketing Assistant"
              title="Run the full agentic marketing workflow"
              description="Ask one question, optionally attach campaign CSV data, and get grounded answers, ad drafts, optimization guidance, and report-ready outputs."
            />
          </div>

          <div className="staged-tab-body-wide">
            <form className="brief-form" onSubmit={handleSubmit}>
              <div className="field-grid">
                <label className="span-two">
                  Request
                  <textarea
                    name="message"
                    value={form.message}
                    onChange={handleFieldChange}
                    rows={5}
                    required
                  />
                </label>

                <label>
                  Product / Brand
                  <input name="productName" value={form.productName} onChange={handleFieldChange} />
                </label>

                <label>
                  Platform
                  <select name="platform" value={form.platform} onChange={handleFieldChange}>
                    {PLATFORM_OPTIONS.map((platform) => (
                      <option key={platform} value={platform}>
                        {platform}
                      </option>
                    ))}
                  </select>
                </label>

                <label>
                  Audience
                  <input name="audience" value={form.audience} onChange={handleFieldChange} />
                </label>

                <label>
                  Goal
                  <input name="goal" value={form.goal} onChange={handleFieldChange} />
                </label>
              </div>

              <div
                className="upload-zone"
                role="button"
                tabIndex={0}
                aria-label="Upload campaign CSV"
                onClick={() => fileInputRef.current?.click()}
                onKeyDown={(event) => {
                  if (event.key === "Enter" || event.key === " ") {
                    event.preventDefault();
                    fileInputRef.current?.click();
                  }
                }}
              >
                <input
                  ref={fileInputRef}
                  className="visually-hidden-input"
                  type="file"
                  accept=".csv"
                  aria-label="Upload campaign CSV"
                  onChange={handleFileChange}
                  onClick={(event) => {
                    event.currentTarget.value = "";
                  }}
                />
                <span>Campaign Data</span>
                <strong>{campaignCsv?.fileName || "Attach a campaign CSV for grounded analysis and optimization."}</strong>
                <small>Optional. Required columns: campaign_id, impressions, clicks, spend, conversions, revenue</small>
              </div>

              <label className="checkbox-row">
                <input
                  name="runAllAgents"
                  type="checkbox"
                  checked={form.runAllAgents}
                  onChange={handleFieldChange}
                />
                Run the full workflow bundle in one call.
              </label>

              <label className="checkbox-row">
                <input
                  name="exportReport"
                  type="checkbox"
                  checked={form.exportReport}
                  onChange={handleFieldChange}
                />
                Export a Markdown report when reporting is part of the result.
              </label>

              <label className="checkbox-row">
                <input
                  name="saveOutput"
                  type="checkbox"
                  checked={form.saveOutput}
                  onChange={handleFieldChange}
                />
                Save the assistant output bundle under `outputs/`.
              </label>

              <div className="form-actions">
                <button className="primary-action" type="submit" disabled={isSubmitting}>
                  {isSubmitting ? "Running..." : "Run Marketing Assistant"}
                </button>
              </div>
            </form>
          </div>
        </div>

        {error ? (
          <div
            ref={resultsRef}
            className="result-stack staged-tab-results staged-tab-results-narrow result-message-panel"
            role="alert"
          >
            <p className="eyebrow">Assistant not ready</p>
            <h3>We could not complete the marketing workflow</h3>
            <p>{error}</p>
          </div>
        ) : null}

        {response ? (
          <div ref={resultsRef} className="result-stack staged-tab-results staged-tab-results-wide">
            <div className="structured-grid">
              <article className="detail-card">
                <p className="eyebrow">Intent</p>
                <h3>{response.intent}</h3>
              </article>

              <article className="detail-card">
                <p className="eyebrow">Status</p>
                <h3>{response.status}</h3>
              </article>

              <article className="detail-card span-two">
                <p className="eyebrow">Plan</p>
                <p>{response.plan.final_format}</p>
                <p>{response.plan.agents_to_call.join(" -> ")}</p>
              </article>
            </div>

            {response.rag ? (
              <article className="detail-card">
                <div className="card-header">
                  <div>
                    <p className="eyebrow">Knowledge Answer</p>
                    <h3>Grounded context</h3>
                  </div>
                </div>
                {renderTextBlocks(response.rag.answer)}
              </article>
            ) : null}

            {response.analysis ? (
              <>
                <div className="kpi-grid">
                  <article className="kpi-card">
                    <span>CTR</span>
                    <strong>{response.analysis.summary.ctr}</strong>
                  </article>
                  <article className="kpi-card">
                    <span>Conversion Rate</span>
                    <strong>{response.analysis.summary.conversion_rate}</strong>
                  </article>
                  <article className="kpi-card">
                    <span>CPA</span>
                    <strong>{response.analysis.summary.cpa}</strong>
                  </article>
                  <article className="kpi-card">
                    <span>ROAS</span>
                    <strong>{response.analysis.summary.roas}</strong>
                  </article>
                  <article className="kpi-card">
                    <span>ROI</span>
                    <strong>{response.analysis.summary.roi}</strong>
                  </article>
                </div>

                <article className="detail-card">
                  <div className="card-header">
                    <div>
                      <p className="eyebrow">Performance Analysis</p>
                      <h3>Campaign insights</h3>
                    </div>
                  </div>
                  <p>{response.analysis.main_problem}</p>
                  {response.analysis.insights.length > 0 ? (
                    <ul className="bullet-list">
                      {response.analysis.insights.map((insight) => (
                        <li key={insight}>{insight}</li>
                      ))}
                    </ul>
                  ) : null}
                </article>
              </>
            ) : null}

            {response.optimization ? (
              <article className="detail-card">
                <div className="card-header">
                  <div>
                    <p className="eyebrow">Optimization</p>
                    <h3>Recommended actions</h3>
                  </div>
                </div>
                <ul className="bullet-list">
                  {response.optimization.quick_wins.map((item) => (
                    <li key={item.recommendation}>
                      {item.recommendation} {`(${item.priority})`} - {item.reason}
                    </li>
                  ))}
                  {response.optimization.strategic_changes.map((item) => (
                    <li key={item.recommendation}>
                      {item.recommendation} {`(${item.priority})`} - {item.reason}
                    </li>
                  ))}
                  {response.optimization.ab_tests.map((test) => (
                    <li key={test}>{test}</li>
                  ))}
                </ul>
              </article>
            ) : null}

            {response.creative ? (
              <article className="detail-card">
                <div className="card-header">
                  <div>
                    <p className="eyebrow">Ad Generation</p>
                    <h3>Creative output</h3>
                  </div>
                </div>
                <p>{response.creative.headline}</p>
                <p>{response.creative.primary_text}</p>
                <p>{response.creative.cta}</p>
                <p>{response.creative.hashtags.join(" ")}</p>
                {response.creative.ab_variants.length > 0 ? (
                  <ul className="bullet-list">
                    {response.creative.ab_variants.map((variant) => (
                      <li key={variant.headline}>
                        {variant.headline}: {variant.primary_text}
                      </li>
                    ))}
                  </ul>
                ) : null}
              </article>
            ) : null}

            {response.publication ? (
              <article className="detail-card">
                <div className="card-header">
                  <div>
                    <p className="eyebrow">Publication</p>
                    <h3>Ready-for-review package</h3>
                  </div>
                </div>
                <p>{response.publication.headline}</p>
                <p>{response.publication.caption}</p>
                <p>{response.publication.recommended_schedule}</p>
              </article>
            ) : null}

            {response.image ? (
              <article className="detail-card">
                <div className="card-header">
                  <div>
                    <p className="eyebrow">Visual Output</p>
                    <h3>{response.image.status}</h3>
                  </div>
                </div>
                <p>{response.image.image_prompt}</p>
                {response.image.notes.length > 0 ? (
                  <ul className="bullet-list">
                    {response.image.notes.map((note) => (
                      <li key={note}>{note}</li>
                    ))}
                  </ul>
                ) : null}
                {canPreviewImage(response.image.image_url ?? response.image.image_path) && previewUrl ? (
                  <img className="image-preview" src={previewUrl} alt={response.image.alt_text} />
                ) : null}
              </article>
            ) : null}

            {response.report ? (
              <article className="detail-card">
                <div className="card-header">
                  <div>
                    <p className="eyebrow">Report Summary</p>
                    <h3>Executive-ready output</h3>
                  </div>
                </div>
                <p>{response.report.executive_summary}</p>
                {response.report.recommended_actions.length > 0 ? (
                  <ul className="bullet-list">
                    {response.report.recommended_actions.map((action) => (
                      <li key={action}>{action}</li>
                    ))}
                  </ul>
                ) : null}
              </article>
            ) : null}

            {response.saved_output_path || response.artifact_paths.length > 0 ? (
              <article className="detail-card">
                <div className="card-header">
                  <div>
                    <p className="eyebrow">Artifacts</p>
                    <h3>Saved outputs</h3>
                  </div>
                </div>
                {response.saved_output_path ? <p>{response.saved_output_path}</p> : null}
                {response.artifact_paths.length > 0 ? (
                  <ul className="bullet-list">
                    {response.artifact_paths.map((path) => (
                      <li key={path}>{path}</li>
                    ))}
                  </ul>
                ) : null}
              </article>
            ) : null}
          </div>
        ) : null}
      </div>
    </div>
  );
}
