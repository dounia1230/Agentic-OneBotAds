import shutil
import time
from inspect import signature
from functools import lru_cache
from pathlib import Path

from langchain.tools import tool

from onebot_ads.core.config import get_settings

DEFAULT_NEGATIVE_PROMPT = (
    "words, letters, text, watermark, logo, distorted UI, unreadable dashboard, "
    "blurry, low quality, fake brand marks"
)
QWEN_IMAGE_PROVIDER = "qwen_image"
FLUX_IMAGE_PROVIDER = "flux_schnell"
HF_SPACE_BACKEND = "huggingface_space"
IMAGE_GENERATION_DISABLED_ERROR = "Image generation is disabled in configuration."
ASPECT_RATIO_DIMENSIONS = {
    "1:1": (1024, 1024),
    "16:9": (1344, 768),
    "9:16": (768, 1344),
    "4:3": (1152, 864),
    "3:4": (864, 1152),
    "3:2": (1216, 832),
    "2:3": (832, 1216),
}


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


def _background_output_path(output_dir: Path, source_path: Path | None = None) -> Path:
    extension = source_path.suffix if source_path and source_path.suffix else ".png"
    return output_dir / f"background_{int(time.time())}{extension}"


def _load_client_class():
    try:
        from gradio_client import Client
    except ImportError as exc:
        raise RuntimeError(
            "gradio_client is required for Hugging Face image generation. Install it first."
        ) from exc
    return Client


def _build_client_kwargs(client_class, hf_token: str | None) -> dict:
    client_signature = signature(client_class.__init__)
    kwargs = {}
    if hf_token and "token" in client_signature.parameters:
        kwargs["token"] = hf_token
    if "verbose" in client_signature.parameters:
        kwargs["verbose"] = False
    if "httpx_kwargs" in client_signature.parameters:
        kwargs["httpx_kwargs"] = {"timeout": 120.0}
    return kwargs


@lru_cache(maxsize=4)
def _get_hf_space_client(space_id: str, hf_token: str | None):
    client_class = _load_client_class()
    return client_class(space_id, **_build_client_kwargs(client_class, hf_token))


@lru_cache(maxsize=2)
def _get_qwen_client(space_id: str, hf_token: str | None):
    return _get_hf_space_client(space_id, hf_token)


@lru_cache(maxsize=2)
def _get_flux_client(space_id: str, hf_token: str | None):
    return _get_hf_space_client(space_id, hf_token)


def _resolve_predict_api_name(client) -> str:
    try:
        api_info = client.view_api(return_format="dict")
    except TypeError:
        api_info = None
    except Exception:
        api_info = None

    if isinstance(api_info, dict):
        named_endpoints = api_info.get("named_endpoints", {})
        if isinstance(named_endpoints, dict):
            for candidate in ("/infer", "/generate"):
                if candidate in named_endpoints:
                    return candidate
            if named_endpoints:
                return next(iter(named_endpoints))
    return "/infer"


def _extract_local_file_path(value) -> Path | None:
    if value is None:
        return None
    if isinstance(value, Path) and value.exists():
        return value
    if isinstance(value, str):
        candidate = Path(value)
        if candidate.exists():
            return candidate
        return None
    if isinstance(value, dict):
        for key in ("path", "name", "image", "value"):
            path = _extract_local_file_path(value.get(key))
            if path:
                return path
        return None
    if isinstance(value, (list, tuple)):
        for item in value:
            path = _extract_local_file_path(item)
            if path:
                return path
        return None

    for attribute in ("path", "name"):
        if hasattr(value, attribute):
            path = _extract_local_file_path(getattr(value, attribute))
            if path:
                return path
    return None


def _copy_generated_image(source_path: Path, output_dir: Path) -> Path:
    output_dir.mkdir(parents=True, exist_ok=True)
    target_path = _background_output_path(output_dir, source_path)
    shutil.copyfile(source_path, target_path)
    return target_path


def _is_opaque_upstream_app_error(exception_name: str, exception_message: str) -> bool:
    return exception_name == "AppError" and exception_message.endswith("Error")


