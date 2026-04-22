# ChromaDB RAG

## Why ChromaDB

ChromaDB is used as the persistent local vector store for private marketing knowledge. It keeps the MVP simple, local-first, and aligned with the repo guardrail that avoids introducing a second vector database.

## Storage Details

- Persist path: `vector_store/chroma`
- Collection name: `onebotads_kb`
- Embedding model: `nomic-embed-text:latest`
- Text model for query workflows: `qwen3:8b`
- Source documents: `data/knowledge_base`

## Build The Index

Run the Ollama pulls first, then build the persistent index:

```bash
ollama pull qwen3:8b
ollama pull nomic-embed-text:latest

python rag/build_index.py
python app.py --reload
```

`python rag/build_index.py` calls the backend `onebot_ads.rag.build_index` module and writes vectors into `vector_store/chroma`.

## Query The Index

- CLI path: ask a brand/product/tone question in `python app.py cli`.
- API path: `POST /api/v1/assistant/run` or `POST /api/v1/rag/reindex` after changing files.
- Internal code path: `onebot_ads.rag.query_engine.get_query_engine()`.

## Add New Knowledge Files

1. Add Markdown or text files under `data/knowledge_base/`.
2. Rebuild the index with `python rag/build_index.py`.
3. Ask the CLI or API a grounded question to verify retrieval.

## Reset The Vector Store

Delete the files inside `vector_store/chroma/`, then rebuild:

```bash
python rag/build_index.py
```

The backend also exposes `POST /api/v1/rag/reindex` for a rebuild from the API.
