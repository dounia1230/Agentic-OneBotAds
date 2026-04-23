import re
from pathlib import Path
from textwrap import dedent

from onebot_ads.agents._llm import build_chat_model, extract_json_payload
from onebot_ads.core.config import Settings
from onebot_ads.rag.knowledge_base import KnowledgeBaseService
from onebot_ads.schemas.campaigns import RAGAgentResponse
from onebot_ads.schemas.knowledge import KnowledgeScope

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

    def run(
        self,
        question: str,
        knowledge_scope: KnowledgeScope | None = None,
    ) -> RAGAgentResponse:
        snippets = self.knowledge_base.retrieve(question, top_k=4, scope=knowledge_scope)
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

        source_documents = list(dict.fromkeys(snippet.source for snippet in snippets))
        relevant_context = self._build_relevant_context(snippets)
        return RAGAgentResponse(
            answer=self._build_fallback_answer(question, source_documents, relevant_context),
            relevant_context=relevant_context,
            source_documents=source_documents,
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

    @staticmethod
    def _clean_excerpt(excerpt: str) -> str:
        return " ".join(excerpt.split()).strip()

    def _build_relevant_context(self, snippets) -> list[str]:
        context: list[str] = []
        seen_sources: set[str] = set()
        for snippet in snippets:
            if snippet.source in seen_sources:
                continue
            seen_sources.add(snippet.source)
            context.append(self._clean_excerpt(snippet.excerpt))
            if len(context) == 3:
                break
        return context

    def _build_fallback_answer(
        self,
        question: str,
        source_documents: list[str],
        relevant_context: list[str],
    ) -> str:
        lowered = question.lower()
        if any(token in lowered for token in ["persona", "audience", "tone", "brand", "guideline"]):
            brand_advice = self._build_brand_advice_fallback(lowered)
            if brand_advice:
                return brand_advice

        summary_lines = ["Grounded context found in the knowledge base:"]
        for source, excerpt in zip(source_documents, relevant_context, strict=False):
            summary_lines.append(f"- {source}: {excerpt}")
        return "\n".join(summary_lines)

    def _build_brand_advice_fallback(self, question: str) -> str:
        brand_text = self._read_knowledge_file("brand_guidelines.md")
        audience_text = self._read_knowledge_file("audience_personas.md")

        lines: list[str] = []

        if audience_text and any(token in question for token in ["persona", "audience"]):
            personas = re.findall(r"^## Persona \d+: (.+)$", audience_text, flags=re.MULTILINE)
            if personas:
                lines.append("Main audience personas:")
                lines.append(f"- {', '.join(personas)}")

        if brand_text and any(token in question for token in ["tone", "brand", "guideline"]):
            brand_role = self._extract_section_paragraph(brand_text, "Brand Role")
            voice_attributes = self._extract_section_bullets(brand_text, "Voice Attributes", limit=5)
            tone_rules = self._extract_section_bullets(brand_text, "Tone Rules", limit=4)
            avoid_terms = self._extract_section_bullets(brand_text, "Avoid", limit=5)

            if brand_role:
                lines.append("Brand role:")
                lines.append(f"- {brand_role}")
            if voice_attributes:
                lines.append("Voice attributes:")
                lines.append(f"- {', '.join(voice_attributes)}")
            if tone_rules:
                lines.append("Tone rules:")
                for item in tone_rules:
                    lines.append(f"- {item}")
            if avoid_terms:
                lines.append("Avoid:")
                lines.append(f"- {', '.join(avoid_terms)}")

        if not lines:
            return ""

        lines.append("Sources:")
        lines.append("- audience_personas.md")
        lines.append("- brand_guidelines.md")
        return "\n".join(lines)

    def _read_knowledge_file(self, source_name: str) -> str:
        path = Path(self.settings.knowledge_base_directory) / source_name
        if not path.exists():
            return ""
        return path.read_text(encoding="utf-8")

    @staticmethod
    def _extract_section_paragraph(markdown: str, heading: str) -> str:
        match = re.search(
            rf"^## {re.escape(heading)}\s*$\n+(.*?)(?=^## |\Z)",
            markdown,
            flags=re.MULTILINE | re.DOTALL,
        )
        if not match:
            return ""
        body = match.group(1).strip()
        for line in body.splitlines():
            cleaned = line.strip()
            if cleaned and not cleaned.startswith("-") and not cleaned.startswith("#"):
                return cleaned
        return ""

    @staticmethod
    def _extract_section_bullets(markdown: str, heading: str, *, limit: int) -> list[str]:
        match = re.search(
            rf"^## {re.escape(heading)}\s*$\n+(.*?)(?=^## |\Z)",
            markdown,
            flags=re.MULTILINE | re.DOTALL,
        )
        if not match:
            return []
        bullets: list[str] = []
        for line in match.group(1).splitlines():
            cleaned = line.strip()
            if cleaned.startswith("- "):
                bullets.append(cleaned[2:].strip())
            if len(bullets) == limit:
                break
        return bullets
