import json

from onebot_ads.core.config import Settings


def build_chat_model(settings: Settings):
    from langchain_ollama import ChatOllama

    return ChatOllama(
        model=settings.llm_model,
        base_url=settings.ollama_base_url,
        temperature=settings.llm_temperature,
        num_predict=900,
        validate_model_on_init=False,
        format="json",
    )


def extract_json_payload(raw: str) -> dict:
    start = raw.find("{")
    end = raw.rfind("}")
    if start == -1 or end == -1 or start >= end:
        raise ValueError("Model response did not contain a JSON object.")
    return json.loads(raw[start : end + 1])
