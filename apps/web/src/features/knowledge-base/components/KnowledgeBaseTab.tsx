import { FormEvent, KeyboardEvent, useEffect, useLayoutEffect, useRef, useState } from "react";

import { useScrollIntoViewOnChange } from "../../../hooks/useScrollIntoViewOnChange";
import {
  runAssistant,
} from "../../../services/api/onebot";
import type {
  AssistantResponse,
} from "../../../types/api";

function ArrowUpIcon() {
  return (
    <svg viewBox="0 0 24 24" aria-hidden="true" focusable="false">
      <path d="M12 19V5" />
      <path d="m6 11 6-6 6 6" />
    </svg>
  );
}

function formatText(text: string) {
  const parts = text.split(/(\*\*.*?\*\*|`.*?`)/g);
  return parts.map((part, i) => {
    if (part.startsWith('**') && part.endsWith('**')) {
      return <strong key={i} style={{ color: "var(--foreground)" }}>{part.slice(2, -2)}</strong>;
    }
    if (part.startsWith('`') && part.endsWith('`')) {
      return <code key={i} style={{ backgroundColor: "var(--surface-sunken)", padding: "2px 4px", borderRadius: "4px" }}>{part.slice(1, -1)}</code>;
    }
    return part;
  });
}

function renderKnowledgeAnswer(answer: string) {
  const lines = answer
    .split(/\r?\n/)
    .map((line) => line.trim())
    .filter((line) => line.length > 0);

  const content: Array<
    { type: "paragraph"; text: string } | { type: "list"; items: string[] }
  > = [];

  for (const line of lines) {
    if (/^[-*•]\s+/.test(line)) {
      const previous = content[content.length - 1];
      const item = line.replace(/^[-*•]\s+/, "").trim();
      if (previous?.type === "list") {
        previous.items.push(item);
      } else {
        content.push({ type: "list", items: [item] });
      }
      continue;
    }

    content.push({ type: "paragraph", text: line });
  }

  return content.map((block, index) =>
    block.type === "paragraph" ? (
      <p key={`paragraph-${index}`}>{formatText(block.text)}</p>
    ) : (
      <ul key={`list-${index}`} className="knowledge-chat-answer-list">
        {block.items.map((item) => (
          <li key={item}>{formatText(item)}</li>
        ))}
      </ul>
    ),
  );
}

