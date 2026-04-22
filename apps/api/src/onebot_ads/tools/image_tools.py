import base64
import mimetypes
import time
from functools import lru_cache
from pathlib import Path
from urllib.parse import quote

import requests
from langchain.tools import tool

from onebot_ads.core.config import get_settings

DEFAULT_NEGATIVE_PROMPT = (
    "words, letters, text, watermark, logo, distorted UI, unreadable dashboard, "
    "blurry, low quality, fake brand marks"
)
NANO_BANANA_PROVIDERS = {"nano_banana", "gemini", "google_gemini"}


def build_publication_background_prompt(
    *,
    product_name: str,
    audience: str,
    platform: str,
) -> dict[str, str]:
    prompt = (
        "Clean professional SaaS marketing background for an AI advertising assistant, "
        f"{product_name} for {audience}, {platform} publication format, abstract dashboard "
        "shapes, business productivity mood, blue and white modern tech aesthetic, soft "
        "gradients, clean composition, empty space for text overlay, high quality, no text, "
        "no words, no letters, no logos, no watermark, no fake UI labels, "
        "no readable dashboard text"
    )
    return {
        "prompt": prompt,
        "negative_prompt": DEFAULT_NEGATIVE_PROMPT,
        "alt_text": f"Clean professional marketing background for {product_name}.",
    }


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


def _background_output_path(output_dir: Path, mime_type: str = "image/png") -> Path:
    extension = mimetypes.guess_extension(mime_type) or ".png"
    if extension == ".jpe":
        extension = ".jpg"
    return output_dir / f"background_{int(time.time())}{extension}"


def _read_error_response(response: requests.Response) -> str:
    try:
        payload = response.json()
        if isinstance(payload, dict):
            return str(payload.get("error") or payload)[:400]
    except ValueError:
        pass
    return (response.text or f"HTTP {response.status_code}")[:400]


