import base64
import json
from pathlib import Path

from onebot_ads.tools.image_tools import generate_ad_image, generate_background_image
from onebot_ads.tools.path_tools import to_outputs_url


class _FakeResponse:
    status_code = 200
    text = '{"ok":true}'

    def raise_for_status(self) -> None:
        return None

    def json(self) -> dict:
        return {
            "candidates": [
                {
                    "content": {
                        "parts": [
                            {
                                "inlineData": {
                                    "data": base64.b64encode(b"fake-image-bytes").decode(),
                                    "mimeType": "image/png",
                                }
                            }
                        ]
                    }
                }
            ]
        }


def test_generate_ad_image_supports_nano_banana(monkeypatch, tmp_path: Path) -> None:
    captured_request = {}

    class StubSettings:
        enable_image_generation = True
        image_provider = "nano_banana"
        image_model = "gemini-2.5-flash-image"
        gemini_api_key = "test-key"
        gemini_api_base = "https://generativelanguage.googleapis.com/v1beta"
        llm_request_timeout_seconds = 90.0
        output_image_dir = tmp_path
        pollinations_width = 1024
        pollinations_height = 1024

    monkeypatch.setattr("onebot_ads.tools.image_tools.get_settings", lambda: StubSettings())

    def fake_post(*args, **kwargs):
        captured_request["json"] = kwargs["json"]
        return _FakeResponse()

    monkeypatch.setattr("onebot_ads.tools.image_tools.requests.post", fake_post)

    result = generate_ad_image.invoke(
        {
            "prompt": "Create a campaign visual",
            "negative_prompt": "blurry",
            "aspect_ratio": "16:9",
        }
    )

    assert result["status"] == "generated"
    assert result["image_path"] is not None
    assert Path(result["image_path"]).exists()
    assert captured_request["json"]["generationConfig"]["responseModalities"] == ["Image"]


def test_generate_ad_image_uses_preview_image_config_for_gemini_31(
    monkeypatch,
    tmp_path: Path,
) -> None:
    captured_request = {}

    class StubSettings:
        enable_image_generation = True
        image_provider = "nano_banana"
        image_model = "gemini-3.1-flash-image-preview"
        gemini_api_key = "test-key"
        gemini_api_base = "https://generativelanguage.googleapis.com/v1beta"
        llm_request_timeout_seconds = 90.0
        output_image_dir = tmp_path
        pollinations_width = 1024
        pollinations_height = 1024

    monkeypatch.setattr("onebot_ads.tools.image_tools.get_settings", lambda: StubSettings())

    def fake_post(*args, **kwargs):
        captured_request["json"] = kwargs["json"]
        return _FakeResponse()

    monkeypatch.setattr("onebot_ads.tools.image_tools.requests.post", fake_post)

    result = generate_ad_image.invoke(
        {
            "prompt": "Create a campaign visual",
            "negative_prompt": "blurry",
            "aspect_ratio": "16:9",
        }
    )

    assert result["status"] == "generated"
    assert captured_request["json"]["generationConfig"]["imageConfig"]["imageSize"] == "1K"
    assert "responseModalities" not in captured_request["json"]["generationConfig"]


def test_generate_background_image_supports_pollinations(monkeypatch, tmp_path: Path) -> None:
    class StubSettings:
        enable_image_generation = True
        image_provider = "pollinations"
        image_model = "unused"
        gemini_api_key = None
        gemini_api_base = "https://generativelanguage.googleapis.com/v1beta"
        llm_request_timeout_seconds = 90.0
        output_image_dir = tmp_path
        pollinations_image_base_url = "https://image.pollinations.ai/prompt"
        pollinations_nologo = True
        pollinations_width = 1024
        pollinations_height = 1024

    class FakePollinationsResponse:
        status_code = 200
        headers = {"Content-Type": "image/png"}
        content = b"fake-image-content"
        text = ""

        def json(self):
            raise ValueError

    monkeypatch.setattr("onebot_ads.tools.image_tools.get_settings", lambda: StubSettings())
    monkeypatch.setattr(
        "onebot_ads.tools.image_tools.requests.get",
        lambda *args, **kwargs: FakePollinationsResponse(),
    )

    result = generate_background_image.invoke(
        {
            "prompt": "clean professional background",
            "provider": "pollinations",
            "width": 1024,
            "height": 1024,
        }
    )

    assert result["status"] == "generated"
    assert result["provider"] == "pollinations"
    assert result["background_image_path"] is not None
    assert Path(result["background_image_path"]).exists()


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
