from textwrap import dedent

from onebot_ads.agents._llm import build_chat_model, extract_json_payload
from onebot_ads.core.config import Settings
from onebot_ads.rag.knowledge_base import KnowledgeBaseService
from onebot_ads.schemas.campaigns import RAGAgentResponse

SYSTEM_PROMPT = """
You are the RAG Marketing Knowledge Agent of Agentic OneBotAds.

Your role is to answer using the private marketing knowledge base.

Use this agent when the task requires:
- brand guidelines
- product descriptions
- marketing strategy
- audience personas
- platform advertising rules
- previous campaign examples
- tone of voice
- approved messaging
- prohibited claims
- positioning and value proposition

You must query the RAG tool before answering.

Rules:
1. Do not invent brand facts.
2. If the knowledge base does not contain enough information, say what is missing.
3. Return concise but useful context for downstream agents.
4. When possible, return the answer as structured JSON with:
   - answer
   - relevant_context
   - source_documents
   - confidence
""".strip()


class RAGMarketingKnowledgeAgent:
    def __init__(self, settings: Settings, knowledge_base: KnowledgeBaseService) -> None:
        self.settings = settings
        self.knowledge_base = knowledge_base

    def run(self, question: str) -> RAGAgentResponse:
        snippets = self.knowledge_base.retrieve(question, top_k=4)
        if not snippets:
            return RAGAgentResponse(
                answer=(
                    "The knowledge base does not contain enough grounded "
                    "information for this request."
                ),
                relevant_context=[],
                source_documents=[],
                confidence="low",
            )

        if self.settings.enable_live_llm:
            try:
                return self._summarize_with_llm(question, snippets)
            except Exception:
                pass

        return RAGAgentResponse(
            answer=" ".join(snippet.excerpt for snippet in snippets[:2]).strip(),
            relevant_context=[snippet.excerpt for snippet in snippets[:3]],
            source_documents=list(dict.fromkeys(snippet.source for snippet in snippets)),
            confidence="medium" if len(snippets) > 1 else "low",
        )

    def _summarize_with_llm(self, question: str, snippets) -> RAGAgentResponse:
        from langchain_core.prompts import ChatPromptTemplate

        prompt = ChatPromptTemplate.from_messages(
            [
                ("system", SYSTEM_PROMPT),
                (
                    "human",
                    dedent(
                        """
                        Question: {question}

                        Retrieved snippets:
                        {snippets}

                        Return only valid JSON with keys:
                        answer, relevant_context, source_documents, confidence
                        """
                    ).strip(),
                ),
            ]
        )
        llm = build_chat_model(self.settings)
        response = llm.invoke(
            prompt.format_messages(
                question=question,
                snippets="\n".join(f"- {item.source}: {item.excerpt}" for item in snippets),
            )
        )
        payload = extract_json_payload(getattr(response, "content", str(response)))
        return RAGAgentResponse.model_validate(payload)
