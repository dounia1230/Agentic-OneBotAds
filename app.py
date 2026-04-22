import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent
API_SRC = PROJECT_ROOT / "apps" / "api" / "src"
if str(API_SRC) not in sys.path:
    sys.path.insert(0, str(API_SRC))


def run_onebotads(user_message: str):
    from onebot_ads.core.config import get_settings
    from onebot_ads.services.campaign_service import CampaignService

    settings = get_settings()
    service = CampaignService(settings)
    return service.handle_request(user_message)


if __name__ == "__main__":
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
