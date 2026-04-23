import { ChangeEvent, FormEvent, useRef, useState } from "react";

import { EmptyState } from "../../../components/ui/EmptyState";
import { SectionIntro } from "../../../components/ui/SectionIntro";
import { useScrollIntoViewOnChange } from "../../../hooks/useScrollIntoViewOnChange";
import { canPreviewImage } from "../../../lib/media";
import { PLATFORM_OPTIONS } from "../../../lib/platforms";
import { runAssistant } from "../../../services/api/onebot";
import type { ImageGenerationResponse } from "../../../types/api";

type ImagePromptFormValues = {
  productName: string;
  platform: string;
  audience: string;
  style: string;
  generateImage: boolean;
};

const defaultImageForm: ImagePromptFormValues = {
  productName: "Agentic OneBotAds",
  platform: "LinkedIn",
  audience: "SMEs and marketing teams",
  style: "modern editorial SaaS advertising with clean hierarchy and bold product storytelling",
  generateImage: false,
};

function buildImagePromptRequestMessage(form: ImagePromptFormValues): string {
  return [
    `Create an image prompt for ${form.productName}.`,
    `Platform: ${form.platform}.`,
    `Audience: ${form.audience}.`,
    `Style: ${form.style}.`,
    form.generateImage ? "Generate the image if the stack allows it." : "Prompt-only output is fine.",
  ].join(" ");
}

export function ImagePromptTab() {
  const resultsRef = useRef<HTMLDivElement | null>(null);
  const [form, setForm] = useState<ImagePromptFormValues>(defaultImageForm);
  const [result, setResult] = useState<ImageGenerationResponse | null>(null);
  const [intent, setIntent] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [isSubmitting, setIsSubmitting] = useState(false);

  useScrollIntoViewOnChange(resultsRef, result);

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

    try {
      const response = await runAssistant({ message: buildImagePromptRequestMessage(form) });

      if (!response.image) {
        setResult(null);
        setIntent(null);
        setError("The assistant responded, but it did not return image guidance.");
        return;
      }

      setResult(response.image);
      setIntent(response.intent);
    } catch (submitError) {
      setResult(null);
      setIntent(null);
      setError(submitError instanceof Error ? submitError.message : "Unable to generate the image prompt.");
    } finally {
      setIsSubmitting(false);
    }
  }

  return (
    <div className="tab-layout">
      <SectionIntro
        eyebrow="Image Prompt"
        title="Generate a visual brief"
        description="This stays useful even when image generation is disabled: prompt, negative prompt, alt text, file path, and preview when available."
      />

      {error ? (
        <p className="error-banner" role="alert">
          {error}
        </p>
      ) : null}

      <form className="brief-form" onSubmit={handleSubmit}>
        <div className="field-grid">
          <label>
            Product / Concept
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
            Style
            <input name="style" value={form.style} onChange={handleFieldChange} />
          </label>
        </div>

        <label className="checkbox-row">
          <input
            name="generateImage"
            type="checkbox"
            checked={form.generateImage}
            onChange={handleFieldChange}
          />
          Generate the image if the backend stack permits it.
        </label>

        <div className="form-actions">
          <button className="primary-action" type="submit" disabled={isSubmitting}>
            {isSubmitting ? "Generating..." : "Generate Image Prompt"}
          </button>
        </div>
      </form>

      {result ? (
        <div ref={resultsRef} className="result-stack">
          <div className="structured-grid">
            <article className="detail-card span-two">
              <p className="eyebrow">Image Prompt</p>
              <p>{result.image_prompt}</p>
            </article>

            <article className="detail-card span-two">
              <p className="eyebrow">Negative Prompt</p>
              <p>{result.negative_prompt}</p>
            </article>

            <article className="detail-card">
              <p className="eyebrow">Alt Text</p>
              <p>{result.alt_text}</p>
            </article>

            <article className="detail-card">
              <p className="eyebrow">Image Path</p>
              <p>{result.image_path ?? "No file was created."}</p>
            </article>

            <article className="detail-card">
              <p className="eyebrow">Status</p>
              <h3>{result.status}</h3>
            </article>

            <article className="detail-card">
              <p className="eyebrow">Intent</p>
              <h3>{intent ?? "Unknown"}</h3>
            </article>
          </div>

          {result.notes.length > 0 ? (
            <article className="warning-card">
              <p className="eyebrow">Image Notes</p>
              <ul className="bullet-list">
                {result.notes.map((note) => (
                  <li key={note}>{note}</li>
                ))}
              </ul>
            </article>
          ) : null}

          {canPreviewImage(result.image_path) ? (
            <article className="detail-card">
              <p className="eyebrow">Preview</p>
              <img className="image-preview" src={result.image_path ?? ""} alt={result.alt_text} />
            </article>
          ) : null}
        </div>
      ) : (
        <EmptyState
          title="No image brief yet"
          description="Provide the concept, platform, audience, and visual style to generate a prompt package with optional preview support."
        />
      )}
    </div>
  );
}
