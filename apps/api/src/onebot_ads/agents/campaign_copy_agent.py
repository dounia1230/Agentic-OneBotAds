import json
import re
from pathlib import Path
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
from onebot_ads.schemas.knowledge import KnowledgeScope
from onebot_ads.tools.channel_guidance import build_channel_guidance, build_default_cta
from onebot_ads.tools.image_composer import compose_publication_image
from onebot_ads.tools.image_tools import (
    build_publication_background_prompt,
    generate_background_image,
    normalize_image_provider,
    provider_backend,
    provider_reference,
)
from onebot_ads.tools.path_tools import to_outputs_url

UNSUPPORTED_PATTERN_REPLACEMENTS = [
    (r"\bguaranteed\b", "designed to support"),
    (r"\brisk-free\b", "lower-friction"),
    (r"\bwithout risk\b", "with more confidence"),
    (r"\bno risk\b", "with fewer manual steps"),
    (r"\binstant results\b", "faster iteration"),
    (r"\bperfect targeting\b", "stronger targeting"),
    (r"\bguaranteed leads\b", "qualified lead generation"),
    (r"\bguaranteed sales\b", "stronger sales opportunities"),
    (r"\b\d+%\s+(higher|faster|more)\b", "stronger"),
    (r"\bsaving\s+\d+\+?\s+hours\b", "saving time"),
]


