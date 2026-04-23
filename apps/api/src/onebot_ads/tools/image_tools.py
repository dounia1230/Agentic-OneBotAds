import shutil
import time
from functools import lru_cache
from inspect import signature
from pathlib import Path

from langchain.tools import tool

from onebot_ads.core.config import get_settings

DEFAULT_NEGATIVE_PROMPT = (
    "words, letters, text, watermark, logo, distorted UI, unreadable dashboard, "
    "blurry, low quality, fake brand marks"
)
QWEN_IMAGE_PROVIDER = "qwen_image"
HF_SPACE_BACKEND = "huggingface_space"
IMAGE_GENERATION_DISABLED_ERROR = "Image generation is disabled in configuration."
SUPPORTED_IMAGE_PROVIDERS = {QWEN_IMAGE_PROVIDER}


def _clean_fragment(value: str | None, *, max_length: int = 180) -> str | None:
    if value is None:
        return None
    normalized = " ".join(str(value).strip().split()).rstrip(".")
    if not normalized:
        return None
    if len(normalized) <= max_length:
        return normalized
    return normalized[: max_length - 3].rstrip() + "..."


def _dedupe_fragments(values: list[str]) -> list[str]:
    return list(dict.fromkeys(value for value in values if value))


def build_publication_background_prompt(
    *,
    product_name: str,
    audience: str,
    platform: str,
    goal: str | None = None,
    style: str | None = None,
    headline: str | None = None,
    cta: str | None = None,
    brand_context: str | None = None,
    performance_context: list[str] | None = None,
    optimization_context: list[str] | None = None,
    offer: str | None = None,
    key_points: list[str] | None = None,
    brand_constraints: list[str] | None = None,
) -> dict[str, str]:
    prompt_sections = [
        (
            "Create a brand-safe campaign visual background for "
            f"{product_name}, aimed at {audience}, optimized for {platform} publication format."
        )
    ]
    cleaned_goal = _clean_fragment(goal)
    cleaned_offer = _clean_fragment(offer)
    cleaned_headline = _clean_fragment(headline)
    cleaned_cta = _clean_fragment(cta)
    cleaned_brand_context = _clean_fragment(brand_context, max_length=220)
    cleaned_key_points = _dedupe_fragments(
        [
            fragment
            for fragment in (_clean_fragment(item, max_length=80) for item in key_points or [])
            if fragment
        ][:3]
    )
    cleaned_performance = _dedupe_fragments(
        [
            fragment
            for fragment in (
                _clean_fragment(item, max_length=140) for item in performance_context or []
            )
            if fragment
        ][:2]
    )
    cleaned_optimization = _dedupe_fragments(
        [
            fragment
            for fragment in (
                _clean_fragment(item, max_length=140) for item in optimization_context or []
            )
            if fragment
        ][:2]
    )
    cleaned_constraints = _dedupe_fragments(
        [
            fragment
            for fragment in (
                _clean_fragment(item, max_length=80) for item in brand_constraints or []
            )
            if fragment
        ][:3]
    )

    if cleaned_goal:
        prompt_sections.append(f"Visual objective: support a campaign designed to {cleaned_goal}.")
    if cleaned_offer:
        prompt_sections.append(f"Offer cue: frame the scene around {cleaned_offer}.")
    if cleaned_key_points:
        prompt_sections.append(
            "Product cues to suggest visually: " + ", ".join(cleaned_key_points) + "."
        )
    if cleaned_headline:
        prompt_sections.append(
            f"Creative direction should support the headline concept \"{cleaned_headline}\"."
        )
    if cleaned_cta:
        prompt_sections.append(
            f"Leave clear composition space for a CTA such as \"{cleaned_cta}\"."
        )
    if cleaned_brand_context:
        prompt_sections.append(f"Brand guidance: {cleaned_brand_context}.")
    if cleaned_performance:
        prompt_sections.append(
            "Performance context to reflect visually: " + "; ".join(cleaned_performance) + "."
        )
    if cleaned_optimization:
        prompt_sections.append(
            "Optimization focus: " + "; ".join(cleaned_optimization) + "."
        )
    if cleaned_constraints:
        prompt_sections.append(
            "Brand constraints to respect: " + ", ".join(cleaned_constraints) + "."
        )

    prompt_sections.append(
        "Use "
        + (
            _clean_fragment(style, max_length=180)
            or "a polished commercial advertising style, strong focal subject cues, clean "
            "composition, premium lighting, soft depth, and negative space for text overlay"
        )
        + "."
    )
    prompt_sections.append(
        "High quality, campaign-ready, modern, brand-safe, no text, no words, no letters, "
        "no logos, no watermark, no fake UI, no readable labels."
    )
    prompt = " ".join(prompt_sections)

    alt_text = f"{platform} campaign visual for {product_name} aimed at {audience}"
    if cleaned_goal:
        alt_text += f", supporting a goal to {cleaned_goal}"
    alt_text += "."
    return {
        "prompt": prompt,
        "negative_prompt": DEFAULT_NEGATIVE_PROMPT,
        "alt_text": alt_text,
    }


def _background_output_path(output_dir: Path, source_path: Path | None = None) -> Path:
    extension = source_path.suffix if source_path and source_path.suffix else ".png"
    return output_dir / f"background_{int(time.time())}{extension}"


