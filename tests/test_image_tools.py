import json
from pathlib import Path

from gradio_client.exceptions import AppError

from onebot_ads.tools.image_tools import (
    QWEN_IMAGE_PROVIDER,
    _format_exception_details,
    build_publication_background_prompt,
    generate_ad_image,
    generate_background_image,
)
from onebot_ads.tools.path_tools import to_outputs_url


def test_build_publication_background_prompt_uses_richer_context() -> None:
    spec = build_publication_background_prompt(
        product_name="Agentic OneBotAds",
        audience="SMEs and marketing teams",
        platform="LinkedIn",
        goal="increase qualified leads",
        style="modern editorial SaaS advertising with clean hierarchy",
        headline="Smarter campaign execution for SMEs",
        cta="Book a demo",
        brand_context="Use direct, practical, and credible messaging.",
        performance_context=["Scale cues from ALT003, the current best campaign."],
        optimization_context=["Increase budget on ALT003 by 15-20%."],
        offer="7-day pilot",
        key_points=["faster launches", "brand-safe drafts"],
        brand_constraints=["avoid hype", "no guaranteed outcomes"],
    )

    assert "increase qualified leads" in spec["prompt"]
    assert "Smarter campaign execution for SMEs" in spec["prompt"]
    assert "Book a demo" in spec["prompt"]
    assert "Scale cues from ALT003" in spec["prompt"]
    assert "avoid hype" in spec["prompt"]
    assert spec["alt_text"] == (
        "LinkedIn campaign visual for Agentic OneBotAds aimed at SMEs and marketing teams, "
        "supporting a goal to increase qualified leads."
    )


def test_generate_ad_image_uses_qwen_huggingface_space(
    monkeypatch,
    tmp_path: Path,
) -> None:
    captured = {}
    generated_source = tmp_path / "hf-temp-image.png"
    generated_source.write_bytes(b"fake-image-bytes")

    class StubSettings:
        enable_image_generation = True
        image_provider = QWEN_IMAGE_PROVIDER
        qwen_image_space_id = "Qwen/Qwen-Image-2512"
        hf_token = None
        output_image_dir = tmp_path

    class FakeClient:
        def view_api(self, return_format="dict"):
            return {"named_endpoints": {"/infer": {"parameters": []}}}

        def predict(self, *args, **kwargs):
            captured["args"] = args
            captured["kwargs"] = kwargs
            return [str(generated_source), 12345]

    monkeypatch.setattr("onebot_ads.tools.image_tools.get_settings", lambda: StubSettings())
    monkeypatch.setattr(
        "onebot_ads.tools.image_tools._get_qwen_client",
        lambda space_id, hf_token: FakeClient(),
    )

    result = generate_ad_image.invoke(
        {
            "prompt": "Create a campaign visual",
            "negative_prompt": "blurry",
            "aspect_ratio": "16:9",
        }
    )

    assert result["status"] == "generated"
    assert result["provider"] == QWEN_IMAGE_PROVIDER
    assert result["backend"] == "huggingface_space"
    assert result["space_id"] == "Qwen/Qwen-Image-2512"
    assert Path(result["image_path"]).exists()
    assert captured["args"][:4] == ("Create a campaign visual", 0, True, "16:9")
    assert captured["kwargs"]["api_name"] == "/infer"


def test_generate_background_image_normalizes_unsupported_provider(
    monkeypatch,
    tmp_path: Path,
) -> None:
    generated_source = tmp_path / "hf-temp-image.png"
    generated_source.write_bytes(b"fake-image-bytes")

    class StubSettings:
        enable_image_generation = True
        image_provider = QWEN_IMAGE_PROVIDER
        qwen_image_space_id = "Qwen/Qwen-Image-2512"
        hf_token = None
        output_image_dir = tmp_path

    class FakeClient:
        def view_api(self, return_format="dict"):
            return {"named_endpoints": {"/infer": {"parameters": []}}}

        def predict(self, *args, **kwargs):
            return str(generated_source)

    monkeypatch.setattr("onebot_ads.tools.image_tools.get_settings", lambda: StubSettings())
    monkeypatch.setattr(
        "onebot_ads.tools.image_tools._get_qwen_client",
        lambda space_id, hf_token: FakeClient(),
    )

    result = generate_background_image.invoke(
        {
            "prompt": "clean professional background",
            "provider": "pollinations",
            "aspect_ratio": "1:1",
        }
    )

    assert result["status"] == "generated"
    assert result["provider"] == QWEN_IMAGE_PROVIDER
    assert result["notes"][0] == "Image provider normalized to qwen_image."


