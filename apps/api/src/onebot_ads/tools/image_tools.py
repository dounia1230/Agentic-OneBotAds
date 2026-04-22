import time
from functools import lru_cache
from pathlib import Path

from langchain.tools import tool

from onebot_ads.core.config import get_settings

DEFAULT_NEGATIVE_PROMPT = (
    "blurry, low quality, distorted text, unreadable text, watermark, unreadable UI, fake logos"
)


@lru_cache(maxsize=1)
def load_image_pipeline():
    try:
        import torch
        from diffusers import AutoPipelineForText2Image
    except ImportError as exc:
        raise RuntimeError(
            "Diffusers image generation dependencies are not installed."
        ) from exc

    settings = get_settings()
    device = "cuda" if torch.cuda.is_available() else "cpu"
    dtype = torch.float16 if device == "cuda" else torch.float32
    pipe = AutoPipelineForText2Image.from_pretrained(
        settings.image_model,
        torch_dtype=dtype,
    )
    pipe.to(device)
    return pipe


@tool
def generate_ad_image(prompt: str, negative_prompt: str = DEFAULT_NEGATIVE_PROMPT) -> dict:
    """
    Generate an advertising image from a text prompt.
    Returns the local image path and generation status.
    """
    settings = get_settings()
    if not settings.enable_image_generation:
        return {
            "status": "disabled",
            "image_path": None,
            "message": "Image generation is disabled in configuration.",
        }

    pipe = load_image_pipeline()
    image = pipe(
        prompt=prompt,
        negative_prompt=negative_prompt,
        num_inference_steps=30,
        guidance_scale=7.5,
    ).images[0]

    output_dir = Path(settings.output_image_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    filename = output_dir / f"ad_image_{int(time.time())}.png"
    image.save(filename)
    return {
        "status": "generated",
        "image_path": str(filename),
    }