export function KnowledgeBaseTab() {
  const composerRef = useRef<HTMLFormElement | null>(null);
  const buttonRef = useRef<HTMLButtonElement | null>(null);
  const inputRef = useRef<HTMLTextAreaElement | null>(null);
  const resultsRef = useRef<HTMLDivElement | null>(null);
  const previousComposerRectRef = useRef<DOMRect | null>(null);
  const previousButtonRectRef = useRef<DOMRect | null>(null);
  const [question, setQuestion] = useState("");
  const [submittedQuestion, setSubmittedQuestion] = useState("");
  const [useWebSearch, setUseWebSearch] = useState(true);
  const [response, setResponse] = useState<AssistantResponse | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [isSubmitting, setIsSubmitting] = useState(false);

  const hasQuestion = question.trim().length > 0;
  const hasConversationStarted =
    isSubmitting ||
    submittedQuestion.trim().length > 0 ||
    Boolean(response?.rag) ||
    Boolean(error);

  useScrollIntoViewOnChange(resultsRef, response?.rag ?? error);

  useLayoutEffect(() => {
    const animateFlip = (
      element: HTMLElement | null,
      previousRect: DOMRect | null,
      storeRect: { current: DOMRect | null },
    ) => {
      if (!element) {
        storeRect.current = null;
        return;
      }

      const nextRect = element.getBoundingClientRect();
      if (previousRect) {
        const deltaX = previousRect.left - nextRect.left;
        const deltaY = previousRect.top - nextRect.top;
        const scaleX = previousRect.width / Math.max(nextRect.width, 1);
        const scaleY = previousRect.height / Math.max(nextRect.height, 1);

        if (Math.abs(deltaX) > 1 || Math.abs(deltaY) > 1 || Math.abs(scaleX - 1) > 0.01 || Math.abs(scaleY - 1) > 0.01) {
          element.animate(
            [
              {
                transform: `translate(${deltaX}px, ${deltaY}px) scale(${scaleX}, ${scaleY})`,
                transformOrigin: "top left",
              },
              {
                transform: "translate(0, 0) scale(1, 1)",
                transformOrigin: "top left",
              },
            ],
            {
              duration: 420,
              easing: "cubic-bezier(0.22, 1, 0.36, 1)",
            },
          );
        }
      }

      storeRect.current = nextRect;
    };

    animateFlip(composerRef.current, previousComposerRectRef.current, previousComposerRectRef);
    animateFlip(buttonRef.current, previousButtonRectRef.current, previousButtonRectRef);
  }, [hasConversationStarted, isSubmitting]);

  useLayoutEffect(() => {
    const input = inputRef.current;
    if (!input) {
      return;
    }

    input.style.height = "0px";
    input.style.height = `${Math.max(input.scrollHeight, hasConversationStarted ? 58 : 88)}px`;
  }, [question, hasConversationStarted]);

  function handleQuestionKeyDown(event: KeyboardEvent<HTMLTextAreaElement>) {
    if (event.key !== "Enter" || event.shiftKey) {
      return;
    }

    event.preventDefault();

    if (!hasQuestion || isSubmitting) {
      return;
    }

    event.currentTarget.form?.requestSubmit();
  }

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();

    const nextQuestion = question.trim();
    if (!nextQuestion) {
      return;
    }

    setError(null);
    setResponse(null);
    setSubmittedQuestion(nextQuestion);
    setQuestion("");
    setIsSubmitting(true);

    try {
      const nextResponse = await runAssistant({ 
        message: nextQuestion,
        use_web_search: useWebSearch,
      });
      setResponse(nextResponse);
    } catch (submitError) {
      setError(submitError instanceof Error ? submitError.message : "Unable to query the knowledge base.");
    } finally {
      setIsSubmitting(false);
    }
  }

  return (
    <div className={`knowledge-chat ${hasConversationStarted ? "is-active" : ""}`}>
      <div className="knowledge-chat-spacer" />

      <div className="knowledge-chat-stage">
        <div className="knowledge-chat-shell">
          <header className={`knowledge-chat-header ${hasConversationStarted ? "is-hidden" : ""}`}>
            <p className="eyebrow">Knowledge Base Q&A</p>
            <h2>Ask the local RAG workflow</h2>
          </header>

          {submittedQuestion || response?.rag || error ? (
            <div ref={resultsRef} className="knowledge-chat-results">
              {submittedQuestion ? (
                <article className="knowledge-chat-message knowledge-chat-message-user">
                  <p>{submittedQuestion}</p>
                </article>
              ) : null}

              {error ? (
                <article className="knowledge-chat-error" role="alert">
                  <p>{error}</p>
                </article>
              ) : null}

              {response?.rag ? (
                <article className="knowledge-chat-answer-block">
                  <div className="knowledge-chat-answer">{renderKnowledgeAnswer(response.rag.answer)}</div>
                </article>
              ) : null}
            </div>
          ) : null}
        </div>

        <form
          ref={composerRef}
          className={`knowledge-chat-composer ${hasConversationStarted ? "is-compact" : ""}`}
          onSubmit={handleSubmit}
        >
          <textarea
            ref={inputRef}
            className="knowledge-chat-input"
            value={question}
            onChange={(event) => setQuestion(event.target.value)}
            onKeyDown={handleQuestionKeyDown}
            rows={1}
            placeholder="Question"
            aria-label="Question"
          />

          <div style={{ display: "flex", alignItems: "center", gap: "16px", alignSelf: "flex-end" }}>
            <label style={{ display: "flex", alignItems: "center", gap: "6px", color: "var(--foreground-muted)", fontSize: "0.875rem", cursor: "pointer", userSelect: "none" }}>
              <input
                type="checkbox"
                checked={useWebSearch}
                onChange={(e) => setUseWebSearch(e.target.checked)}
                style={{ cursor: "pointer", width: "16px", height: "16px" }}
              />
              Web Search
            </label>

            <button
              ref={buttonRef}
              className={`knowledge-chat-submit ${hasConversationStarted ? "is-compact" : ""}`}
              type="submit"
              disabled={!hasQuestion || isSubmitting}
              aria-busy={isSubmitting}
              aria-label={isSubmitting ? "Asking" : hasConversationStarted ? "Ask question" : "Ask"}
            >
              {isSubmitting ? <span className="button-spinner" aria-hidden="true" /> : hasConversationStarted ? <ArrowUpIcon /> : null}
              <span className="knowledge-chat-submit-label">{isSubmitting ? "Asking..." : "Ask"}</span>
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}
