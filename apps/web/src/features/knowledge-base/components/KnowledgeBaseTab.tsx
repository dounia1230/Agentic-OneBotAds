import { FormEvent, useState } from "react";

import { EmptyState } from "../../../components/ui/EmptyState";
import { SectionIntro } from "../../../components/ui/SectionIntro";
import { runAssistant } from "../../../services/api/onebot";
import type { AssistantResponse } from "../../../types/api";

const defaultQuestion =
  "What guidance does the knowledge base give for tone and messaging?";

export function KnowledgeBaseTab() {
  const [question, setQuestion] = useState(defaultQuestion);
  const [response, setResponse] = useState<AssistantResponse | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [isSubmitting, setIsSubmitting] = useState(false);

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setError(null);
    setIsSubmitting(true);

    try {
      const nextResponse = await runAssistant({ message: question });
      setResponse(nextResponse);
    } catch (submitError) {
      setResponse(null);
      setError(submitError instanceof Error ? submitError.message : "Unable to query the knowledge base.");
    } finally {
      setIsSubmitting(false);
    }
  }

  return (
    <div className="tab-layout">
      <SectionIntro
        eyebrow="Knowledge Base Q&A"
        title="Ask the local RAG workflow"
        description="Ask product, tone, audience, or campaign questions and surface the grounded answer plus source signals when the assistant can provide them."
      />

      {error ? (
        <p className="error-banner" role="alert">
          {error}
        </p>
      ) : null}

      <form className="brief-form" onSubmit={handleSubmit}>
        <label>
          Question
          <textarea value={question} onChange={(event) => setQuestion(event.target.value)} rows={6} />
        </label>

        <div className="form-actions">
          <button className="primary-action" type="submit" disabled={isSubmitting}>
            {isSubmitting ? "Asking..." : "Ask"}
          </button>
        </div>
      </form>

      {response?.rag ? (
        <div className="result-stack">
          <article className="detail-card">
            <p className="eyebrow">Answer</p>
            <p>{response.rag.answer}</p>
          </article>

          <div className="structured-grid">
            <article className="detail-card">
              <p className="eyebrow">Confidence</p>
              <h3>{response.rag.confidence}</h3>
            </article>

            <article className="detail-card">
              <p className="eyebrow">Intent</p>
              <h3>{response.intent}</h3>
            </article>

            <article className="detail-card span-two">
              <p className="eyebrow">Relevant Context</p>
              <ul className="bullet-list">
                {response.rag.relevant_context.map((snippet) => (
                  <li key={snippet}>{snippet}</li>
                ))}
              </ul>
            </article>

            <article className="detail-card span-two">
              <p className="eyebrow">Source Documents</p>
              <ul className="bullet-list">
                {response.rag.source_documents.map((document) => (
                  <li key={document}>{document}</li>
                ))}
              </ul>
            </article>
          </div>
        </div>
      ) : (
        <EmptyState
          title="No answer yet"
          description="Ask a question about messaging, positioning, offers, or prior knowledge-base content."
        />
      )}
    </div>
  );
}
