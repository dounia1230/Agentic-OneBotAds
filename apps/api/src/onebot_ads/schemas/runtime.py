from pydantic import BaseModel, Field


class RuntimeSummary(BaseModel):
    app_name: str
    environment: str
    api_prefix: str
    ollama_base_url: str
    ollama_chat_model: str
    ollama_embedding_model: str
    rag_enabled: bool
    image_generation_enabled: bool
    image_provider: str
    image_model: str
    knowledge_base_directory: str
    outputs_directory: str


class HealthResponse(BaseModel):
    status: str
    environment: str
    live_llm_enabled: bool
    rag_enabled: bool


class ReindexResponse(BaseModel):
    documents_indexed: int
    collection_name: str
    persist_directory: str
    notes: list[str] = Field(default_factory=list)