def _format_exception_details(
    exc: Exception,
    *,
    provider: str | None = None,
    include_repr: bool = False,
) -> str:
    exception_name = type(exc).__name__
    message_candidates: list[str] = []

    explicit_message = getattr(exc, "message", None)
    if isinstance(explicit_message, str) and explicit_message.strip():
        message_candidates.append(explicit_message.strip())

    string_message = str(exc).strip()
    if string_message and string_message not in message_candidates:
        message_candidates.append(string_message)

    for arg in getattr(exc, "args", ()):
        if isinstance(arg, str):
            normalized_arg = arg.strip()
            if normalized_arg and normalized_arg not in message_candidates:
                message_candidates.append(normalized_arg)

    exception_message = message_candidates[0] if message_candidates else ""
    details = f"{exception_name}: {exception_message}" if exception_message else exception_name

    if _is_opaque_upstream_app_error(exception_name, exception_message):
        provider_hint = f" for {provider}" if provider else ""
        details = (
            f"{details} (the upstream Hugging Face Space{provider_hint} failed internally "
            "and only returned the exception class name; retry later or disable this "
            "fallback if it keeps failing)"
        )

    if include_repr:
        exception_repr = repr(exc)
        redundant_reprs = {
            exception_name,
            exception_message,
            details,
            f"{exception_name}('{exception_message}')",
            f'{exception_name}("{exception_message}")',
        }
        if exception_repr and exception_repr not in redundant_reprs:
            details = f"{details} (repr={exception_repr})"
    return details


def _build_generation_result(
    *,
    status: str,
    provider: str,
    space_id: str,
    prompt: str,
    image_path: str | None,
    error: str | None,
    notes: list[str] | None = None,
    fallback_used: bool = False,
    fallback_attempted: bool = False,
    fallback_succeeded: bool = False,
) -> dict:
    return {
        "status": status,
        "provider": provider,
        "backend": HF_SPACE_BACKEND,
        "space_id": space_id,
        "image_path": image_path,
        "background_image_path": image_path,
        "prompt": prompt,
        "error": error,
        "notes": notes or [],
        "fallback_used": fallback_used,
        "fallback_attempted": fallback_attempted,
        "fallback_succeeded": fallback_succeeded,
        "primary_provider": provider,
        "fallback_provider": None,
    }


def _run_hf_space_generation(
    *,
    prompt: str,
    output_dir: str,
    provider: str,
    space_id: str,
    client_getter,
    predict_args: tuple,
) -> dict:
    settings = get_settings()
    output_path = Path(output_dir)
    client = client_getter(space_id, settings.hf_token)
    api_name = _resolve_predict_api_name(client)

    try:
        result = client.predict(*predict_args, api_name=api_name)
        generated_file = _extract_local_file_path(result)
        if not generated_file:
            raise RuntimeError(
                f"{provider} returned an unexpected payload: {type(result).__name__}"
            )

        saved_path = _copy_generated_image(generated_file, output_path)
        if not saved_path.exists():
            raise RuntimeError("Generated image could not be copied to outputs/images.")

        return _build_generation_result(
            status="generated",
            provider=provider,
            space_id=space_id,
            prompt=prompt,
            image_path=str(saved_path),
            error=None,
        )
    except Exception as exc:
        return _build_generation_result(
            status="generation_failed",
            provider=provider,
            space_id=space_id,
            prompt=prompt,
            image_path=None,
            error=_format_exception_details(exc, provider=provider, include_repr=True),
        )


def _flux_dimensions_for(aspect_ratio: str) -> tuple[int, int]:
    return ASPECT_RATIO_DIMENSIONS.get(aspect_ratio, ASPECT_RATIO_DIMENSIONS["1:1"])


def _should_attempt_fallback(error: str | None) -> bool:
    if not error:
        return True
    return IMAGE_GENERATION_DISABLED_ERROR.lower() not in error.lower()


def generate_qwen_image_background(
    prompt: str,
    aspect_ratio: str = "1:1",
    output_dir: str = "outputs/images",
    seed: int = 0,
    randomize_seed: bool = True,
    guidance_scale: float = 4.0,
    num_inference_steps: int = 30,
    prompt_enhance: bool = False,
) -> dict:
    settings = get_settings()
    return _run_hf_space_generation(
        prompt=prompt,
        output_dir=output_dir,
        provider=QWEN_IMAGE_PROVIDER,
        space_id=settings.qwen_image_space_id,
        client_getter=_get_qwen_client,
        predict_args=(
            prompt,
            int(seed),
            randomize_seed,
            aspect_ratio,
            guidance_scale,
            num_inference_steps,
            prompt_enhance,
        ),
    )


def generate_flux_schnell_background(
    prompt: str,
    aspect_ratio: str = "1:1",
    output_dir: str = "outputs/images",
    seed: int = 0,
    randomize_seed: bool = True,
    num_inference_steps: int = 4,
) -> dict:
    settings = get_settings()
    width, height = _flux_dimensions_for(aspect_ratio)
    return _run_hf_space_generation(
        prompt=prompt,
        output_dir=output_dir,
        provider=FLUX_IMAGE_PROVIDER,
        space_id=settings.flux_image_space_id,
        client_getter=_get_flux_client,
        predict_args=(
            prompt,
            int(seed),
            randomize_seed,
            width,
            height,
            num_inference_steps,
        ),
    )


