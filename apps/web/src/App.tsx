import { ChangeEvent, FormEvent, useEffect, useMemo, useState, useTransition } from "react";

import { createCampaignDraft, fetchRuntime } from "./api";
import type { CampaignBriefPayload, CampaignDraftResponse, RuntimeSummary } from "./types";

const CHANNEL_OPTIONS = [
  { value: "meta", label: "Meta" },
  { value: "google", label: "Google" },
  { value: "linkedin", label: "LinkedIn" },
  { value: "email", label: "Email" },
  { value: "landing_page", label: "Landing Page" },
];

type BriefFormState = {
  productName: string;
  audience: string;
  goal: string;
  tone: string;
  offer: string;
  keyPoints: string;
  brandConstraints: string;
  landingPageUrl: string;
  sourceContextQuery: string;
  generateImagePrompt: boolean;
  channels: string[];
};

const defaultBrief: BriefFormState = {
  productName: "Agentic OneBotAds",
  audience: "SME marketing teams and campaign managers",
  goal: "Increase qualified demo bookings",
  tone: "clear, credible, conversion-focused",
  offer: "7-day pilot campaign setup",
  keyPoints: "Local-first workflow\nChannel-ready ad drafts\nReusable brand context",
  brandConstraints: "Avoid hype claims\nKeep copy concrete\nLead with operational value",
  landingPageUrl: "",
  sourceContextQuery: "local-first AI campaign drafting for SME marketing teams",
  generateImagePrompt: true,
  channels: ["meta", "linkedin"],
};

function linesToArray(value: string): string[] {
  return value
    .split("\n")
    .map((line) => line.trim())
    .filter(Boolean);
}

function runtimeLabel(runtime: RuntimeSummary | null): string {
  if (!runtime) {
    return "Backend unavailable";
  }
  return `${runtime.environment} | ${runtime.ollama_chat_model}`;
}

