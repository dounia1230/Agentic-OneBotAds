# ChromaDB RAG

## Why ChromaDB

ChromaDB is used as the persistent local vector store for private marketing knowledge. It keeps the MVP simple, local-first, and aligned with the repo guardrail that avoids introducing a second vector database.

## Storage Details

- Persist path: `vector_store/chroma`
- Collection name: `onebotads_kb`
- Embedding model: `nomic-embed-text:latest`
- Text model for query workflows: `qwen3:8b`
- Source documents: `data/knowledge_base`
- Retrieval strategy: semantic search plus metadata filters for shared, brand, and campaign scope

## Recommended Knowledge Layout

Use directory structure to control retrieval scope:

```text
data/knowledge_base/
|- shared/
|  `- platform_ads_rules.md
`- brands/
   `- your-brand/
      |- brand_guidelines.md
      `- campaigns/
         `- holiday-launch/
            `- brief.md
```

Metadata assignment:

- files under `shared/` are indexed as shared knowledge
- files under `brands/<brand>/` are indexed as brand knowledge
- files under `brands/<brand>/campaigns/<campaign>/` are indexed as campaign knowledge
- legacy files at the root are treated as belonging to the repo's default brand

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

## Postman Quick Test

Use Postman after the FastAPI app is running on `http://127.0.0.1:8000`.

### Step 1: Reindex The Knowledge Base

- Method: `POST`
- URL: `http://127.0.0.1:8000/api/v1/rag/reindex`
- Body: none

Expected result:
- a JSON response confirming the index was rebuilt

### Step 2: Query Through The Assistant API

- Method: `POST`
- URL: `http://127.0.0.1:8000/api/v1/assistant/run`
- Header: `Content-Type: application/json`
- Body:

```json
{
  "message": "What are the main audience personas and tone rules for Agentic OneBotAds?",
  "product_name": "Agentic OneBotAds",
  "knowledge_scope": {
    "brand_name": "Agentic OneBotAds"
  },
  "run_all_agents": false,
  "save_output": false,
  "export_report": false
}
```

This message should route to the RAG path because it asks about personas and tone.

Useful test prompts:
- `What are the main audience personas for Agentic OneBotAds?`
- `What tone and wording should the brand avoid?`
- `Summarize the product catalog and safe claims.`
- `What message angles are best for agencies versus SME owners?`

Check these response fields:
- `intent`
- `plan.agents_to_call`
- `rag.answer`
- `rag.relevant_context`
- `rag.source_documents`
- `rag.confidence`

### Step 3: Test A Specific Brand Or Campaign

```json
{
  "message": "What positioning and tone should I use for the Spring Launch plushie campaign?",
  "product_name": "CuddleNest Plushies",
  "knowledge_scope": {
    "brand_name": "CuddleNest Plushies",
    "campaign_name": "Spring Launch"
  },
  "run_all_agents": false,
  "save_output": false,
  "export_report": false
}
```

## Reset The Vector Store

Delete the files inside `vector_store/chroma/`, then rebuild:

```bash
python rag/build_index.py
```

The backend also exposes `POST /api/v1/rag/reindex` for a rebuild from the API.
