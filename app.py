import argparse
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent
API_SRC = PROJECT_ROOT / "apps" / "api" / "src"
if str(API_SRC) not in sys.path:
    sys.path.insert(0, str(API_SRC))

from onebot_ads.main import app as app


def run_onebotads(user_message: str):
    from onebot_ads.core.config import get_settings
    from onebot_ads.services.campaign_service import CampaignService

    settings = get_settings()
    service = CampaignService(settings)
    return service.handle_request(user_message)


def run_cli() -> None:
    print("Agentic OneBotAds CLI")
    print("Type 'exit' or 'quit' to stop.")

    while True:
        user_input = input("OneBotAds > ").strip()
        if user_input.lower() in {"exit", "quit"}:
            break
        if not user_input:
            continue
        result = run_onebotads(user_input)
        print(result.model_dump_json(indent=2))


def run_api(*, host: str = "127.0.0.1", port: int = 8000, reload: bool = False) -> None:
    import uvicorn

    uvicorn.run(
        "app:app",
        host=host,
        port=port,
        reload=reload,
        access_log=True,
        log_level="info",
    )


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1].lower() == "cli":
        run_cli()
    else:
        parser = argparse.ArgumentParser(
            description="Run the Agentic OneBotAds FastAPI app from the repo root."
        )
        parser.add_argument("--host", default="127.0.0.1")
        parser.add_argument("--port", type=int, default=8000)
        parser.add_argument("--reload", action="store_true")
        args = parser.parse_args()
        run_api(host=args.host, port=args.port, reload=args.reload)
