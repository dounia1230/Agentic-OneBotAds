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
3. Return a full but readable answer. Prefer 1 short intro paragraph plus 4-6 bullets when the
   question asks for recommendations, angles, strategy, positioning, audience, tone, or offers.
4. When the context supports it, explain the recommendation, not just the conclusion.
5. Use concrete marketing language and practical next steps.
6. If the question asks for "best angles", "how to market", or similar strategy guidance, cover
   audience, positioning, offer, proof, tone, and CTA when relevant.
7. Keep the answer grounded in the retrieved context and clearly note gaps when information is thin.
8. Do not mention file names, source documents, or where the information came from inside the answer text.
9. When possible, return the answer as structured JSON with:
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
        use_web_search: bool = False,
        min_answer_words: int | None = None,
    ) -> RAGAgentResponse:
        snippets = self.knowledge_base.retrieve(
            question,
            top_k=self._resolve_top_k(min_answer_words, use_web_search),
            scope=knowledge_scope,
        )

        if use_web_search:
            try:
                from langchain_community.utilities import SerpAPIWrapper
                if not self.settings.serpapi_api_key:
                    raise ValueError("SERPAPI_API_KEY is missing")
                search = SerpAPIWrapper(serpapi_api_key=self.settings.serpapi_api_key)
                search_result = search.run(question)
                if isinstance(search_result, str) and search_result.startswith("[") and search_result.endswith("]"):
                    import ast
                    try:
                        parsed = ast.literal_eval(search_result)
                        if isinstance(parsed, list):
                            search_result = "\n".join(f"- {str(item)}" for item in parsed)
                    except Exception:
                        pass
                Snippet = type("Snippet", (), {"source": "Web Search (SerpAPI)", "excerpt": search_result})
                snippets.insert(0, Snippet())
            except Exception as e:
                import logging
                logging.getLogger(__name__).warning(f"Web search failed: {e}")

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
                return self._sanitize_response(
                    self._summarize_with_llm(question, snippets, min_answer_words)
                )
            except Exception as e:
                import logging
                logging.getLogger(__name__).warning(f"LLM summary failed: {e}")
                try:
                    return self._sanitize_response(
                        self._summarize_with_plain_llm(
                            question,
                            snippets,
                            min_answer_words=min_answer_words,
                        )
                    )
                except Exception as plain_exc:
                    logging.getLogger(__name__).warning(
                        f"Plain-text LLM summary failed: {plain_exc}"
                    )
                    pass

        source_documents = list(dict.fromkeys(snippet.source for snippet in snippets))
        relevant_context = self._build_relevant_context(snippets)
        return self._sanitize_response(
            RAGAgentResponse(
                answer=self._build_fallback_answer(
                    question,
                    relevant_context,
                    min_answer_words=min_answer_words,
                ),
                relevant_context=relevant_context,
                source_documents=source_documents,
                confidence="medium" if len(snippets) > 1 else "low",
            )
        )

    def _summarize_with_llm(self, question: str, snippets, min_answer_words: int | None) -> RAGAgentResponse:
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

                        Return ONLY a raw JSON object. Do not wrap it in markdown block quotes. Use these exact keys:
                        - "answer" (string)
                        - "relevant_context" (array of strings)
                        - "source_documents" (array of strings)
                        - "confidence" (string, must be "high", "medium", or "low")

                        Writing expectations:
                        - Make the answer fuller than a single short paragraph when context allows.
                        - For strategy or recommendation questions, prefer 1 short intro paragraph
                          followed by 4-6 concrete bullets.
                        - Explain why each recommendation fits the context.
                        - Keep the answer grounded and specific rather than generic.
                        - Minimum answer words: {min_answer_words}
                        - If a minimum word target is provided, meet or exceed it unless the
                          available context is too thin to do so without inventing facts. If the
                          context is thin, still answer as fully as possible and say what is missing.
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
                min_answer_words=(
                    str(min_answer_words) if min_answer_words is not None else "not specified"
                ),
            )
        )
        payload = extract_json_payload(getattr(response, "content", str(response)))
        return RAGAgentResponse.model_validate(payload)

    def _summarize_with_plain_llm(
        self,
        question: str,
        snippets,
        *,
        min_answer_words: int | None,
    ) -> RAGAgentResponse:
        from langchain_core.prompts import ChatPromptTemplate

        relevant_context = self._build_relevant_context(snippets)
        source_documents = list(dict.fromkeys(snippet.source for snippet in snippets))
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

                        Write a polished plain-text answer for a marketing operator.

                        Requirements:
                        - Do not output JSON.
                        - Do not mention file names or sources in the answer.
                        - Synthesize the snippets into a coherent recommendation.
                        - Prefer one short intro paragraph, then concrete bullets or short paragraphs.
                        - If the question is strategic, cover audience, positioning, proof, offer, CTA,
                          and compliance when relevant.
                        - Minimum answer words: {min_answer_words}
                        - If the context is limited, say what is missing without inventing facts.
                        """
                    ).strip(),
                ),
            ]
        )
        llm = build_chat_model(
            self.settings,
            output_json=False,
            num_predict=2200 if (min_answer_words or 0) >= 1000 else 1400,
        )
        response = llm.invoke(
            prompt.format_messages(
                question=question,
                snippets="\n".join(f"- {item.source}: {item.excerpt}" for item in snippets),
                min_answer_words=(
                    str(min_answer_words) if min_answer_words is not None else "not specified"
                ),
            )
        )
        return RAGAgentResponse(
            answer=getattr(response, "content", str(response)),
            relevant_context=relevant_context,
            source_documents=source_documents,
            confidence="high" if len(source_documents) >= 3 else "medium",
        )

    def _sanitize_response(self, response: RAGAgentResponse) -> RAGAgentResponse:
        response.answer = self._sanitize_answer_text(response.answer)
        return response

    @classmethod
    def _clean_excerpt(cls, excerpt: str) -> str:
        cleaned = excerpt.replace("\r", "\n")
        cleaned = re.sub(r"^#{1,6}\s+[^\n]+", " ", cleaned, flags=re.MULTILINE)
        cleaned = re.sub(r"`([^`]+)`", r"\1", cleaned)
        cleaned = re.sub(r"\*\*([^*]+)\*\*", r"\1", cleaned)
        cleaned = re.sub(r"(?m)^\s*[-*]\s+", "", cleaned)
        cleaned = re.sub(r"\b(?:Purpose|Collection Rules|Retrieval Notes|Source Capture Rule)\b\s*:?", " ", cleaned, flags=re.IGNORECASE)
        cleaned = " ".join(cleaned.split()).strip(" -")
        if not cleaned:
            return ""

        sentence_match = re.match(r"(.{40,260}?[.!?])(?:\s|$)", cleaned)
        if sentence_match:
            return sentence_match.group(1).strip()

        return cleaned[:260].rstrip(" ,;:-")

    @staticmethod
    def _classify_context_excerpt(excerpt: str) -> str:
        lowered = excerpt.lower()
        if any(token in lowered for token in ["audience", "persona", "buyer", "customer"]):
            return "Audience"
        if any(token in lowered for token in ["tone", "voice", "brand", "messaging"]):
            return "Brand"
        if any(token in lowered for token in ["rule", "policy", "claim", "compliance", "safe"]):
            return "Compliance"
        if any(token in lowered for token in ["offer", "cta", "pricing", "conversion"]):
            return "Offer"
        if any(token in lowered for token in ["example", "campaign", "ad", "creative"]):
            return "Creative"
        if any(token in lowered for token in ["strategy", "channel", "landing", "retargeting"]):
            return "Strategy"
        return "Context"

    def _build_relevant_context(self, snippets) -> list[str]:
        context: list[str] = []
        seen_sources: set[str] = set()
        for snippet in snippets:
            if snippet.source in seen_sources:
                continue
            seen_sources.add(snippet.source)
            cleaned_excerpt = self._clean_excerpt(snippet.excerpt)
            if not cleaned_excerpt:
                continue
            context.append(cleaned_excerpt)
            if len(context) == 5:
                break
        return context

    def _build_fallback_answer(
        self,
        question: str,
        relevant_context: list[str],
        *,
        min_answer_words: int | None = None,
    ) -> str:
        lowered = question.lower()
        if any(token in lowered for token in ["persona", "audience", "tone", "brand", "guideline"]):
            brand_advice = self._build_brand_advice_fallback(lowered)
            if brand_advice:
                return brand_advice

        if any(
            token in lowered
            for token in [
                "angle",
                "angles",
                "market",
                "marketing",
                "position",
                "positioning",
                "message",
                "messaging",
                "strategy",
                "offer",
                "cta",
            ]
        ):
            return self._build_strategy_fallback(
                relevant_context,
                min_answer_words=min_answer_words,
            )

        summary_lines = [
            "Based on the available knowledge, the strongest answer is to use the retrieved context as operating guidance rather than treating it like raw notes.",
            "",
            "Key guidance:",
        ]
        for excerpt in relevant_context:
            summary_lines.append(
                f"- {self._classify_context_excerpt(excerpt)}: {excerpt}"
            )
        return self._expand_fallback_answer(
            "\n".join(summary_lines),
            relevant_context,
            min_answer_words=min_answer_words,
        )

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

        return "\n".join(lines)

    def _build_strategy_fallback(
        self,
        relevant_context: list[str],
        *,
        min_answer_words: int | None = None,
    ) -> str:
        if not relevant_context:
            return ""

        lines = [
            "Based on the available knowledge, the strongest marketing approach is to lead with the clearest buyer value and support it with trust signals that reduce hesitation.",
            "",
            "Recommended angles:",
        ]

        angle_labels = [
            "Audience fit",
            "Positioning",
            "Offer focus",
            "Proof",
            "Tone",
            "CTA direction",
        ]
        for label, excerpt in zip(angle_labels, relevant_context):
            lines.append(f"- {label}: {excerpt}")

        return self._expand_fallback_answer(
            "\n".join(lines),
            relevant_context,
            min_answer_words=min_answer_words,
        )

    @staticmethod
    def _resolve_top_k(min_answer_words: int | None, use_web_search: bool) -> int:
        top_k = 6
        if min_answer_words:
            top_k = max(top_k, min(10, 4 + (min_answer_words // 250)))
        if use_web_search:
            top_k = min(10, top_k + 1)
        return top_k

    @staticmethod
    def _count_words(text: str) -> int:
        return len(re.findall(r"\b\w+\b", text))

    def _expand_fallback_answer(
        self,
        base_answer: str,
        relevant_context: list[str],
        *,
        min_answer_words: int | None,
    ) -> str:
        if not min_answer_words or self._count_words(base_answer) >= min_answer_words:
            return base_answer
        if not relevant_context:
            return base_answer

        lines = [base_answer, "", "Expanded guidance:"]
        elaborations = [
            "Use this point to shape the primary message, the proof layer, and the CTA so the answer stays specific instead of generic.",
            "Treat it as guidance for positioning, landing-page hierarchy, ad framing, and objection handling, not as a throwaway note.",
            "If you want sharper outputs later, expand this area in the knowledge base with stronger examples, more proof points, and clearer commercial constraints.",
        ]

        while self._count_words("\n".join(lines)) < min_answer_words:
            for excerpt in relevant_context:
                label = self._classify_context_excerpt(excerpt)
                lines.append(f"- {label}: {excerpt}")
                for note in elaborations:
                    lines.append(note)
                if self._count_words("\n".join(lines)) >= min_answer_words:
                    break

        return "\n".join(lines)

    @staticmethod
    def _sanitize_answer_text(answer: str) -> str:
        cleaned_lines: list[str] = []
        skip_source_block = False

        for raw_line in answer.splitlines():
            line = raw_line.strip()
            if not line:
                if not skip_source_block and cleaned_lines and cleaned_lines[-1]:
                    cleaned_lines.append("")
                continue

            lowered = line.lower()
            if lowered in {"sources:", "source:", "source documents:", "source document:"}:
                skip_source_block = True
                continue

            if skip_source_block:
                if re.match(r"^[-*]\s+.+\.(md|txt|csv|json|pdf)\b", line, flags=re.IGNORECASE):
                    continue
                skip_source_block = False

            line = re.sub(
                r"^[-*]\s+[A-Za-z0-9_./ -]+\.(md|txt|csv|json|pdf)\s*:\s*",
                "- ",
                line,
                flags=re.IGNORECASE,
            )
            line = re.sub(
                r"\b(?:from|according to)\s+[A-Za-z0-9_./ -]+\.(md|txt|csv|json|pdf)\b[:,]?\s*",
                "",
                line,
                flags=re.IGNORECASE,
            ).strip()

            if line:
                cleaned_lines.append(line)

        return "\n".join(cleaned_lines).strip()

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
