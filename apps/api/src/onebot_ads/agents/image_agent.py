from onebot_ads.core.config import Settings
from onebot_ads.schemas.campaigns import ImageGenerationResponse
from onebot_ads.tools.creative_tools import normalize_platform
from onebot_ads.tools.image_tools import generate_ad_image

SYSTEM_PROMPT = """
You are the Image Generation Agent of Agentic OneBotAds.

Your job is to create advertising image prompts and generate images
through an image generation tool when requested.

Important:
The text LLM does not create images directly.
You generate a detailed image prompt.
The image generation tool creates the actual image.

When creating image prompts, include:
- subject
- product/service concept
- audience
- platform format
- visual style
- composition
- color direction
- mood
- quality terms
- aspect ratio when relevant

Avoid:
- unreadable text in the image
- distorted logos
- watermarks
- low quality
- unrealistic promises
- copyrighted characters or brand marks unless explicitly provided by the user

Return:
- image_prompt
- negative_prompt
- alt_text
- image_path if generated
- status
""".strip()


class ImageGenerationAgent:
    def __init__(self, settings: Settings) -> None:
        self.settings = settings

    def run(
        self,
        *,
        product_name: str,
        audience: str,
        platform: str,
        goal: str,
        style: str,
        request_image_generation: bool,
    ) -> ImageGenerationResponse:
        platform_name = normalize_platform(platform)
        aspect_ratio = "16:9" if platform_name == "LinkedIn" else "1:1"
        image_prompt = (
            f"Professional {platform_name} ad visual for {product_name}, showing an AI-powered "
            f"campaign workspace helping {audience} {goal.lower()}, {style}, "
            f"clean SaaS dashboard, clear composition, blue and white palette, "
            f"premium startup look, high quality, {aspect_ratio}"
        )
        negative_prompt = (
            "blurry, low quality, distorted text, unreadable text, "
            "watermark, unreadable UI, fake logos"
        )
        alt_text = f"A modern AI advertising dashboard supporting {audience}."
        notes: list[str] = []
        image_path = None
        status = "prompt_only"

        if request_image_generation:
            try:
                generation = generate_ad_image.invoke(
                    {"prompt": image_prompt, "negative_prompt": negative_prompt}
                )
                image_path = generation.get("image_path")
                status = generation.get("status", "not_generated")
                if generation.get("message"):
                    notes.append(generation["message"])
            except Exception as exc:
                status = "failed"
                notes.append(str(exc))

        return ImageGenerationResponse(
            image_prompt=image_prompt,
            negative_prompt=negative_prompt,
            alt_text=alt_text,
            image_path=image_path,
            status=status,
            notes=notes,
        )