def test_generate_background_image_returns_failure_when_qwen_errors(
    monkeypatch,
    tmp_path: Path,
) -> None:
    class StubSettings:
        enable_image_generation = True
        image_provider = QWEN_IMAGE_PROVIDER
        qwen_image_space_id = "Qwen/Qwen-Image-2512"
        hf_token = None
        output_image_dir = tmp_path

    class FakeClient:
        def view_api(self, return_format="dict"):
            return {"named_endpoints": {"/infer": {"parameters": []}}}

        def predict(self, *args, **kwargs):
            raise RuntimeError("Space unavailable")

    monkeypatch.setattr("onebot_ads.tools.image_tools.get_settings", lambda: StubSettings())
    monkeypatch.setattr(
        "onebot_ads.tools.image_tools._get_qwen_client",
        lambda space_id, hf_token: FakeClient(),
    )

    result = generate_background_image.invoke(
        {
            "prompt": "clean professional background",
            "provider": QWEN_IMAGE_PROVIDER,
            "aspect_ratio": "1:1",
        }
    )

    assert result["status"] == "generation_failed"
    assert result["provider"] == QWEN_IMAGE_PROVIDER
    assert result["fallback_used"] is False
    assert result["fallback_provider"] is None
    assert "Space unavailable" in result["error"]


def test_generate_background_image_returns_failure_when_disabled(
    tmp_path: Path,
    monkeypatch,
) -> None:
    class StubSettings:
        enable_image_generation = False
        image_provider = QWEN_IMAGE_PROVIDER
        qwen_image_space_id = "Qwen/Qwen-Image-2512"
        hf_token = None
        output_image_dir = tmp_path

    monkeypatch.setattr("onebot_ads.tools.image_tools.get_settings", lambda: StubSettings())

    result = generate_background_image.invoke(
        {
            "prompt": "clean professional background",
            "provider": QWEN_IMAGE_PROVIDER,
            "aspect_ratio": "1:1",
        }
    )

    assert result["status"] == "generation_failed"
    assert result["fallback_used"] is False
    assert result["fallback_provider"] is None
    assert "disabled" in result["error"].lower()


def test_format_exception_details_explains_opaque_upstream_app_errors() -> None:
    details = _format_exception_details(
        AppError("RuntimeError"),
        provider=QWEN_IMAGE_PROVIDER,
        include_repr=True,
    )

    assert "AppError: RuntimeError" in details
    assert "upstream Hugging Face Space for qwen_image failed internally" in details


def test_get_qwen_client_uses_supported_token_parameter(monkeypatch) -> None:
    from onebot_ads.tools.image_tools import _get_hf_space_client

    captured = {}

    class FakeClient:
        def __init__(self, src, token=None, verbose=True, httpx_kwargs=None):
            captured["src"] = src
            captured["token"] = token
            captured["verbose"] = verbose
            captured["httpx_kwargs"] = httpx_kwargs

    _get_hf_space_client.cache_clear()
    monkeypatch.setattr("onebot_ads.tools.image_tools._load_client_class", lambda: FakeClient)

    client = _get_hf_space_client("Qwen/Qwen-Image-2512", "test-token")

    assert isinstance(client, FakeClient)
    assert captured == {
        "src": "Qwen/Qwen-Image-2512",
        "token": "test-token",
        "verbose": False,
        "httpx_kwargs": {"timeout": 120.0},
    }


def test_generate_qwen_image_background_uses_integer_seed(monkeypatch, tmp_path: Path) -> None:
    from onebot_ads.tools.image_tools import generate_qwen_image_background

    captured = {}
    generated_source = tmp_path / "hf-temp-image.png"
    generated_source.write_bytes(b"fake-image-bytes")

    class StubSettings:
        qwen_image_space_id = "Qwen/Qwen-Image-2512"
        hf_token = None

    class FakeClient:
        def view_api(self, return_format="dict"):
            return {"named_endpoints": {"/infer": {"parameters": []}}}

        def predict(self, *args, **kwargs):
            captured["args"] = args
            captured["kwargs"] = kwargs
            return [str(generated_source), 12345]

    monkeypatch.setattr("onebot_ads.tools.image_tools.get_settings", lambda: StubSettings())
    monkeypatch.setattr("onebot_ads.tools.image_tools._get_qwen_client", lambda *args: FakeClient())

    result = generate_qwen_image_background(
        prompt="clean abstract background",
        output_dir=str(tmp_path),
    )

    assert result["status"] == "generated"
    assert captured["args"][1] == 0


def test_saved_output_bundle_contains_saved_path(tmp_path: Path) -> None:
    from onebot_ads.core.config import Settings
    from onebot_ads.schemas.campaigns import AssistantResponse, OrchestrationPlan
    from onebot_ads.tools.output_tools import save_assistant_output

    settings = Settings(output_post_dir=tmp_path, outputs_directory=tmp_path)
    result = AssistantResponse(
        intent="full_workflow",
        plan=OrchestrationPlan(
            intent="full_workflow",
            agents_to_call=["image_agent"],
            final_format="full_workflow_bundle",
        ),
        saved_output_path=str(tmp_path / "bundle.json"),
        artifact_paths=[str(tmp_path / "bundle.json")],
    )

    output_path = save_assistant_output(
        result,
        "test request",
        settings=settings,
        output_path=result.saved_output_path,
    )
    saved_payload = json.loads(Path(output_path).read_text(encoding="utf-8"))

    assert saved_payload["saved_output_path"] == str(tmp_path / "bundle.json")


def test_outputs_url_maps_local_output_path() -> None:
    url = to_outputs_url("outputs/images/publication_123.png")

    assert url == "/outputs/images/publication_123.png"
