import re

from onebot_ads.core.config import Settings
from onebot_ads.schemas.campaigns import (
    ComplianceReviewResponse,
    ComplianceSafeVersion,
    CreativeCopyResponse,
    ImageGenerationResponse,
    RAGAgentResponse,
)

SYSTEM_PROMPT = """
You are the Brand Safety & Compliance Agent of Agentic OneBotAds.

Your role is to review advertising content before it is returned as ready for review.

Check:
- brand tone
- factual accuracy against RAG context
- exaggerated claims
- prohibited claims
- unsafe content
- platform advertising rule conflicts
- unclear CTA
- unsupported product features
- visual prompt issues
- accessibility alt text

Rules:
1. Do not approve content with unsupported promises.
2. Do not approve content that invents product capabilities.
3. If issues exist, explain them clearly and provide corrected text.
4. If content is safe, return approved = true.
5. Always return JSON.
""".strip()

PROHIBITED_PHRASES = [
    "guaranteed sales",
    "instant success",
    "risk-free profit",
    "perfect targeting",
    "guaranteed success",
    "guaranteed leads",
    "without risk",
    "no risk",
    "instant results",
]
UNSUPPORTED_REGEX_PATTERNS = [
    r"\b\d+%\s+(higher|faster|more)\b",
    r"\bsaving\s+\d+\+?\s+hours\b",
]


class BrandSafetyComplianceAgent:
    def __init__(self, settings: Settings) -> None:
        self.settings = settings

    def run(
        self,
        creative: CreativeCopyResponse,
        image: ImageGenerationResponse | None = None,
        rag_context: RAGAgentResponse | None = None,
    ) -> ComplianceReviewResponse:
        issues: list[str] = []
        suggested_fixes: list[str] = []
        headline = creative.headline
        caption = creative.primary_text

        haystack = f"{headline} {caption}".lower()
        for phrase in PROHIBITED_PHRASES:
            if phrase in haystack:
                issues.append(f"Unsupported or exaggerated claim detected: '{phrase}'.")
                caption = caption.replace(phrase, "stronger campaign outcomes")

        for pattern in UNSUPPORTED_REGEX_PATTERNS:
            if re.search(pattern, haystack, flags=re.IGNORECASE):
                issues.append(f"Unsupported quantified claim detected: '{pattern}'.")

        if rag_context and (
            "does not contain enough grounded information" in rag_context.answer.lower()
        ):
            issues.append("Brand context was limited; review factual claims before publishing.")

        if image and not image.alt_text.strip():
            issues.append("Accessibility alt text is missing.")
            suggested_fixes.append("Add a concise alt text description for the generated visual.")

        if image:
            negative_prompt = image.negative_prompt.lower()
            text_tokens = ["unreadable text", "words", "letters", "text"]
            if not any(token in negative_prompt for token in text_tokens):
                issues.append(
                    "Negative prompt should discourage readable text in generated visuals."
                )

        if issues:
            suggested_fixes.append(
                "Remove unsupported promises and keep the message grounded "
                "in product capabilities."
            )

        return ComplianceReviewResponse(
            approved=not issues,
            issues=issues,
            suggested_fixes=suggested_fixes,
            final_safe_version=ComplianceSafeVersion(
                headline=headline,
                caption=caption,
            ),
        )
