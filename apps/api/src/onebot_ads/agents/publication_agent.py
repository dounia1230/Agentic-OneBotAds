from onebot_ads.core.config import Settings
from onebot_ads.schemas.campaigns import (
    ComplianceReviewResponse,
    CreativeCopyResponse,
    ImageGenerationResponse,
    OptimizationResponse,
    PublicationPackage,
)
from onebot_ads.tools.creative_tools import normalize_platform
from onebot_ads.tools.path_tools import to_outputs_url
from onebot_ads.tools.publication_tools import recommended_schedule_for_platform

SYSTEM_PROMPT = """
You are the Publication Agent of Agentic OneBotAds.

Your task is to assemble a complete advertising publication package.

You do not invent copy from scratch if the Creative Copywriting Agent already provided it.
You combine the approved copy, image information, RAG context, and compliance result.

A complete publication must include:
- platform
- headline
- caption
- cta
- hashtags
- image_prompt
- image_path if available
- alt_text
- recommended_schedule
- compliance_status
- optimization_notes
- status

Rules:
1. If compliance approved the content, set status to "ready_for_review".
2. If compliance found issues, set status to "needs_revision".
3. If image generation was requested but failed, include the image
   prompt and set image_path to null.
4. Keep the final package easy to copy and use.
""".strip()


class PublicationAgent:
    def __init__(self, settings: Settings) -> None:
        self.settings = settings

    def run(
        self,
        *,
        platform: str,
        creative: CreativeCopyResponse,
        image: ImageGenerationResponse | None,
        compliance: ComplianceReviewResponse,
        optimization: OptimizationResponse | None = None,
    ) -> PublicationPackage:
        resolved_platform = normalize_platform(platform)
        optimization_notes = []
        if optimization:
            optimization_notes.extend(
                item.recommendation for item in optimization.quick_wins[:2]
            )
            optimization_notes.extend(
                item.recommendation for item in optimization.strategic_changes[:1]
            )

        resolved_image_path = (
            image.publication_image_path
            or image.image_path
            or image.background_image_path
            if image
            else None
        )
        return PublicationPackage(
            platform=resolved_platform,
            headline=compliance.final_safe_version.headline,
            caption=compliance.final_safe_version.caption,
            cta=creative.cta,
            hashtags=creative.hashtags,
            image_prompt=image.image_prompt if image else None,
            image_path=resolved_image_path,
            image_url=to_outputs_url(resolved_image_path),
            alt_text=image.alt_text if image else None,
            recommended_schedule=recommended_schedule_for_platform(resolved_platform),
            compliance_status="approved" if compliance.approved else "needs_revision",
            optimization_notes=optimization_notes,
            status="ready_for_review" if compliance.approved else "needs_revision",
        )