def _format_exception_details(exc: Exception) -> str:
    exception_name = type(exc).__name__
    exception_message = str(exc).strip()
    return f"{exception_name}: {exception_message}" if exception_message else exception_name


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
        if brief.source_context_query and not context:
            warnings.append(
                "Draft context query returned no snippets; fallback copy used only the brief."
            )

        if self.settings.enable_live_llm:
            try:
                response = self._draft_with_live_llm(brief, context, warnings)
                return self._finalize_draft_response(response, brief, context, warnings)
            except Exception as exc:
                warnings.append(
                    "Live LLM draft path failed; deterministic fallback returned: "
                    f"{_format_exception_details(exc)}"
                )

        response = self._draft_fallback(brief, context, warnings)
        return self._finalize_draft_response(response, brief, context, warnings)

    def _retrieve_context(self, brief: CampaignBrief) -> list[ContextSnippet]:
        if not self.settings.enable_rag:
            return []

        query = brief.source_context_query or " ".join(
            part
            for part in [brief.product_name, brief.audience, brief.goal, brief.offer or ""]
            if part.strip()
        )
        scope = brief.knowledge_scope
        if scope is None and (brief.brand_name or brief.campaign_name or brief.product_name):
            scope = KnowledgeScope(
                brand_name=brief.brand_name or brief.product_name,
                campaign_name=brief.campaign_name,
            )
        return self.knowledge_base.retrieve(query=query, top_k=3, scope=scope)

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
                        {{
                          "summary": "string",
                          "variants": [
                            {{
                              "channel": "string",
                              "headline": "string",
                              "primary_text": "string",
                              "cta": "string",
                              "rationale": "string"
                            }}
                          ],
                          "image_prompt": "string or null"
                        }}
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

        return CampaignDraftResponse(
            provider="fallback",
            mode="fallback",
            summary=summary,
            variants=variants,
            image_prompt=image_prompt,
            used_context=context,
            warnings=warnings,
        )

    def _finalize_draft_response(
        self,
        response: CampaignDraftResponse,
        brief: CampaignBrief,
        context: list[ContextSnippet],
        warnings: list[str],
    ) -> CampaignDraftResponse:
        compliance_issues: list[str] = []
        response.used_context = context
        response.variants = [
            self._sanitize_variant(variant, brief.brand_constraints, compliance_issues)
            for variant in response.variants
        ]

        if brief.generate_image_prompt or brief.generate_image or brief.compose_publication_image:
            response.image_prompt = self._build_image_payload(brief, response.variants)

        response.warnings = warnings
        response.compliance_issues = list(dict.fromkeys(compliance_issues))
        response.status = "needs_revision" if response.compliance_issues else "ready_for_review"
        return response

    def _build_image_payload(
        self,
        brief: CampaignBrief,
        variants: list[AdVariant],
    ) -> ImagePrompt:
        provider, normalization_note = normalize_image_provider(
            brief.image_provider or self.settings.image_provider,
            self.settings.image_provider,
        )
        image_spec = build_publication_background_prompt(
            product_name=brief.product_name,
            audience=brief.audience,
            platform="/".join(brief.channels) if brief.channels else "linkedin",
        )
        notes: list[str] = []
        if normalization_note:
            notes.append(normalization_note)
        background_path = None
        publication_path = None
        status = "prompt_ready"
        error = None
        fallback_used = False
        fallback_attempted = False
        fallback_succeeded = False
        primary_provider = provider
        fallback_provider = None
        backend = provider_backend(provider)
        space_id = provider_reference(provider, self.settings)

        if brief.generate_image:
            try:
                generation = generate_background_image.invoke(
                    {
                        "prompt": image_spec["prompt"],
                        "provider": provider,
                        "negative_prompt": image_spec["negative_prompt"],
                        "aspect_ratio": "16:9" if "linkedin" in brief.channels else "1:1",
                    }
                )
            except Exception as exc:
                generation = {
                    "status": "generation_failed",
                    "provider": provider,
                    "backend": backend,
                    "space_id": space_id,
                    "background_image_path": None,
                    "image_path": None,
                    "error": _format_exception_details(exc),
                    "notes": ["Image generation failed before a provider response was returned."],
                    "fallback_used": False,
                    "fallback_attempted": False,
                    "fallback_succeeded": False,
                    "primary_provider": provider,
                    "fallback_provider": fallback_provider,
                }
            status = generation["status"]
            background_path = generation.get("background_image_path")
            error = generation.get("error")
            notes.extend(generation.get("notes", []))
            provider = generation.get("provider", provider)
            backend = generation.get("backend", backend)
            space_id = generation.get("space_id", space_id)
            fallback_used = generation.get("fallback_used", False)
            fallback_attempted = generation.get("fallback_attempted", False)
            fallback_succeeded = generation.get("fallback_succeeded", False)
            primary_provider = generation.get("primary_provider", primary_provider)
            fallback_provider = generation.get("fallback_provider", fallback_provider)

            if brief.compose_publication_image and background_path and variants:
                try:
                    composition = compose_publication_image(
                        background_path=background_path,
                        headline=variants[0].headline,
                        cta=variants[0].cta,
                        product_name=brief.product_name,
                        output_dir=str(self.settings.output_image_dir),
                    )
                except Exception as exc:
                    composition = {"status": "composition_failed", "error": str(exc)}
                publication_path = composition.get("image_path")
                if composition["status"] == "composed" and publication_path:
                    status = "composed"
                elif composition["status"] == "composition_failed":
                    error = composition.get("error")
                    notes.append(f"Composition failed: {composition.get('error')}")

        image_path = publication_path or background_path
        final_image_path = image_path if image_path and Path(image_path).exists() else None
        return ImagePrompt(
            prompt=image_spec["prompt"],
            provider=provider,
            backend=backend,
            space_id=space_id,
            negative_prompt=image_spec["negative_prompt"],
            status=status,
            background_image_path=background_path,
            publication_image_path=publication_path,
            image_path=final_image_path,
            image_url=to_outputs_url(final_image_path),
            alt_text=image_spec["alt_text"],
            error=error,
            notes=notes,
            fallback_used=fallback_used,
            fallback_attempted=fallback_attempted,
            fallback_succeeded=fallback_succeeded,
            primary_provider=primary_provider,
            fallback_provider=fallback_provider,
        )

    def _sanitize_variant(
        self,
        variant: AdVariant,
        brand_constraints: list[str],
        compliance_issues: list[str],
    ) -> AdVariant:
        if not self._strict_compliance(brand_constraints):
            return variant

        return AdVariant(
            channel=variant.channel,
            headline=self._sanitize_text(variant.headline, compliance_issues),
            primary_text=self._sanitize_text(variant.primary_text, compliance_issues),
            cta=self._sanitize_text(variant.cta, compliance_issues),
            rationale=variant.rationale,
        )

    @staticmethod
    def _strict_compliance(brand_constraints: list[str]) -> bool:
        lowered = {constraint.lower() for constraint in brand_constraints}
        return "avoid hype" in lowered or "no guaranteed outcomes" in lowered

    @staticmethod
    def _sanitize_text(text: str, compliance_issues: list[str]) -> str:
        sanitized = text
        for pattern, replacement in UNSUPPORTED_PATTERN_REPLACEMENTS:
            updated = re.sub(pattern, replacement, sanitized, flags=re.IGNORECASE)
            if updated != sanitized:
                compliance_issues.append(
                    f"Removed unsupported claim pattern from draft copy: {pattern}"
                )
                sanitized = updated
        return sanitized

    @staticmethod
    def _extract_json_payload(raw: str) -> dict:
        start = raw.find("{")
        end = raw.rfind("}")
        if start == -1 or end == -1 or start >= end:
            raise ValueError("Model response did not contain a JSON object.")
        return json.loads(raw[start : end + 1])
