from onebot_ads.core.config import Settings
from onebot_ads.schemas.campaigns import ImageGenerationResponse
from onebot_ads.tools.creative_tools import normalize_platform
from onebot_ads.tools.image_composer import compose_publication_image
from onebot_ads.tools.image_tools import (
    build_publication_background_prompt,
    generate_background_image,
)
from onebot_ads.tools.path_tools import to_outputs_url

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
        headline: str | None = None,
        cta: str | None = None,
        compose_publication_image_flag: bool = True,
        provider: str | None = None,
    ) -> ImageGenerationResponse:
        platform_name = normalize_platform(platform)
        aspect_ratio = "16:9" if platform_name == "LinkedIn" else "1:1"
        image_spec = build_publication_background_prompt(
            product_name=product_name,
            audience=audience,
            platform=platform_name,
        )
        notes: list[str] = []
        background_image_path = None
        publication_image_path = None
        image_path = None
        resolved_provider = (provider or self.settings.image_provider).lower()
        status = "prompt_only"
        error = None

        if request_image_generation and self.settings.enable_image_generation:
            generation = generate_background_image.invoke(
                {
                    "prompt": image_spec["prompt"],
                    "provider": resolved_provider,
                    "width": self.settings.pollinations_width,
                    "height": self.settings.pollinations_height,
                    "negative_prompt": image_spec["negative_prompt"],
                    "aspect_ratio": aspect_ratio,
                }
            )
            background_image_path = generation.get("background_image_path")
            image_path = generation.get("image_path")
            status = generation.get("status", "not_generated")
            error = generation.get("error")
            notes.extend(generation.get("notes", []))

            if (
                compose_publication_image_flag
                and background_image_path
                and headline
                and cta
            ):
                composition = compose_publication_image(
                    background_path=background_image_path,
                    headline=headline,
                    cta=cta,
                    product_name=product_name,
                    output_dir=str(self.settings.output_image_dir),
                )
                publication_image_path = composition.get("image_path")
                if composition["status"] == "composed" and publication_image_path:
                    status = "composed"
                    image_path = publication_image_path
                elif composition["status"] == "composition_failed":
                    error = composition.get("error")
                    notes.append(f"Composition failed: {composition.get('error')}")
        elif request_image_generation and not self.settings.enable_image_generation:
            status = "disabled"
            notes.append("Image generation is disabled in configuration.")

        return ImageGenerationResponse(
            image_prompt=image_spec["prompt"],
            negative_prompt=image_spec["negative_prompt"],
            alt_text=image_spec["alt_text"],
            provider=resolved_provider,
            background_image_path=background_image_path,
            publication_image_path=publication_image_path,
            image_path=image_path,
            image_url=to_outputs_url(image_path),
            status=status,
            error=error,
            notes=notes,
        )
