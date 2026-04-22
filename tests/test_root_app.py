import importlib.util
from pathlib import Path

from fastapi import FastAPI


def test_root_app_exports_fastapi_app() -> None:
    app_path = Path(__file__).resolve().parents[1] / "app.py"
    spec = importlib.util.spec_from_file_location("root_app_module", app_path)
    assert spec is not None
    assert spec.loader is not None

    root_app = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(root_app)

    assert isinstance(root_app.app, FastAPI)
