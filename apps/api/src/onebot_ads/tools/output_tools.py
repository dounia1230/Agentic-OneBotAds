import re
from datetime import datetime
from pathlib import Path

from onebot_ads.core.config import Settings, get_settings
from onebot_ads.schemas.campaigns import AssistantResponse


def build_assistant_output_path(
    request_text: str,
    settings: Settings | None = None,
) -> str:
    resolved_settings = settings or get_settings()
    output_dir = Path(resolved_settings.output_post_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    slug = re.sub(r"[^a-z0-9]+", "_", request_text.lower()).strip("_")
    slug = slug[:50] or "assistant_run"
    filename = output_dir / f"{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}_{slug}.json"
    return str(filename)


def save_assistant_output(
    result: AssistantResponse,
    request_text: str,
    settings: Settings | None = None,
    output_path: str | None = None,
) -> str:
    resolved_settings = settings or get_settings()

    if output_path:
        filename = Path(output_path)
    else:
        filename = Path(build_assistant_output_path(request_text, settings=resolved_settings))
    filename.write_text(result.model_dump_json(indent=2), encoding="utf-8")
    return str(filename)
