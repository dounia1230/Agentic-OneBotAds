from pathlib import Path

from onebot_ads.core.config import get_settings


def build_rag_index():
    from chromadb import PersistentClient
    from llama_index.core import Settings as LlamaSettings
    from llama_index.core import (
        SimpleDirectoryReader,
        StorageContext,
        VectorStoreIndex,
    )
    from llama_index.embeddings.ollama import OllamaEmbedding
    from llama_index.llms.ollama import Ollama
    from llama_index.vector_stores.chroma import ChromaVectorStore

    settings = get_settings()
    knowledge_path = Path(settings.knowledge_base_path)
    knowledge_path.mkdir(parents=True, exist_ok=True)

    LlamaSettings.llm = Ollama(
        model=settings.llm_model,
        base_url=settings.ollama_base_url,
        request_timeout=settings.llm_request_timeout_seconds,
    )
    LlamaSettings.embed_model = OllamaEmbedding(
        model_name=settings.embed_model,
        base_url=settings.ollama_base_url,
    )

    documents = SimpleDirectoryReader(str(knowledge_path), recursive=True).load_data()

    chroma_client = PersistentClient(path=str(settings.chroma_path))
    chroma_collection = chroma_client.get_or_create_collection(settings.chroma_collection)
    vector_store = ChromaVectorStore(chroma_collection=chroma_collection)
    storage_context = StorageContext.from_defaults(vector_store=vector_store)

    return VectorStoreIndex.from_documents(
        documents,
        storage_context=storage_context,
    )


if __name__ == "__main__":
    build_rag_index()
    print("RAG index created successfully.")
