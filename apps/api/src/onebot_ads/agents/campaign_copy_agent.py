import re
from pathlib import Path

from onebot_ads.agents.creative_agent import CreativeCopywritingAgent
from onebot_ads.core.config import Settings
from onebot_ads.rag.knowledge_base import KnowledgeBaseService
from onebot_ads.schemas.campaigns import (
    AdVariant,
    CampaignBrief,
    CampaignDraftResponse,
    ContextSnippet,
    ImagePrompt,
    RAGAgentResponse,
)
from onebot_ads.schemas.knowledge import KnowledgeScope
from onebot_ads.tools.channel_guidance import build_channel_guidance
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


class CampaignCopyAgent:
    def __init__(self, settings: Settings, knowledge_base: KnowledgeBaseService) -> None:
        self.settings = settings
        self.knowledge_base = knowledge_base
        self.creative_agent = CreativeCopywritingAgent(settings)

    def draft(self, brief: CampaignBrief) -> CampaignDraftResponse:
        warnings: list[str] = []
        context = self._retrieve_context(brief)
        if brief.source_context_query and not context:
            warnings.append(
                "Draft context query returned no snippets; fallback copy used only the brief."
            )

        response = self._draft_with_creative_agent(brief, context, warnings)
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

    def _draft_with_creative_agent(
        self,
        brief: CampaignBrief,
        context: list[ContextSnippet],
        warnings: list[str],
    ) -> CampaignDraftResponse:
        guidance = build_channel_guidance(brief.channels)
        context_sources = (
            ", ".join(item.source for item in context[:2]) if context else "the base brief"
        )
        rag_context = self._build_rag_context(context)
        variants: list[AdVariant] = []
        mode = "fallback"

        for channel in brief.channels:
            rule = guidance.get(channel, guidance["default"])
            creative_response, creative_mode, creative_warning = (
                self.creative_agent.generate_with_mode(
                    user_request=self._build_channel_request(brief, channel, rule),
                    platform=self._channel_to_platform(channel),
                    audience=brief.audience,
                    goal=brief.goal,
                    product_name=brief.product_name,
                    tone=brief.tone,
                    rag_context=rag_context,
                )
            )
            if creative_mode == "live_llm":
                mode = "live_llm"
            if creative_warning and creative_warning not in warnings:
                warnings.append(creative_warning)

            rationale = (
                f"Optimized for {channel} with emphasis on {rule['copy_goal']}. "
                f"Format guidance: {rule['format_hint']} "
                f"Grounded in {context_sources}."
            )
            variants.append(
                AdVariant(
                    channel=channel,
                    headline=creative_response.headline[:110],
                    primary_text=creative_response.primary_text,
                    cta=creative_response.cta,
                    rationale=rationale,
                )
            )

        summary = (
            f"Drafted {len(variants)} channel variants for {brief.product_name} using "
            f"CreativeCopywritingAgent and context from {context_sources}."
        )

        return CampaignDraftResponse(
            provider="ollama" if mode == "live_llm" else "fallback",
            mode=mode,
            summary=summary,
            variants=variants,
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
            response.image_prompt = self._build_image_payload(brief, response.variants, context)

        response.warnings = warnings
        response.compliance_issues = list(dict.fromkeys(compliance_issues))
        response.status = "needs_revision" if response.compliance_issues else "ready_for_review"
        return response

    def _build_image_payload(
        self,
        brief: CampaignBrief,
        variants: list[AdVariant],
        context: list[ContextSnippet],
    ) -> ImagePrompt:
        provider, normalization_note = normalize_image_provider(
            brief.image_provider or self.settings.image_provider,
            self.settings.image_provider,
        )
        image_spec = build_publication_background_prompt(
            product_name=brief.product_name,
            audience=brief.audience,
            platform="/".join(brief.channels) if brief.channels else "linkedin",
            goal=brief.goal,
            style=(
                "modern editorial marketing, clear hierarchy, strong offer framing, "
                "brand-safe and conversion-focused"
            ),
            headline=variants[0].headline if variants else None,
            cta=variants[0].cta if variants else None,
            brand_context=" ".join(snippet.excerpt for snippet in context[:2]) or None,
            offer=brief.offer,
            key_points=brief.key_points,
            brand_constraints=brief.brand_constraints,
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
    def _channel_to_platform(channel: str) -> str:
        normalized = channel.strip().lower()
        if normalized == "meta":
            return "Facebook"
        if normalized == "google":
            return "Google Ads"
        if normalized == "landing_page":
            return "LinkedIn"
        return normalized.replace("_", " ").title()

    def _build_channel_request(
        self,
        brief: CampaignBrief,
        channel: str,
        guidance: dict[str, str],
    ) -> str:
        request_parts = [
            f"Create a {channel} campaign draft for {brief.product_name}.",
            f"Audience: {brief.audience}.",
            f"Goal: {brief.goal}.",
            f"Tone: {brief.tone}.",
            f"Channel guidance: {guidance['format_hint']}",
            f"Copy goal: {guidance['copy_goal']}.",
        ]
        if brief.offer:
            request_parts.append(f"Offer: {brief.offer}.")
        if brief.key_points:
            request_parts.append("Key points: " + ", ".join(brief.key_points[:4]) + ".")
        if brief.brand_constraints:
            request_parts.append(
                "Brand constraints: " + ", ".join(brief.brand_constraints[:4]) + "."
            )
        return " ".join(request_parts)

    @staticmethod
    def _build_rag_context(context: list[ContextSnippet]) -> RAGAgentResponse | None:
        if not context:
            return None
        return RAGAgentResponse(
            answer=" ".join(snippet.excerpt.strip() for snippet in context if snippet.excerpt.strip()),
            relevant_context=[snippet.excerpt.strip() for snippet in context if snippet.excerpt.strip()],
            source_documents=[snippet.source for snippet in context],
            confidence="medium",
        )