def _generate_with_pollinations(
    prompt: str,
    width: int,
    height: int,
) -> dict:
    settings = get_settings()
    output_dir = Path(settings.output_image_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    encoded_prompt = quote(prompt, safe="")
    response = requests.get(
        f"{settings.pollinations_image_base_url.rstrip('/')}/{encoded_prompt}",
        params={
            "width": width,
            "height": height,
            "nologo": str(settings.pollinations_nologo).lower(),
        },
        timeout=120,
    )
    if response.status_code >= 400:
        return {
            "status": "generation_failed",
            "provider": "pollinations",
            "image_path": None,
            "background_image_path": None,
            "prompt": prompt,
            "error": _read_error_response(response),
        }

    content_type = response.headers.get("Content-Type", "")
    if content_type and not content_type.startswith("image/"):
        return {
            "status": "generation_failed",
            "provider": "pollinations",
            "image_path": None,
            "background_image_path": None,
            "prompt": prompt,
            "error": f"Unexpected content type: {content_type}",
        }

    filename = _background_output_path(output_dir, content_type or "image/png")
    filename.write_bytes(response.content)
    if not filename.exists():
        return {
            "status": "generation_failed",
            "provider": "pollinations",
            "image_path": None,
            "background_image_path": None,
            "prompt": prompt,
            "error": "Image file could not be written.",
        }

    return {
        "status": "generated",
        "provider": "pollinations",
        "image_path": str(filename),
        "background_image_path": str(filename),
        "prompt": prompt,
        "error": None,
    }


def _generate_with_nano_banana(
    *,
    prompt: str,
    negative_prompt: str,
    aspect_ratio: str,
) -> dict:
    settings = get_settings()
    if not settings.gemini_api_key:
        raise RuntimeError(
            "GEMINI_API_KEY is required when IMAGE_PROVIDER is set to nano_banana."
        )

    output_dir = Path(settings.output_image_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    full_prompt = f"{prompt}\n\nAvoid: {negative_prompt}".strip()
    generation_config: dict = {}
    if (
        "3.1-flash-image-preview" in settings.image_model
        or "3-pro-image-preview" in settings.image_model
    ):
        generation_config["imageConfig"] = {
            "aspectRatio": aspect_ratio,
            "imageSize": "1K",
        }
    else:
        generation_config["imageConfig"] = {"aspectRatio": aspect_ratio}
        generation_config["responseModalities"] = ["Image"]

    response = requests.post(
        f"{settings.gemini_api_base.rstrip('/')}/models/{settings.image_model}:generateContent",
        headers={
            "x-goog-api-key": settings.gemini_api_key,
            "Content-Type": "application/json",
        },
        json={
            "contents": [{"parts": [{"text": full_prompt}]}],
            "generationConfig": generation_config,
        },
        timeout=120,
    )
    if response.status_code >= 400:
        raise RuntimeError(
            f"Nano Banana request failed with {response.status_code}: {response.text}"
        )

    payload = response.json()
    candidates = payload.get("candidates", [])
    for candidate in candidates:
        parts = ((candidate.get("content") or {}).get("parts") or [])
        for part in parts:
            inline_data = part.get("inlineData") or part.get("inline_data") or {}
            if not inline_data.get("data"):
                continue
            filename = _background_output_path(
                output_dir,
                inline_data.get("mimeType", "image/png"),
            )
            filename.write_bytes(base64.b64decode(inline_data["data"]))
            return {
                "status": "generated",
                "provider": settings.image_provider,
                "image_path": str(filename),
                "background_image_path": str(filename),
                "prompt": prompt,
                "error": None,
            }
    raise RuntimeError("Nano Banana did not return any image data.")


def _generate_with_diffusers(
    *,
    prompt: str,
    negative_prompt: str,
) -> dict:
    pipe = load_image_pipeline()
    settings = get_settings()
    image = pipe(
        prompt=prompt,
        negative_prompt=negative_prompt,
        num_inference_steps=30,
        guidance_scale=7.5,
    ).images[0]
    output_dir = Path(settings.output_image_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    filename = _background_output_path(output_dir)
    image.save(filename)
    return {
        "status": "generated",
        "provider": settings.image_provider,
        "image_path": str(filename),
        "background_image_path": str(filename),
        "prompt": prompt,
        "error": None,
    }


@tool
def generate_background_image(
    prompt: str,
    provider: str = "pollinations",
    width: int = 1024,
    height: int = 1024,
    negative_prompt: str = DEFAULT_NEGATIVE_PROMPT,
    aspect_ratio: str = "1:1",
) -> dict:
    """
    Generate a background image for publication visuals.
    Returns prompt-only, generated, or generation_failed status.
    """
    settings = get_settings()
    resolved_provider = (provider or settings.image_provider or "pollinations").lower()
    if not settings.enable_image_generation:
        return {
            "status": "prompt_only",
            "provider": resolved_provider,
            "image_path": None,
            "background_image_path": None,
            "prompt": prompt,
            "error": None,
        }

    if resolved_provider == "none":
        return {
            "status": "prompt_only",
            "provider": "none",
            "image_path": None,
            "background_image_path": None,
            "prompt": prompt,
            "error": None,
        }

    try:
        if resolved_provider == "pollinations":
            return _generate_with_pollinations(prompt, width, height)
        if resolved_provider in NANO_BANANA_PROVIDERS:
            try:
                return _generate_with_nano_banana(
                    prompt=prompt,
                    negative_prompt=negative_prompt,
                    aspect_ratio=aspect_ratio,
                )
            except Exception as exc:
                fallback = _generate_with_pollinations(prompt, width, height)
                fallback.setdefault("notes", []).append(
                    f"Primary provider failed, Pollinations fallback used: {exc}"
                )
                return fallback
        if resolved_provider == "diffusers":
            return _generate_with_diffusers(
                prompt=prompt,
                negative_prompt=negative_prompt,
            )
        return {
            "status": "generation_failed",
            "provider": resolved_provider,
            "image_path": None,
            "background_image_path": None,
            "prompt": prompt,
            "error": f"Unsupported image provider: {resolved_provider}",
        }
    except Exception as exc:
        return {
            "status": "generation_failed",
            "provider": resolved_provider,
            "image_path": None,
            "background_image_path": None,
            "prompt": prompt,
            "error": str(exc),
        }


@tool
def generate_ad_image(
    prompt: str,
    negative_prompt: str = DEFAULT_NEGATIVE_PROMPT,
    aspect_ratio: str = "1:1",
) -> dict:
    """
    Backwards-compatible wrapper around background image generation.
    """
    settings = get_settings()
    return generate_background_image.invoke(
        {
            "prompt": prompt,
            "provider": settings.image_provider,
            "width": settings.pollinations_width,
            "height": settings.pollinations_height,
            "negative_prompt": negative_prompt,
            "aspect_ratio": aspect_ratio,
        }
    )
