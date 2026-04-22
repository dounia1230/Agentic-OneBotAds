import { ChangeEvent, FormEvent, useState } from "react";

import { EmptyState } from "../../../components/ui/EmptyState";
import { SectionIntro } from "../../../components/ui/SectionIntro";
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

export function PublicationGeneratorTab() {
  const [form, setForm] = useState<PublicationFormValues>(defaultPublicationForm);
  const [publication, setPublication] = useState<PublicationPackage | null>(null);
  const [draftWarnings, setDraftWarnings] = useState<string[]>([]);
  const [complianceIssues, setComplianceIssues] = useState<string[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [isSubmitting, setIsSubmitting] = useState(false);

  function handleFieldChange(event: ChangeEvent<HTMLInputElement | HTMLSelectElement>) {
    const target = event.target;
    const value =
      target instanceof HTMLInputElement && target.type === "checkbox" ? target.checked : target.value;

    setForm((current) => ({
      ...current,
      [target.name]: value,
    }));
  }

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setError(null);
    setIsSubmitting(true);

    const [assistantResult, draftResult] = await Promise.allSettled([
      runAssistant({ message: buildPublicationRequestMessage(form) }),
      createCampaignDraft(buildCampaignDraftPayload(form)),
    ]);

    if (draftResult.status === "fulfilled") {
      setDraftWarnings(draftResult.value.warnings);
    } else {
      setDraftWarnings([]);
    }

    if (assistantResult.status === "rejected") {
      setPublication(null);
      setComplianceIssues([]);
      setError(assistantResult.reason instanceof Error ? assistantResult.reason.message : "Unable to generate publication output.");
      setIsSubmitting(false);
      return;
    }

    const nextPublication = derivePublicationOutput(assistantResult.value, form);

    if (!nextPublication) {
      setPublication(null);
      setComplianceIssues([]);
      setError("The assistant responded, but it did not return a publication package.");
      setIsSubmitting(false);
      return;
    }

    setPublication(nextPublication);
    setComplianceIssues(assistantResult.value.compliance?.issues ?? []);
    setIsSubmitting(false);
  }

  return (
    <div className="tab-layout">
      <SectionIntro
        eyebrow="Publication Generator"
        title="Build a structured publication package"
        description="This tab keeps the workflow operator-friendly: focused inputs, structured output, and helper warnings without leaking backend implementation details into the UI."
      />

      {error ? (
        <p className="error-banner" role="alert">
          {error}
        </p>
      ) : null}

      <form className="brief-form" onSubmit={handleSubmit}>
        <div className="field-grid">
          <label>
            Product Name
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

        <label className="checkbox-row">
          <input
            name="generateImage"
            type="checkbox"
            checked={form.generateImage}
            onChange={handleFieldChange}
          />
          Generate image guidance in the package.
        </label>

        <div className="form-actions">
          <button className="primary-action" type="submit" disabled={isSubmitting}>
            {isSubmitting ? "Generating..." : "Generate Publication"}
          </button>
        </div>
      </form>

      {publication ? (
        <div className="result-stack">
          <div className="structured-grid">
            <article className="detail-card">
              <p className="eyebrow">Headline</p>
              <h3>{publication.headline}</h3>
            </article>

            <article className="detail-card">
              <p className="eyebrow">CTA</p>
              <h3>{publication.cta}</h3>
            </article>

            <article className="detail-card span-two">
              <p className="eyebrow">Caption</p>
              <p>{publication.caption}</p>
            </article>

            <article className="detail-card">
              <p className="eyebrow">Compliance Status</p>
              <h3>{publication.compliance_status}</h3>
            </article>

            <article className="detail-card">
              <p className="eyebrow">Status</p>
              <h3>{publication.status}</h3>
            </article>

            <article className="detail-card span-two">
              <p className="eyebrow">Hashtags</p>
              <p>{publication.hashtags.join(" ")}</p>
            </article>

            <article className="detail-card span-two">
              <p className="eyebrow">Image Prompt</p>
              <p>{publication.image_prompt ?? "No image prompt returned in this run."}</p>
            </article>

            <article className="detail-card">
              <p className="eyebrow">Alt Text</p>
              <p>{publication.alt_text ?? "No alt text returned."}</p>
            </article>

            <article className="detail-card">
              <p className="eyebrow">Image Path</p>
              <p>{publication.image_path ?? "No image file created in this flow."}</p>
            </article>

            <article className="detail-card span-two">
              <p className="eyebrow">Recommended Schedule</p>
              <p>{publication.recommended_schedule}</p>
            </article>
          </div>

          <article className="detail-card">
            <div className="card-header">
              <div>
                <p className="eyebrow">Optimization Notes</p>
                <h3>What to refine next</h3>
              </div>
            </div>

            {publication.optimization_notes.length > 0 ? (
              <ul className="bullet-list">
                {publication.optimization_notes.map((note) => (
                  <li key={note}>{note}</li>
                ))}
              </ul>
            ) : (
              <p>No optimization notes were returned for this publication.</p>
            )}
          </article>

          {draftWarnings.length > 0 ? (
            <article className="warning-card">
              <p className="eyebrow">Draft Warnings</p>
              <ul className="bullet-list">
                {draftWarnings.map((warning) => (
                  <li key={warning}>{warning}</li>
                ))}
              </ul>
            </article>
          ) : null}

          {complianceIssues.length > 0 ? (
            <article className="warning-card">
              <p className="eyebrow">Compliance Notes</p>
              <ul className="bullet-list">
                {complianceIssues.map((issue) => (
                  <li key={issue}>{issue}</li>
                ))}
              </ul>
            </article>
          ) : null}
        </div>
      ) : (
        <EmptyState
          title="No publication package yet"
          description="Fill in the inputs and generate a structured publication with headline, caption, CTA, hashtags, image guidance, status, and compliance context."
        />
      )}
    </div>
  );
}
