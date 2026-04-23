import { ChangeEvent, FormEvent, useRef, useState } from "react";

import { SectionIntro } from "../../../components/ui/SectionIntro";
import { useScrollIntoViewOnChange } from "../../../hooks/useScrollIntoViewOnChange";
import { PLATFORM_OPTIONS } from "../../../lib/platforms";
import { createCampaignDraft, runAssistant } from "../../../services/api/onebot";
import type { PublicationPackage } from "../../../types/api";
import {
  buildCampaignDraftPayload,
  buildPublicationRequestMessage,
  defaultPublicationForm,
  derivePublicationOutput,
  type PublicationFormValues,
} from "../lib/publication";

function isFilled(value: string): boolean {
  return value.trim().length > 0;
}

function isBlockingPublicationStatus(status: string): boolean {
  const normalized = status.toLowerCase();
  return normalized.includes("error") || normalized.includes("fail") || normalized.includes("needs_revision");
}

function formatStatusLabel(status: string): string {
  return status.replace(/_/g, " ");
}

function escapeHtml(value: string): string {
  return value
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/\"/g, "&quot;")
    .replace(/'/g, "&#39;");
}

function sanitizeFileName(value: string): string {
  const normalized = value.trim().toLowerCase().replace(/[^a-z0-9]+/g, "-");
  return normalized.replace(/^-+|-+$/g, "") || "publication-report";
}

type PublicationReportContent = {
  form: PublicationFormValues;
  publication: PublicationPackage;
  reviewNotes: string[];
  draftWarnings: string[];
  complianceIssues: string[];
};

function renderReportListHtml(items: string[]): string {
  if (items.length === 0) {
    return "";
  }

  return `<ul>${items.map((item) => `<li>${escapeHtml(item)}</li>`).join("")}</ul>`;
}

function buildPublicationReportPlainText({
  form,
  publication,
  reviewNotes,
  draftWarnings,
  complianceIssues,
}: PublicationReportContent): string {
  const lines = [
    "Publication Draft",
    publication.headline,
    `${publication.platform} post for ${form.audience}`,
    "",
    "Metadata",
    `Platform: ${publication.platform}`,
    `Goal: ${form.goal}`,
    `Recommended Time: ${publication.recommended_schedule}`,
    "",
    "Ready-to-publish copy",
    publication.headline,
    publication.caption,
    `CTA: ${publication.cta}`,
    `Hashtags: ${publication.hashtags.join(" ")}`,
  ];

  if (reviewNotes.length > 0) {
    lines.push("", "Review Recommended", ...reviewNotes.map((note) => `- ${note}`));
  }

  if (form.generateImage) {
    lines.push(
      "",
      "Creative Brief",
      `Image Prompt: ${publication.image_prompt ?? "Not provided."}`,
      `Alt Text: ${publication.alt_text ?? "Not provided."}`,
      `Asset Status: ${
        publication.image_path
          ? `Image file: ${publication.image_path}`
          : "Design asset pending; use the prompt above for production."
      }`,
    );
  }

  lines.push("", "Recommendations");

  if (publication.optimization_notes.length > 0) {
    lines.push(...publication.optimization_notes.map((note) => `- ${note}`));
  } else {
    lines.push("Review the copy against the campaign goal, audience fit, and platform tone before scheduling.");
  }

  if (draftWarnings.length > 0) {
    lines.push("", "Backend Notes", ...draftWarnings.map((warning) => `- ${warning}`));
  }

  if (complianceIssues.length > 0) {
    lines.push("", "Compliance Notes", ...complianceIssues.map((issue) => `- ${issue}`));
  }

  return lines.join("\n");
}

function buildPublicationReportHtml({
  form,
  publication,
  reviewNotes,
  draftWarnings,
  complianceIssues,
}: PublicationReportContent): string {
  const optimizationNotes =
    publication.optimization_notes.length > 0
      ? renderReportListHtml(publication.optimization_notes)
      : `<p>Review the copy against the campaign goal, audience fit, and platform tone before scheduling.</p>`;

  const creativeBrief = form.generateImage
    ? `
      <section>
        <h2>Creative Brief</h2>
        <dl class="field-grid">
          <div class="field field-wide">
            <dt>Image Prompt</dt>
            <dd>${escapeHtml(publication.image_prompt ?? "Not provided.")}</dd>
          </div>
          <div class="field">
            <dt>Alt Text</dt>
            <dd>${escapeHtml(publication.alt_text ?? "Not provided.")}</dd>
          </div>
          <div class="field">
            <dt>Asset Status</dt>
            <dd>${escapeHtml(
              publication.image_path
                ? `Image file: ${publication.image_path}`
                : "Design asset pending; use the prompt above for production.",
            )}</dd>
          </div>
        </dl>
      </section>
    `
    : "";

  const reviewSection =
    reviewNotes.length > 0
      ? `
        <section class="callout">
          <p class="eyebrow">Review Recommended</p>
          <h2>Publication available with revision notes</h2>
          ${renderReportListHtml(reviewNotes)}
        </section>
      `
      : "";

  const backendNotes =
    draftWarnings.length > 0
      ? `
        <section>
          <p class="eyebrow">Backend Notes</p>
          ${renderReportListHtml(draftWarnings)}
        </section>
      `
      : "";

  const complianceNotes =
    complianceIssues.length > 0
      ? `
        <section>
          <p class="eyebrow">Compliance Notes</p>
          ${renderReportListHtml(complianceIssues)}
        </section>
      `
      : "";

  return `
    <article class="report-shell">
      <header>
        <p class="eyebrow">Publication Draft</p>
        <h1>${escapeHtml(publication.headline)}</h1>
        <p class="deck">${escapeHtml(publication.platform)} post for ${escapeHtml(form.audience)}</p>
        <dl class="meta-grid">
          <div>
            <dt>Platform</dt>
            <dd>${escapeHtml(publication.platform)}</dd>
          </div>
          <div>
            <dt>Goal</dt>
            <dd>${escapeHtml(form.goal)}</dd>
          </div>
          <div>
            <dt>Recommended Time</dt>
            <dd>${escapeHtml(publication.recommended_schedule)}</dd>
          </div>
        </dl>
      </header>
      ${reviewSection}
      <section>
        <p class="eyebrow">Ready-to-publish copy</p>
        <h2>${escapeHtml(publication.headline)}</h2>
        <p>${escapeHtml(publication.caption)}</p>
        <p class="cta">${escapeHtml(publication.cta)}</p>
        <p class="tags">${escapeHtml(publication.hashtags.join(" "))}</p>
      </section>
      ${creativeBrief}
      <section>
        <h2>Recommendations</h2>
        ${optimizationNotes}
      </section>
      ${backendNotes}
      ${complianceNotes}
    </article>
  `;
}

function buildPublicationReportDocument(content: PublicationReportContent): { html: string; text: string; fileName: string } {
  const fileName = `${sanitizeFileName(content.publication.headline)}.pdf`;
  const html = `
    <!doctype html>
    <html lang="en">
      <head>
        <meta charset="utf-8" />
        <meta name="viewport" content="width=device-width, initial-scale=1" />
        <title>${escapeHtml(fileName)}</title>
        <style>
          :root {
            color-scheme: light;
            --ink: #101828;
            --muted: #516179;
            --accent: #5f8fdf;
            --line: #d8e1ef;
            --panel: #f4f8ff;
            --warn: #a56a00;
          }
          * { box-sizing: border-box; }
          body {
            margin: 0;
            padding: 32px;
            background: #edf3fb;
            color: var(--ink);
            font-family: Inter, "Segoe UI", sans-serif;
          }
          .report-shell {
            max-width: 960px;
            margin: 0 auto;
            padding: 36px;
            background: #ffffff;
            border: 1px solid var(--line);
            border-radius: 18px;
          }
          .eyebrow {
            margin: 0 0 10px;
            font-size: 12px;
            font-weight: 700;
            letter-spacing: 0.08em;
            text-transform: uppercase;
            color: #6d4cff;
          }
          h1, h2 { margin: 0; line-height: 1.15; font-family: "Segoe UI", Inter, sans-serif; }
          h1 { font-size: 36px; max-width: 24ch; }
          h2 { font-size: 24px; margin-bottom: 18px; }
          p { margin: 18px 0 0; line-height: 1.7; }
          .deck, .tags { color: var(--muted); }
          .cta { color: var(--accent); font-weight: 700; }
          .meta-grid, .field-grid {
            display: grid;
            grid-template-columns: repeat(3, minmax(0, 1fr));
            gap: 18px;
            margin: 24px 0 0;
            padding: 20px;
            border-radius: 14px;
            background: var(--panel);
          }
          .field-grid {
            grid-template-columns: repeat(2, minmax(0, 1fr));
          }
          .field-wide {
            grid-column: 1 / -1;
          }
          dt {
            margin-bottom: 6px;
            font-size: 12px;
            font-weight: 700;
            letter-spacing: 0.06em;
            text-transform: uppercase;
            color: var(--muted);
          }
          dd { margin: 0; line-height: 1.7; }
          section {
            margin-top: 32px;
            padding-top: 28px;
            border-top: 1px solid var(--line);
          }
          .callout {
            border-left: 4px solid #f0b94d;
            padding-left: 18px;
          }
          ul {
            margin: 18px 0 0;
            padding-left: 20px;
          }
          li + li {
            margin-top: 10px;
          }
          @media print {
            body {
              padding: 0;
              background: #ffffff;
            }
            .report-shell {
              border: 0;
              border-radius: 0;
              padding: 0;
            }
          }
        </style>
      </head>
      <body>
        ${buildPublicationReportHtml(content)}
      </body>
    </html>
  `;

  return {
    html,
    text: buildPublicationReportPlainText(content),
    fileName,
  };
}

export function PublicationGeneratorTab() {
  const resultsRef = useRef<HTMLDivElement | null>(null);
  const [form, setForm] = useState<PublicationFormValues>(defaultPublicationForm);
  const [publication, setPublication] = useState<PublicationPackage | null>(null);
  const [reviewNotes, setReviewNotes] = useState<string[]>([]);
  const [draftWarnings, setDraftWarnings] = useState<string[]>([]);
  const [complianceIssues, setComplianceIssues] = useState<string[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [actionMessage, setActionMessage] = useState("");
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [lastGeneratedFormSignature, setLastGeneratedFormSignature] = useState<string | null>(null);

  const currentFormSignature = JSON.stringify(form);
  const hasGeneratedCurrentPublication = publication !== null && lastGeneratedFormSignature === currentFormSignature;
  const hasRequiredValues =
    isFilled(form.productName) && isFilled(form.platform) && isFilled(form.audience) && isFilled(form.goal);
  const canGenerate = hasRequiredValues && !isSubmitting && !hasGeneratedCurrentPublication;
  const resultMessage = error || (!hasRequiredValues ? "Fill in all required fields to generate a publication." : null);

  useScrollIntoViewOnChange(resultsRef, publication ?? resultMessage);

  function handleFieldChange(event: ChangeEvent<HTMLInputElement | HTMLSelectElement>) {
    const target = event.target;
    const value =
      target instanceof HTMLInputElement && target.type === "checkbox" ? target.checked : target.value;

    setForm((current) => ({
      ...current,
      [target.name]: value,
    }));
    setPublication(null);
    setReviewNotes([]);
    setDraftWarnings([]);
    setComplianceIssues([]);
    setActionMessage("");
    setLastGeneratedFormSignature(null);
  }

  function getReportContent(currentPublication: PublicationPackage): PublicationReportContent {
    return {
      form,
      publication: currentPublication,
      reviewNotes,
      draftWarnings,
      complianceIssues,
    };
  }

  async function handleCopyReport() {
    if (!publication) {
      return;
    }

    const reportDocument = buildPublicationReportDocument(getReportContent(publication));

    try {
      if (!navigator.clipboard) {
        throw new Error("Clipboard access is unavailable.");
      }

      if ("ClipboardItem" in window && typeof navigator.clipboard.write === "function") {
        await navigator.clipboard.write([
          new ClipboardItem({
            "text/html": new Blob([reportDocument.html], { type: "text/html" }),
            "text/plain": new Blob([reportDocument.text], { type: "text/plain" }),
          }),
        ]);
      } else {
        await navigator.clipboard.writeText(reportDocument.text);
      }

      setActionMessage("Report copied.");
    } catch {
      setActionMessage("Unable to copy the report from this browser.");
    }
  }

  function handleDownloadPdf() {
    if (!publication) {
      return;
    }

    const reportDocument = buildPublicationReportDocument(getReportContent(publication));
    const printWindow = window.open("", "_blank", "noopener,noreferrer");

    if (!printWindow) {
      setActionMessage("Allow pop-ups to download the report as PDF.");
      return;
    }

    printWindow.document.open();
    printWindow.document.write(reportDocument.html);
    printWindow.document.close();

    let hasTriggeredPrint = false;
    const runPrint = () => {
      if (hasTriggeredPrint) {
        return;
      }

      hasTriggeredPrint = true;
      printWindow.focus();
      printWindow.print();
    };

    printWindow.addEventListener("afterprint", () => {
      printWindow.close();
    }, { once: true });

    printWindow.addEventListener("load", () => {
      window.setTimeout(runPrint, 120);
    }, { once: true });

    if (printWindow.document.readyState === "complete") {
      window.setTimeout(runPrint, 120);
    }

    setActionMessage("Print dialog opened. Choose Save as PDF to download.");
  }

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setError(null);

    if (!hasRequiredValues) {
      setError("Fill in product name, platform, audience, and goal before generating a publication.");
      return;
    }

    setIsSubmitting(true);
    const submittedFormSignature = currentFormSignature;

    const [assistantResult, draftResult] = await Promise.allSettled([
      runAssistant({ message: buildPublicationRequestMessage(form) }),
      createCampaignDraft(buildCampaignDraftPayload(form)),
    ]);

    const nextDraftWarnings = draftResult.status === "fulfilled" ? draftResult.value.warnings : [];
    const draftComplianceIssues = draftResult.status === "fulfilled" ? draftResult.value.compliance_issues : [];
    setDraftWarnings(nextDraftWarnings);

    if (assistantResult.status === "rejected") {
      setPublication(null);
      setReviewNotes([]);
      setComplianceIssues([]);
      setLastGeneratedFormSignature(null);
      setError(assistantResult.reason instanceof Error ? assistantResult.reason.message : "Unable to generate publication output.");
      setIsSubmitting(false);
      return;
    }

    if (draftResult.status === "rejected") {
      setPublication(null);
      setReviewNotes([]);
      setComplianceIssues([]);
      setLastGeneratedFormSignature(null);
      setError(draftResult.reason instanceof Error ? draftResult.reason.message : "Unable to validate the publication draft.");
      setIsSubmitting(false);
      return;
    }

    const nextPublication = derivePublicationOutput(assistantResult.value, form);

    if (!nextPublication) {
      setPublication(null);
      setReviewNotes([]);
      setComplianceIssues([]);
      setLastGeneratedFormSignature(null);
      setError("The assistant responded, but it did not return a publication package.");
      setIsSubmitting(false);
      return;
    }

    const nextComplianceIssues = assistantResult.value.compliance?.issues ?? [];
    const nextReviewNotes = [
      ...draftComplianceIssues,
      ...nextComplianceIssues,
      form.generateImage && !isFilled(nextPublication.image_prompt ?? "")
        ? "Image guidance was requested, but no image prompt was returned."
        : null,
      form.generateImage && !isFilled(nextPublication.alt_text ?? "")
        ? "Image guidance was requested, but no alt text was returned."
        : null,
      draftResult.value.status === "needs_revision" ? "The draft response needs revision before it can be shown." : null,
      isBlockingPublicationStatus(nextPublication.status) ? `Generation status: ${formatStatusLabel(nextPublication.status)}.` : null,
      isBlockingPublicationStatus(nextPublication.compliance_status)
        ? `Compliance status: ${formatStatusLabel(nextPublication.compliance_status)}.`
        : null,
    ].filter((message): message is string => Boolean(message));

    setPublication(nextPublication);
    setReviewNotes(nextReviewNotes);
    setComplianceIssues(nextComplianceIssues);
    setLastGeneratedFormSignature(submittedFormSignature);
    setIsSubmitting(false);
  }

  return (
    <div className="tab-layout">
      <SectionIntro
        eyebrow="Publication Generator"
        title="Build a structured publication package"
      />

      <form className="brief-form" onSubmit={handleSubmit}>
        <div className="field-grid">
          <label>
            Product Name
            <input name="productName" value={form.productName} onChange={handleFieldChange} required />
          </label>

          <label>
            Platform
            <select name="platform" value={form.platform} onChange={handleFieldChange} required>
              {PLATFORM_OPTIONS.map((platform) => (
                <option key={platform} value={platform}>
                  {platform}
                </option>
              ))}
            </select>
          </label>

          <label>
            Audience
            <input name="audience" value={form.audience} onChange={handleFieldChange} required />
          </label>

          <label>
            Goal
            <input name="goal" value={form.goal} onChange={handleFieldChange} required />
          </label>
        </div>

        <label className="checkbox-row">
          <input
            name="generateImage"
            type="checkbox"
            checked={form.generateImage}
            onChange={handleFieldChange}
          />
          Generate image guidance in the package.
        </label>

        <div className="form-actions form-actions-center">
          <button
            className="primary-action primary-action-pill analysis-action"
            type="submit"
            disabled={!canGenerate}
            aria-live="polite"
          >
            {isSubmitting ? <span className="button-spinner" aria-hidden="true" /> : null}
            <span>{isSubmitting ? "Generating..." : hasGeneratedCurrentPublication ? "Done" : "Generate Publication"}</span>
          </button>
        </div>
      </form>

      {!publication && resultMessage ? (
        <div ref={resultsRef} className="result-stack result-message-panel" role={error ? "alert" : "status"}>
          <p className="eyebrow">{error ? "Publication not ready" : "Ready when complete"}</p>
          <h3>{error ? "Review needed before showing the publication" : "Complete the brief to continue"}</h3>
          <p>{resultMessage}</p>
        </div>
      ) : null}

      {publication ? (
        <div ref={resultsRef} className="result-stack publication-report">
          <header className="report-header">
            <p className="eyebrow">Publication Draft</p>
            <h3>{publication.headline}</h3>
            <p className="report-deck">{publication.platform} post for {form.audience}</p>
            <dl className="report-meta" aria-label="Publication metadata">
              <div>
                <dt>Platform</dt>
                <dd>{publication.platform}</dd>
              </div>
              <div>
                <dt>Goal</dt>
                <dd>{form.goal}</dd>
              </div>
              <div>
                <dt>Recommended Time</dt>
                <dd>{publication.recommended_schedule}</dd>
              </div>
            </dl>
          </header>

          {reviewNotes.length > 0 ? (
            <section className="warning-card" aria-labelledby="publication-review-heading">
              <p className="eyebrow">Review Recommended</p>
              <h4 id="publication-review-heading">Publication available with revision notes</h4>
              <ul className="bullet-list">
                {reviewNotes.map((note) => (
                  <li key={note}>{note}</li>
                ))}
              </ul>
            </section>
          ) : null}

          <section className="publication-article" aria-labelledby="publication-article-heading">
            <p className="eyebrow">Ready-to-publish copy</p>
            <h4 id="publication-article-heading">{publication.headline}</h4>
            <p>{publication.caption}</p>
            <p className="publication-cta">{publication.cta}</p>
            <p className="publication-tags">{publication.hashtags.join(" ")}</p>
          </section>

          {form.generateImage ? (
            <section className="report-section" aria-labelledby="publication-brief-heading">
              <div className="report-section-heading">
                <h4 id="publication-brief-heading">Creative Brief</h4>
              </div>

              <dl className="report-fields">
                <div className="report-field report-field-wide">
                  <dt>Image Prompt</dt>
                  <dd>{publication.image_prompt}</dd>
                </div>
                <div className="report-field">
                  <dt>Alt Text</dt>
                  <dd>{publication.alt_text}</dd>
                </div>
                <div className="report-field">
                  <dt>Asset Status</dt>
                  <dd>
                    {publication.image_path
                      ? `Image file: ${publication.image_path}`
                      : "Design asset pending; use the prompt above for production."}
                  </dd>
                </div>
              </dl>
            </section>
          ) : null}

          <section className="report-section" aria-labelledby="publication-notes-heading">
            <div className="report-section-heading">
              <h4 id="publication-notes-heading">Recommendations</h4>
            </div>

            {publication.optimization_notes.length > 0 ? (
              <ul className="bullet-list">
                {publication.optimization_notes.map((note) => (
                  <li key={note}>{note}</li>
                ))}
              </ul>
            ) : (
              <p>Review the copy against the campaign goal, audience fit, and platform tone before scheduling.</p>
            )}
          </section>

          {draftWarnings.length > 0 ? (
            <section className="guidance-card">
              <p className="eyebrow">Backend Notes</p>
              <ul className="bullet-list">
                {draftWarnings.map((warning) => (
                  <li key={warning}>{warning}</li>
                ))}
              </ul>
            </section>
          ) : null}

          {complianceIssues.length > 0 ? (
            <section className="warning-card">
              <p className="eyebrow">Compliance Notes</p>
              <ul className="bullet-list">
                {complianceIssues.map((issue) => (
                  <li key={issue}>{issue}</li>
                ))}
              </ul>
            </section>
          ) : null}

          <div className="report-actions" aria-label="Report actions">
            <button
              className="report-icon-button"
              type="button"
              onClick={() => {
                void handleCopyReport();
              }}
              aria-label="Copy formatted report"
              title="Copy formatted report"
            >
              <svg viewBox="0 0 24 24" aria-hidden="true">
                <rect x="9" y="9" width="11" height="11" rx="2" />
                <path d="M7 15H6a2 2 0 0 1-2-2V6a2 2 0 0 1 2-2h7a2 2 0 0 1 2 2v1" />
              </svg>
            </button>
            <button
              className="report-icon-button"
              type="button"
              onClick={handleDownloadPdf}
              aria-label="Download report as PDF"
              title="Download report as PDF"
            >
              <svg viewBox="0 0 24 24" aria-hidden="true">
                <path d="M12 3v11" />
                <path d="m7 10 5 5 5-5" />
                <path d="M5 20h14" />
              </svg>
            </button>
          </div>
          <p className="report-action-status" aria-live="polite">
            {actionMessage}
          </p>
        </div>
      ) : null}
    </div>
  );
}
