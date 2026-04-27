import json

from onebot_ads.core.config import Settings


def build_chat_model(
    settings: Settings,
    *,
    output_json: bool = True,
    num_predict: int = 900,
):
    from langchain_ollama import ChatOllama

    kwargs = {
        "model": settings.llm_model,
        "base_url": settings.ollama_base_url,
        "temperature": settings.llm_temperature,
        "num_predict": num_predict,
        "validate_model_on_init": False,
    }
    if output_json:
        kwargs["format"] = "json"

    return ChatOllama(
        **kwargs,
    )


def extract_json_payload(raw: str) -> dict:
    start = raw.find("{")
    end = raw.rfind("}")
    if start == -1 or end == -1 or start >= end:
        raise ValueError("Model response did not contain a JSON object.")
    return json.loads(raw[start : end + 1])
