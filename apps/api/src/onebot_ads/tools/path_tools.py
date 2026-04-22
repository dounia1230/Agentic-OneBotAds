from pathlib import Path

from onebot_ads.core.config import get_settings


def to_outputs_url(file_path: str | None) -> str | None:
    if not file_path:
        return None

    settings = get_settings()
    path = Path(file_path)
    try:
        relative = path.resolve().relative_to(settings.outputs_directory.resolve())
    except Exception:
        try:
            relative = path.relative_to("outputs")
        except Exception:
            return None
    return "/outputs/" + relative.as_posix()
