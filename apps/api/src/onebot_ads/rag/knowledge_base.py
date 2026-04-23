from onebot_ads.core.config import Settings
from onebot_ads.rag.metadata import (
    build_knowledge_file_metadata,
    build_retrieval_filters,
    normalize_scope_value,
)
from onebot_ads.schemas.campaigns import ContextSnippet, ReindexResponse
from onebot_ads.schemas.knowledge import KnowledgeScope


class KnowledgeBaseService:
    def __init__(self, settings: Settings) -> None:
        self.settings = settings
        self._index = None

    def reindex(self) -> ReindexResponse:
        try:
            indexed_count = self._rebuild_index()
            return ReindexResponse(
                documents_indexed=indexed_count,
                collection_name=self.settings.chroma_collection_name,
                persist_directory=str(self.settings.chroma_persist_directory),
                notes=[],
            )
        except Exception as exc:
            return ReindexResponse(
                documents_indexed=0,
                collection_name=self.settings.chroma_collection_name,
                persist_directory=str(self.settings.chroma_persist_directory),
                notes=[f"RAG reindex failed: {exc}"],
            )

    def retrieve(
        self,
        query: str,
        top_k: int = 3,
        scope: KnowledgeScope | None = None,
    ) -> list[ContextSnippet]:
        if not query.strip():
            return []

        try:
            index = self._index or self._load_or_build_index()
            if index is None:
                return []

            # Use the retriever directly so snippet lookup does not depend on
            # an LLM-backed response synthesizer.
            retriever = index.as_retriever(
                similarity_top_k=top_k,
                filters=build_retrieval_filters(scope),
            )
            source_nodes = retriever.retrieve(query)
            snippets: list[ContextSnippet] = []
            for source in source_nodes:
                node = getattr(source, "node", None)
                metadata = getattr(node, "metadata", {}) if node else {}
                text = getattr(node, "text", "") if node else ""
                snippets.append(
                    ContextSnippet(
                        source=(
                            metadata.get("file_name")
                            or metadata.get("filename")
                            or "knowledge-base"
                        ),
                        excerpt=text[:280].strip(),
                        score=getattr(source, "score", None),
                    )
                )
            return snippets
        except Exception:
            return []

    def _load_documents(self) -> list:
        from pathlib import Path

        from llama_index.core import SimpleDirectoryReader

        input_dir = Path(self.settings.knowledge_base_directory)
        if not any(input_dir.iterdir()):
            return []

        default_brand_slug = normalize_scope_value(self.settings.app_name) or "default_brand"
        reader = SimpleDirectoryReader(
            input_dir=str(input_dir),
            recursive=True,
            filename_as_id=True,
            file_metadata=lambda file_path: build_knowledge_file_metadata(
                file_path,
                root_directory=input_dir,
                default_brand_slug=default_brand_slug,
            ),
        )
        return reader.load_data()

    def _load_or_build_index(self):
        from chromadb import PersistentClient
        from llama_index.core import StorageContext, VectorStoreIndex
        from llama_index.embeddings.ollama import OllamaEmbedding
        from llama_index.vector_stores.chroma import ChromaVectorStore

        client = PersistentClient(path=str(self.settings.chroma_persist_directory))
        collection = client.get_or_create_collection(self.settings.chroma_collection_name)
        vector_store = ChromaVectorStore(chroma_collection=collection)
        storage_context = StorageContext.from_defaults(vector_store=vector_store)
        embed_model = OllamaEmbedding(
            model_name=self.settings.ollama_embedding_model,
            base_url=self.settings.ollama_base_url,
        )

        if collection.count() == 0:
            self._rebuild_index()
            return self._index

        self._index = VectorStoreIndex.from_vector_store(
            vector_store,
            storage_context=storage_context,
            embed_model=embed_model,
        )
        return self._index

    def _rebuild_index(self):
        import chromadb
        from llama_index.core import StorageContext, VectorStoreIndex
        from llama_index.core.node_parser import SentenceSplitter
        from llama_index.embeddings.ollama import OllamaEmbedding
        from llama_index.vector_stores.chroma import ChromaVectorStore

        documents = self._load_documents()
        if not documents:
            self._index = None
            return 0

        client = chromadb.PersistentClient(path=str(self.settings.chroma_persist_directory))
        try:
            client.delete_collection(self.settings.chroma_collection_name)
        except Exception:
            pass

        collection = client.get_or_create_collection(self.settings.chroma_collection_name)
        vector_store = ChromaVectorStore(chroma_collection=collection)
        storage_context = StorageContext.from_defaults(vector_store=vector_store)
        embed_model = OllamaEmbedding(
            model_name=self.settings.ollama_embedding_model,
            base_url=self.settings.ollama_base_url,
        )
        self._index = VectorStoreIndex.from_documents(
            documents,
            storage_context=storage_context,
            embed_model=embed_model,
            transformations=[SentenceSplitter(chunk_size=600, chunk_overlap=80)],
            show_progress=False,
        )
        return len(documents)
