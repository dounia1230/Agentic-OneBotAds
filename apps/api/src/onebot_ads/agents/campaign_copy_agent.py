import json
from textwrap import dedent

from pydantic import BaseModel, Field

from onebot_ads.core.config import Settings
from onebot_ads.rag.knowledge_base import KnowledgeBaseService
from onebot_ads.schemas.campaigns import (
    AdVariant,
    CampaignBrief,
    CampaignDraftResponse,
    ContextSnippet,
    ImagePrompt,
)
from onebot_ads.tools.channel_guidance import build_channel_guidance, build_default_cta


class _DraftVariantPayload(BaseModel):
    channel: str
    headline: str
    primary_text: str
    cta: str
    rationale: str


class _DraftPayload(BaseModel):
    summary: str = Field(min_length=10)
    variants: list[_DraftVariantPayload]
    image_prompt: str | None = None


class CampaignCopyAgent:
    def __init__(self, settings: Settings, knowledge_base: KnowledgeBaseService) -> None:
        self.settings = settings
        self.knowledge_base = knowledge_base

    def draft(self, brief: CampaignBrief) -> CampaignDraftResponse:
        warnings: list[str] = []
        context = self._retrieve_context(brief)

        if self.settings.enable_live_llm:
            try:
                return self._draft_with_live_llm(brief, context, warnings)
            except Exception as exc:
                warnings.append(f"Live LLM draft path failed, fallback used: {exc}")

        return self._draft_fallback(brief, context, warnings)

    def _retrieve_context(self, brief: CampaignBrief) -> list[ContextSnippet]:
        if not self.settings.enable_rag:
            return []

        query = brief.source_context_query or " ".join(
            part
            for part in [brief.product_name, brief.audience, brief.goal, brief.offer or ""]
            if part.strip()
        )
        return self.knowledge_base.retrieve(query=query, top_k=3)

    def _draft_with_live_llm(
        self,
        brief: CampaignBrief,
        context: list[ContextSnippet],
        warnings: list[str],
    ) -> CampaignDraftResponse:
        from langchain_core.prompts import ChatPromptTemplate
        from langchain_ollama import ChatOllama

        llm = ChatOllama(
            model=self.settings.ollama_chat_model,
            base_url=self.settings.ollama_base_url,
            temperature=self.settings.llm_temperature,
            num_predict=800,
            validate_model_on_init=False,
        )

        prompt = ChatPromptTemplate.from_messages(
            [
                (
                    "system",
                    dedent(
                        """
                        You are a senior performance marketer.
                        Return only valid JSON with this shape:
                        {
                          "summary": "string",
                          "variants": [
                            {
                              "channel": "string",
                              "headline": "string",
                              "primary_text": "string",
                              "cta": "string",
                              "rationale": "string"
                            }
                          ],
                          "image_prompt": "string or null"
                        }
                        Keep copy concrete, conversion-focused, and compliant with
                        the provided constraints.
                        """
                    ).strip(),
                ),
                (
                    "human",
                    dedent(
                        """
                        Campaign brief:
                        {brief_json}

                        Channel guidance:
                        {guidance_json}

                        Retrieved context:
                        {context_json}

                        Generate one strong ad variant per requested channel.
                        """
                    ).strip(),
                ),
            ]
        )

        response = llm.invoke(
            prompt.format_messages(
                brief_json=json.dumps(brief.model_dump(mode="json"), indent=2),
                guidance_json=json.dumps(build_channel_guidance(brief.channels), indent=2),
                context_json=json.dumps([item.model_dump() for item in context], indent=2),
            )
        )
        content = getattr(response, "content", str(response))
        payload = _DraftPayload.model_validate(self._extract_json_payload(content))

        variants = [
            AdVariant(
                channel=variant.channel,
                headline=variant.headline,
                primary_text=variant.primary_text,
                cta=variant.cta,
                rationale=variant.rationale,
            )
            for variant in payload.variants
        ]

        if not variants:
            raise ValueError("No variants returned by the model.")

        image_prompt = (
            ImagePrompt(prompt=payload.image_prompt, provider=self.settings.image_provider)
            if payload.image_prompt
            else None
        )

        return CampaignDraftResponse(
            provider="ollama",
            mode="live_llm",
            summary=payload.summary,
            variants=variants,
            image_prompt=image_prompt,
            used_context=context,
            warnings=warnings,
        )

    def _draft_fallback(
        self,
        brief: CampaignBrief,
        context: list[ContextSnippet],
        warnings: list[str],
    ) -> CampaignDraftResponse:
        guidance = build_channel_guidance(brief.channels)
        signal = (
            brief.key_points[:2]
            if brief.key_points
            else ["channel-ready drafts", "local-first workflow"]
        )
        context_sources = (
            ", ".join(item.source for item in context[:2]) if context else "the base brief"
        )

        variants: list[AdVariant] = []
        for channel in brief.channels:
            rule = guidance.get(channel, guidance["default"])
            headline = f"{brief.product_name}: faster {brief.goal.lower()} for {brief.audience}"
            primary_text = (
                f"{brief.product_name} helps {brief.audience} move from idea to launch-ready ads "
                f"with {signal[0]} and {signal[-1]}. "
                f"Offer: {brief.offer or 'a focused pilot campaign'}."
            )
            rationale = (
                f"Optimized for {channel} with emphasis on {rule['copy_goal']} and guidance from "
                f"{context_sources}."
            )
            variants.append(
                AdVariant(
                    channel=channel,
                    headline=headline[:110],
                    primary_text=primary_text,
                    cta=build_default_cta(channel),
                    rationale=rationale,
                )
            )

        image_prompt = None
        if brief.generate_image_prompt:
            image_prompt = ImagePrompt(
                prompt=(
                    f"Create a campaign visual for {brief.product_name} aimed at {brief.audience}. "
                    f"Style: modern editorial marketing, clear hierarchy, strong offer framing, "
                    f"brand-safe and conversion-focused."
                ),
                provider=self.settings.image_provider,
            )

        summary = (
            f"Drafted {len(variants)} channel variants for {brief.product_name} using "
            "deterministic "
            f"fallback logic and context from {context_sources}."
        )
        if self.settings.enable_live_llm:
            warnings.append(
                "Live model path unavailable or not provisioned; deterministic fallback "
                "returned."
            )

        return CampaignDraftResponse(
            provider="fallback",
            mode="fallback",
            summary=summary,
            variants=variants,
            image_prompt=image_prompt,
            used_context=context,
            warnings=warnings,
        )

    @staticmethod
    def _extract_json_payload(raw: str) -> dict:
        start = raw.find("{")
        end = raw.rfind("}")
        if start == -1 or end == -1 or start >= end:
            raise ValueError("Model response did not contain a JSON object.")
        return json.loads(raw[start : end + 1])
