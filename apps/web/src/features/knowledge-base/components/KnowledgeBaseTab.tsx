import { FormEvent, KeyboardEvent, useEffect, useLayoutEffect, useRef, useState } from "react";

import { useScrollIntoViewOnChange } from "../../../hooks/useScrollIntoViewOnChange";
import {
  getHealth,
  getRuntimeSummary,
  reindexKnowledgeBase,
  runAssistant,
} from "../../../services/api/onebot";
import type { ConversationTurn, HealthResponse, RuntimeSummary } from "../../../types/api";

type KnowledgeChatTurn = {
  id: string;
  question: string;
  answer?: string;
  error?: string;
  confidence?: string;
};

type KnowledgeChatStorage = {
  conversation: KnowledgeChatTurn[];
  useWebSearch: boolean;
  longAnswer: boolean;
};

const KNOWLEDGE_CHAT_STORAGE_KEY = "onebotads.knowledge-chat";

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
  return parts.map((part, index) => {
    if (part.startsWith("**") && part.endsWith("**")) {
      return (
        <strong key={index} style={{ color: "var(--foreground)" }}>
          {part.slice(2, -2)}
        </strong>
      );
    }
    if (part.startsWith("`") && part.endsWith("`")) {
      return (
        <code
          key={index}
          style={{
            backgroundColor: "var(--surface-sunken)",
            padding: "2px 4px",
            borderRadius: "4px",
          }}
        >
          {part.slice(1, -1)}
        </code>
      );
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
    if (/^[-*]\s+/.test(line)) {
      const previous = content[content.length - 1];
      const item = line.replace(/^[-*]\s+/, "").trim();
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

function buildConversationHistory(turns: KnowledgeChatTurn[]): ConversationTurn[] {
  return turns.flatMap((turn) => {
    const history: ConversationTurn[] = [{ role: "user", content: turn.question }];
    if (turn.answer) {
      history.push({ role: "assistant", content: turn.answer });
    }
    return history;
  });
}

function loadStoredKnowledgeChat(): KnowledgeChatStorage | null {
  if (typeof window === "undefined" || !window.localStorage) {
    return null;
  }

  try {
    const raw = window.localStorage.getItem(KNOWLEDGE_CHAT_STORAGE_KEY);
    if (!raw) {
      return null;
    }
    const parsed = JSON.parse(raw) as Partial<KnowledgeChatStorage>;
    return {
      conversation: Array.isArray(parsed.conversation) ? parsed.conversation : [],
      useWebSearch: typeof parsed.useWebSearch === "boolean" ? parsed.useWebSearch : true,
      longAnswer: typeof parsed.longAnswer === "boolean" ? parsed.longAnswer : true,
    };
  } catch {
    return null;
  }
}

function persistKnowledgeChat(payload: KnowledgeChatStorage) {
  if (typeof window === "undefined" || !window.localStorage) {
    return;
  }

  try {
    window.localStorage.setItem(KNOWLEDGE_CHAT_STORAGE_KEY, JSON.stringify(payload));
  } catch {
    // Ignore storage write failures to keep the chat usable.
  }
}

export function KnowledgeBaseTab() {
  const initialState = loadStoredKnowledgeChat();
  const composerRef = useRef<HTMLFormElement | null>(null);
  const buttonRef = useRef<HTMLButtonElement | null>(null);
  const inputRef = useRef<HTMLTextAreaElement | null>(null);
  const resultsRef = useRef<HTMLDivElement | null>(null);
  const previousComposerRectRef = useRef<DOMRect | null>(null);
  const previousButtonRectRef = useRef<DOMRect | null>(null);
  const [question, setQuestion] = useState("");
  const [conversation, setConversation] = useState<KnowledgeChatTurn[]>(
    initialState?.conversation ?? [],
  );
  const [useWebSearch, setUseWebSearch] = useState(initialState?.useWebSearch ?? true);
  const [longAnswer, setLongAnswer] = useState(initialState?.longAnswer ?? true);
  const [health, setHealth] = useState<HealthResponse | null>(null);
  const [runtime, setRuntime] = useState<RuntimeSummary | null>(null);
  const [runtimeMessage, setRuntimeMessage] = useState<string | null>(null);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [isReindexing, setIsReindexing] = useState(false);

  const hasQuestion = question.trim().length > 0;
  const hasConversationStarted = isSubmitting || conversation.length > 0;

  useScrollIntoViewOnChange(resultsRef, conversation);

  useEffect(() => {
    persistKnowledgeChat({
      conversation,
      useWebSearch,
      longAnswer,
    });
  }, [conversation, useWebSearch, longAnswer]);

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

        if (
          Math.abs(deltaX) > 1 ||
          Math.abs(deltaY) > 1 ||
          Math.abs(scaleX - 1) > 0.01 ||
          Math.abs(scaleY - 1) > 0.01
        ) {
          if (typeof element.animate !== "function") {
            storeRect.current = nextRect;
            return;
          }
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

  useEffect(() => {
    let cancelled = false;

    async function loadRuntimeContext() {
      try {
        const [nextHealth, nextRuntime] = await Promise.all([getHealth(), getRuntimeSummary()]);
        if (cancelled) {
          return;
        }

        setHealth(nextHealth);
        setRuntime(nextRuntime);
        setRuntimeMessage(nextHealth.rag_enabled ? "RAG ready" : "RAG unavailable");
      } catch {
        if (!cancelled) {
          setRuntimeMessage("Runtime details unavailable");
        }
      }
    }

    void loadRuntimeContext();

    return () => {
      cancelled = true;
    };
  }, []);

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

    const pendingTurn: KnowledgeChatTurn = {
      id: `${Date.now()}-${conversation.length}`,
      question: nextQuestion,
    };
    const conversationHistory = buildConversationHistory(conversation);

    setConversation((current) => [...current, pendingTurn]);
    setQuestion("");
    setIsSubmitting(true);

    try {
      const nextResponse = await runAssistant({
        message: nextQuestion,
        knowledge_base_only: true,
        conversation_history: conversationHistory,
        use_web_search: useWebSearch,
        min_answer_words: longAnswer ? 800 : undefined,
      });
      setConversation((current) =>
        current.map((turn) =>
          turn.id === pendingTurn.id
            ? {
                ...turn,
                answer: nextResponse.rag?.answer ?? "No grounded answer was returned.",
                confidence: nextResponse.rag?.confidence ?? "low",
              }
            : turn,
        ),
      );
    } catch (submitError) {
      setConversation((current) =>
        current.map((turn) =>
          turn.id === pendingTurn.id
            ? {
                ...turn,
                error:
                  submitError instanceof Error
                    ? submitError.message
                    : "Unable to query the knowledge base.",
              }
            : turn,
        ),
      );
    } finally {
      setIsSubmitting(false);
    }
  }

  async function handleReindex() {
    setRuntimeMessage(null);
    setIsReindexing(true);

    try {
      const result = await reindexKnowledgeBase();
      setRuntimeMessage(`Reindex complete: ${result.documents_indexed} documents`);
    } catch (reindexError) {
      setRuntimeMessage(
        reindexError instanceof Error
          ? reindexError.message
          : "Unable to reindex the knowledge base.",
      );
    } finally {
      setIsReindexing(false);
    }
  }

  return (
    <div className={`knowledge-chat ${hasConversationStarted ? "is-active" : ""}`}>
      <div className="knowledge-chat-spacer" />

      <div className="knowledge-chat-stage">
        <div className="knowledge-chat-shell">
          <header className={`knowledge-chat-header ${hasConversationStarted ? "is-hidden" : ""}`}>
            <p className="eyebrow">Knowledge Base Q&amp;A</p>
            <h2>Ask the local RAG workflow</h2>
          </header>

          {runtimeMessage || runtime || health ? (
            <div className={`knowledge-chat-runtime ${hasConversationStarted ? "is-inline" : ""}`}>
              <div className="knowledge-chat-runtime-copy">
                <p className="eyebrow">Knowledge Base Runtime</p>
                <p>{runtimeMessage ?? "Runtime ready"}</p>
                {runtime ? (
                  <p>
                    Index source: {runtime.knowledge_base_directory} | model:{" "}
                    {runtime.ollama_embedding_model}
                  </p>
                ) : null}
              </div>

              <div style={{ display: "flex", gap: "12px" }}>
                {conversation.length > 0 ? (
                  <button
                    className="secondary-action"
                    type="button"
                    onClick={() => setConversation([])}
                  >
                    New chat
                  </button>
                ) : null}

                <button
                  className="secondary-action"
                  type="button"
                  onClick={() => {
                    void handleReindex();
                  }}
                  disabled={isReindexing}
                >
                  {isReindexing ? "Reindexing..." : "Reindex KB"}
                </button>
              </div>
            </div>
          ) : null}

          {conversation.length > 0 ? (
            <div ref={resultsRef} className="knowledge-chat-results">
              {conversation.map((turn) => (
                <div key={turn.id}>
                  <article className="knowledge-chat-message knowledge-chat-message-user">
                    <p>{turn.question}</p>
                  </article>

                  {turn.error ? (
                    <article className="knowledge-chat-error" role="alert">
                      <p>{turn.error}</p>
                    </article>
                  ) : null}

                  {turn.answer ? (
                    <article className="knowledge-chat-answer-block">
                      <div className="knowledge-chat-answer">{renderKnowledgeAnswer(turn.answer)}</div>
                      {turn.confidence ? (
                        <p
                          style={{
                            marginTop: "12px",
                            color: "var(--foreground-muted)",
                            fontSize: "0.85rem",
                          }}
                        >
                          Confidence: {turn.confidence}
                        </p>
                      ) : null}
                    </article>
                  ) : null}
                </div>
              ))}
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
            placeholder="Ask a grounded follow-up question"
            aria-label="Question"
          />

          <div
            style={{
              display: "flex",
              alignItems: "center",
              gap: "16px",
              alignSelf: "flex-end",
              flexWrap: "wrap",
            }}
          >
            <label
              style={{
                display: "flex",
                alignItems: "center",
                gap: "6px",
                color: "var(--foreground-muted)",
                fontSize: "0.875rem",
                cursor: "pointer",
                userSelect: "none",
              }}
            >
              <input
                type="checkbox"
                checked={useWebSearch}
                onChange={(event) => setUseWebSearch(event.target.checked)}
                style={{ cursor: "pointer", width: "16px", height: "16px" }}
              />
              Web Search
            </label>

            <label
              style={{
                display: "flex",
                alignItems: "center",
                gap: "6px",
                color: "var(--foreground-muted)",
                fontSize: "0.875rem",
                cursor: "pointer",
                userSelect: "none",
              }}
            >
              <input
                type="checkbox"
                checked={longAnswer}
                onChange={(event) => setLongAnswer(event.target.checked)}
                style={{ cursor: "pointer", width: "16px", height: "16px" }}
              />
              Long answer (800+ words)
            </label>

            <button
              ref={buttonRef}
              className={`knowledge-chat-submit ${hasConversationStarted ? "is-compact" : ""}`}
              type="submit"
              disabled={!hasQuestion || isSubmitting}
              aria-busy={isSubmitting}
              aria-label={isSubmitting ? "Asking" : hasConversationStarted ? "Ask question" : "Ask"}
            >
              {isSubmitting ? (
                <span className="button-spinner" aria-hidden="true" />
              ) : hasConversationStarted ? (
                <ArrowUpIcon />
              ) : null}
              <span className="knowledge-chat-submit-label">
                {isSubmitting ? "Asking..." : "Ask"}
              </span>
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}