def normalize_image_provider(
    provider: str | None,
    default_provider: str = QWEN_IMAGE_PROVIDER,
) -> tuple[str, str | None]:
    normalized_default = (default_provider or QWEN_IMAGE_PROVIDER).strip().lower()
    if normalized_default not in SUPPORTED_IMAGE_PROVIDERS:
        normalized_default = QWEN_IMAGE_PROVIDER
    resolved_provider = (provider or default_provider or QWEN_IMAGE_PROVIDER).strip().lower()
    if resolved_provider in SUPPORTED_IMAGE_PROVIDERS:
        return resolved_provider, None
    return normalized_default, f"Image provider normalized to {normalized_default}."


def provider_backend(provider: str) -> str:
    return HF_SPACE_BACKEND


def provider_reference(provider: str, settings) -> str | None:
    if provider == QWEN_IMAGE_PROVIDER:
        return settings.qwen_image_space_id
    return None


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


@lru_cache(maxsize=2)
def _get_hf_space_client(space_id: str, hf_token: str | None):
    client_class = _load_client_class()
    return client_class(space_id, **_build_client_kwargs(client_class, hf_token))


@lru_cache(maxsize=2)
def _get_qwen_client(space_id: str, hf_token: str | None):
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
            "and only returned the exception class name; retry later or disable image "
            "generation if it keeps failing)"
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
    backend: str,
    space_id: str | None,
    prompt: str,
    image_path: str | None,
    error: str | None,
    notes: list[str] | None = None,
) -> dict:
    return {
        "status": status,
        "provider": provider,
        "backend": backend,
        "space_id": space_id,
        "image_path": image_path,
        "background_image_path": image_path,
        "prompt": prompt,
        "error": error,
        "notes": notes or [],
        "fallback_used": False,
        "fallback_attempted": False,
        "fallback_succeeded": False,
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
            backend=HF_SPACE_BACKEND,
            space_id=space_id,
            prompt=prompt,
            image_path=str(saved_path),
            error=None,
        )
    except Exception as exc:
        return _build_generation_result(
            status="generation_failed",
            provider=provider,
            backend=HF_SPACE_BACKEND,
            space_id=space_id,
            prompt=prompt,
            image_path=None,
            error=_format_exception_details(exc, provider=provider, include_repr=True),
        )


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


def _generate_background_with_provider(
    *,
    provider: str,
    prompt: str,
    negative_prompt: str,
    aspect_ratio: str,
    output_dir: str,
) -> dict:
    if provider == QWEN_IMAGE_PROVIDER:
        return generate_qwen_image_background(
            prompt=prompt,
            aspect_ratio=aspect_ratio,
            output_dir=output_dir,
        )
    raise RuntimeError(f"Unsupported image provider: {provider}")


@tool
def generate_background_image(
    prompt: str,
    provider: str = QWEN_IMAGE_PROVIDER,
    negative_prompt: str = DEFAULT_NEGATIVE_PROMPT,
    aspect_ratio: str = "1:1",
) -> dict:
    """
    Generate a background image for publication visuals with the configured image backend.
    Returns prompt-only, generated, or generation_failed status.
    """
    settings = get_settings()
    notes: list[str] = []
    requested_provider = provider or settings.image_provider or QWEN_IMAGE_PROVIDER
    resolved_provider, normalization_note = normalize_image_provider(
        requested_provider,
        settings.image_provider or QWEN_IMAGE_PROVIDER,
    )
    if normalization_note:
        notes.append(normalization_note)

    try:
        if not settings.enable_image_generation:
            return _build_generation_result(
                status="generation_failed",
                provider=resolved_provider,
                backend=provider_backend(resolved_provider),
                space_id=provider_reference(resolved_provider, settings),
                prompt=prompt,
                image_path=None,
                error=IMAGE_GENERATION_DISABLED_ERROR,
                notes=notes
                + [
                    "Hosted image generation is disabled in the local-first "
                    "default setup."
                ],
            )

        primary_result = _generate_background_with_provider(
            provider=resolved_provider,
            prompt=prompt,
            negative_prompt=negative_prompt,
            aspect_ratio=aspect_ratio,
            output_dir=str(settings.output_image_dir),
        )
        primary_result["notes"] = notes + primary_result.get("notes", [])
        primary_result["primary_provider"] = resolved_provider
        primary_result["fallback_provider"] = None
        if primary_result["status"] != "generation_failed":
            primary_result["notes"].append(
                f"No fallback provider is configured; {resolved_provider} succeeded."
            )
        else:
            primary_result["notes"].append(
                "No fallback provider is configured in the simplified local-first setup."
            )
        return primary_result
    except Exception as exc:
        return _build_generation_result(
            status="generation_failed",
            provider=resolved_provider,
            backend=provider_backend(resolved_provider),
            space_id=provider_reference(resolved_provider, settings),
            prompt=prompt,
            image_path=None,
            error=(
                "Image generation request failed: "
                f"{_format_exception_details(exc, include_repr=True)}"
            ),
            notes=notes
            + [
                "No fallback provider is configured in the simplified "
                "local-first setup."
            ],
        )


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
