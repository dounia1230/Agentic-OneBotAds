def get_query_engine(similarity_top_k: int = 5):
    from chromadb import PersistentClient
    from llama_index.core import Settings as LlamaSettings
    from llama_index.core import VectorStoreIndex
    from llama_index.embeddings.ollama import OllamaEmbedding
    from llama_index.llms.ollama import Ollama
    from llama_index.vector_stores.chroma import ChromaVectorStore

    from onebot_ads.core.config import get_settings

    settings = get_settings()
    LlamaSettings.llm = Ollama(
        model=settings.llm_model,
        base_url=settings.ollama_base_url,
        request_timeout=settings.llm_request_timeout_seconds,
    )
    LlamaSettings.embed_model = OllamaEmbedding(
        model_name=settings.embed_model,
        base_url=settings.ollama_base_url,
    )

    chroma_client = PersistentClient(path=str(settings.chroma_path))
    chroma_collection = chroma_client.get_or_create_collection(settings.chroma_collection)
    vector_store = ChromaVectorStore(chroma_collection=chroma_collection)
    index = VectorStoreIndex.from_vector_store(vector_store)
    return index.as_query_engine(similarity_top_k=similarity_top_k)