@tool
def generate_background_image(
    prompt: str,
    provider: str = QWEN_IMAGE_PROVIDER,
    negative_prompt: str = DEFAULT_NEGATIVE_PROMPT,
    aspect_ratio: str = "1:1",
) -> dict:
    """
    Generate a background image for publication visuals with the Qwen Image Space.
    Returns prompt-only, generated, or generation_failed status.
    """
    settings = get_settings()
    notes: list[str] = []
    requested_provider = (provider or settings.image_provider or QWEN_IMAGE_PROVIDER).lower()
    resolved_provider = QWEN_IMAGE_PROVIDER
    fallback_provider = settings.image_fallback_provider
    if requested_provider != QWEN_IMAGE_PROVIDER:
        notes.append("Image provider normalized to qwen_image.")

    try:
        if not settings.enable_image_generation:
            result = _build_generation_result(
                status="generation_failed",
                provider=resolved_provider,
                space_id=settings.qwen_image_space_id,
                prompt=prompt,
                image_path=None,
                error=IMAGE_GENERATION_DISABLED_ERROR,
                notes=notes + ["Fallback was not attempted because image generation is disabled."],
            )
            result["fallback_provider"] = fallback_provider
            return result

        primary_result = generate_qwen_image_background(
            prompt=prompt,
            aspect_ratio=aspect_ratio,
            output_dir=str(settings.output_image_dir),
        )
        primary_result["notes"] = notes + primary_result.get("notes", [])
        primary_result["primary_provider"] = QWEN_IMAGE_PROVIDER
        primary_result["fallback_provider"] = fallback_provider
        primary_result["fallback_used"] = False
        primary_result["fallback_attempted"] = False
        primary_result["fallback_succeeded"] = False
        if primary_result["status"] != "generation_failed":
            primary_result["notes"].append(
                f"Fallback was not attempted because {QWEN_IMAGE_PROVIDER} succeeded."
            )
            return primary_result

        fallback_enabled = (
            settings.image_fallback_enabled and fallback_provider == FLUX_IMAGE_PROVIDER
        )
        fallback_eligible = _should_attempt_fallback(primary_result.get("error"))
        if not fallback_enabled:
            primary_result["notes"].append(
                f"Fallback was not attempted because provider {fallback_provider} is disabled."
            )
            return primary_result
        if not fallback_eligible:
            primary_result["notes"].append(
                "Fallback was not attempted because the primary error is not eligible."
            )
            return primary_result

        fallback_notes = primary_result["notes"] + [
            f"Primary provider {QWEN_IMAGE_PROVIDER} failed: {primary_result.get('error')}",
            f"Attempting fallback provider {FLUX_IMAGE_PROVIDER}.",
        ]
        fallback_result = generate_flux_schnell_background(
            prompt=prompt,
            aspect_ratio=aspect_ratio,
            output_dir=str(settings.output_image_dir),
        )
        fallback_result["notes"] = fallback_notes + fallback_result.get("notes", [])
        fallback_result["fallback_used"] = True
        fallback_result["fallback_attempted"] = True
        fallback_result["fallback_succeeded"] = False
        fallback_result["primary_provider"] = QWEN_IMAGE_PROVIDER
        fallback_result["fallback_provider"] = FLUX_IMAGE_PROVIDER
        if fallback_result["status"] != "generation_failed":
            fallback_result["error"] = None
            fallback_result["fallback_used"] = True
            fallback_result["fallback_succeeded"] = True
            fallback_result["notes"].append(
                f"Fallback provider {FLUX_IMAGE_PROVIDER} succeeded."
            )
            return fallback_result

        fallback_error = fallback_result.get("error") or "Unknown fallback error."
        fallback_result["notes"].append(
            f"Fallback provider {FLUX_IMAGE_PROVIDER} failed: {fallback_error}"
        )
        fallback_result["error"] = (
            f"Qwen failed: {primary_result.get('error')}; "
            f"FLUX fallback failed: {fallback_error}"
        )
        return fallback_result
    except Exception as exc:
        result = _build_generation_result(
            status="generation_failed",
            provider=resolved_provider,
            space_id=settings.qwen_image_space_id,
            prompt=prompt,
            image_path=None,
            error=f"Image generation request failed: {_format_exception_details(exc, include_repr=True)}",
            notes=notes + ["Fallback outcome is unknown because generation failed before a provider response was returned."],
        )
        result["fallback_provider"] = fallback_provider
        return result


@tool
def generate_ad_image(
    prompt: str,
    negative_prompt: str = DEFAULT_NEGATIVE_PROMPT,
    aspect_ratio: str = "1:1",
) -> dict:
    """
    Backwards-compatible wrapper around Qwen background generation.
    """
    settings = get_settings()
    return generate_background_image.invoke(
        {
            "prompt": prompt,
            "provider": settings.image_provider,
            "negative_prompt": negative_prompt,
            "aspect_ratio": aspect_ratio,
        }
    )