export default function App() {
  const [form, setForm] = useState<BriefFormState>(defaultBrief);
  const [runtime, setRuntime] = useState<RuntimeSummary | null>(null);
  const [draft, setDraft] = useState<CampaignDraftResponse | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [isLoadingRuntime, setIsLoadingRuntime] = useState(true);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [isPending, startTransition] = useTransition();

  useEffect(() => {
    let active = true;

    fetchRuntime()
      .then((response) => {
        if (active) {
          setRuntime(response);
        }
      })
      .catch(() => {
        if (active) {
          setRuntime(null);
        }
      })
      .finally(() => {
        if (active) {
          setIsLoadingRuntime(false);
        }
      });

    return () => {
      active = false;
    };
  }, []);

  const selectedChannels = useMemo(
    () => CHANNEL_OPTIONS.filter((option) => form.channels.includes(option.value)),
    [form.channels],
  );

  function updateField(event: ChangeEvent<HTMLInputElement | HTMLTextAreaElement>) {
    const target = event.target;
    const { name, type } = target;
    const value = type === "checkbox" && target instanceof HTMLInputElement ? target.checked : target.value;

    setForm((current) => ({
      ...current,
      [name]: value,
    }));
  }

  function toggleChannel(channel: string) {
    setForm((current) => {
      const exists = current.channels.includes(channel);
      return {
        ...current,
        channels: exists
          ? current.channels.filter((item) => item !== channel)
          : [...current.channels, channel],
      };
    });
  }

  async function submitBrief(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setError(null);
    setIsSubmitting(true);

    const payload: CampaignBriefPayload = {
      product_name: form.productName,
      audience: form.audience,
      goal: form.goal,
      channels: form.channels,
      tone: form.tone,
      offer: form.offer || undefined,
      key_points: linesToArray(form.keyPoints),
      brand_constraints: linesToArray(form.brandConstraints),
      landing_page_url: form.landingPageUrl || undefined,
      source_context_query: form.sourceContextQuery || undefined,
      generate_image_prompt: form.generateImagePrompt,
    };

    try {
      const response = await createCampaignDraft(payload);
      startTransition(() => {
        setDraft(response);
      });
    } catch (submitError) {
      setError(submitError instanceof Error ? submitError.message : "Unable to generate campaign draft.");
    } finally {
      setIsSubmitting(false);
    }
  }

  return (
    <div className="shell">
      <header className="hero panel">
        <div className="hero-copy">
          <p className="eyebrow">Agentic OneBotAds</p>
          <h1>Campaign Control Room</h1>
          <p className="hero-text">
            Draft local-first ad campaigns with reusable brand context, fast operator review, and a backend
            already shaped for LangChain, LlamaIndex, and Ollama.
          </p>
        </div>
        <div className="hero-metrics">
          <div className="metric">
            <span>Runtime</span>
            <strong>{isLoadingRuntime ? "Checking..." : runtimeLabel(runtime)}</strong>
          </div>
          <div className="metric">
            <span>Channels</span>
            <strong>{selectedChannels.map((item) => item.label).join(", ") || "Choose channels"}</strong>
          </div>
          <div className="metric">
            <span>Mode</span>
            <strong>{draft ? `${draft.provider} | ${draft.mode}` : "Awaiting brief"}</strong>
          </div>
        </div>
      </header>

      <main className="workspace">
        <section className="panel composer">
          <div className="section-header">
            <div>
              <p className="eyebrow">Brief Composer</p>
              <h2>Define the campaign</h2>
            </div>
            <p className="section-copy">Keep the brief sharp. The API converts it into structured draft output.</p>
          </div>

          <form className="brief-form" onSubmit={submitBrief}>
            <div className="field-grid">
              <label>
                Product
                <input name="productName" value={form.productName} onChange={updateField} />
              </label>

              <label>
                Audience
                <input name="audience" value={form.audience} onChange={updateField} />
              </label>

              <label>
                Goal
                <input name="goal" value={form.goal} onChange={updateField} />
              </label>

              <label>
                Tone
                <input name="tone" value={form.tone} onChange={updateField} />
              </label>

              <label className="field-span-2">
                Offer
                <input name="offer" value={form.offer} onChange={updateField} />
              </label>

              <label className="field-span-2">
                Context Query
                <input name="sourceContextQuery" value={form.sourceContextQuery} onChange={updateField} />
              </label>

              <label className="field-span-2">
                Landing Page URL
                <input
                  name="landingPageUrl"
                  placeholder="https://example.com"
                  value={form.landingPageUrl}
                  onChange={updateField}
                />
              </label>

              <label className="field-span-2">
                Key Points
                <textarea name="keyPoints" rows={5} value={form.keyPoints} onChange={updateField} />
              </label>

              <label className="field-span-2">
                Brand Constraints
                <textarea
                  name="brandConstraints"
                  rows={5}
                  value={form.brandConstraints}
                  onChange={updateField}
                />
              </label>
            </div>

            <div className="channel-row">
              {CHANNEL_OPTIONS.map((option) => {
                const active = form.channels.includes(option.value);
                return (
                  <button
                    key={option.value}
                    className={`channel-pill ${active ? "active" : ""}`}
                    type="button"
                    onClick={() => toggleChannel(option.value)}
                  >
                    {option.label}
                  </button>
                );
              })}
            </div>

            <label className="checkbox-row">
              <input
                name="generateImagePrompt"
                type="checkbox"
                checked={form.generateImagePrompt}
                onChange={updateField}
              />
              Include an image-generation prompt in the draft response.
            </label>

            <div className="form-actions">
              <button className="primary-action" type="submit" disabled={isSubmitting || form.channels.length === 0}>
                {isSubmitting ? "Generating..." : "Generate campaign draft"}
              </button>
              <p>{isPending ? "Rendering draft..." : "Results stay local to the running stack."}</p>
            </div>

            {error ? <p className="error-banner">{error}</p> : null}
          </form>
        </section>

        <section className="results-column">
          <div className="panel panel-dark">
            <div className="section-header">
              <div>
                <p className="eyebrow">System Snapshot</p>
                <h2>Local stack status</h2>
              </div>
            </div>
            <dl className="stats-grid">
              <div>
                <dt>Backend</dt>
                <dd>{runtime ? runtime.api_prefix : "Unavailable"}</dd>
              </div>
              <div>
                <dt>Chat model</dt>
                <dd>{runtime?.ollama_chat_model ?? "Not detected"}</dd>
              </div>
              <div>
                <dt>Embedding model</dt>
                <dd>{runtime?.ollama_embedding_model ?? "Not detected"}</dd>
              </div>
              <div>
                <dt>RAG</dt>
                <dd>{runtime?.rag_enabled ? "Enabled" : "Disabled"}</dd>
              </div>
            </dl>
          </div>

          <div className="panel draft-panel">
            <div className="section-header">
              <div>
                <p className="eyebrow">Generated Draft</p>
                <h2>Review before export</h2>
              </div>
            </div>

            {draft ? (
              <div className="draft-stack">
                <p className="summary-copy">{draft.summary}</p>

                <div className="variant-list">
                  {draft.variants.map((variant) => (
                    <article className="variant-card" key={`${variant.channel}-${variant.headline}`}>
                      <div className="variant-head">
                        <span>{variant.channel}</span>
                        <strong>{variant.cta}</strong>
                      </div>
                      <h3>{variant.headline}</h3>
                      <p>{variant.primary_text}</p>
                      <small>{variant.rationale}</small>
                    </article>
                  ))}
                </div>

                {draft.image_prompt ? (
                  <div className="prompt-card">
                    <p className="eyebrow">Image Prompt</p>
                    <p>{draft.image_prompt.prompt}</p>
                    <small>Provider boundary: {draft.image_prompt.provider}</small>
                  </div>
                ) : null}

                {draft.used_context.length > 0 ? (
                  <div className="context-card">
                    <p className="eyebrow">Retrieved Context</p>
                    <ul>
                      {draft.used_context.map((snippet) => (
                        <li key={`${snippet.source}-${snippet.excerpt.slice(0, 24)}`}>
                          <strong>{snippet.source}</strong>
                          <span>{snippet.excerpt}</span>
                        </li>
                      ))}
                    </ul>
                  </div>
                ) : null}

                {draft.warnings.length > 0 ? (
                  <div className="warning-card">
                    <p className="eyebrow">Warnings</p>
                    <ul>
                      {draft.warnings.map((warning) => (
                        <li key={warning}>{warning}</li>
                      ))}
                    </ul>
                  </div>
                ) : null}
              </div>
            ) : (
              <div className="empty-state">
                <h3>No draft yet</h3>
                <p>
                  Submit the brief to generate structured ad variants, a retrieval summary, and an optional image
                  prompt.
                </p>
              </div>
            )}
          </div>
        </section>
      </main>
    </div>
  );
}
