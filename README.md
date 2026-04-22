# Agentic OneBotAds

Agentic OneBotAds is a local-first multi-agent advertising assistant. It retrieves private brand context with RAG, analyzes campaign performance, drafts ad copy, generates image prompts, runs compliance checks, and assembles publication-ready outputs for review.

## Stack

- Python and FastAPI for the backend
- LangChain for prompt orchestration and tool wrappers
- LlamaIndex plus ChromaDB for persistent RAG
- Ollama with `qwen3:8b` and `nomic-embed-text:latest`
- Optional Diffusers-based image generation

## Repo Shape

```text
.
|- app.py
|- apps/api/src/onebot_ads
|- apps/web
|- data
|- docs
|- outputs
|- rag
`- vector_store
```

## Run

```bash
pip install -r requirements.txt
ollama pull qwen3:8b
ollama pull nomic-embed-text:latest
python rag/build_index.py
python app.py
```

## Example CLI Requests

- `Analyze my campaigns.`
- `Create a LinkedIn publication with image for Agentic OneBotAds targeting SMEs.`
- `What tone should I use for OneBotAds ads?`
- `How should I optimize my budget?`

## API Endpoints

- `GET /api/v1/health`
- `GET /api/v1/runtime`
- `POST /api/v1/campaigns/draft`
- `POST /api/v1/assistant/run`
- `POST /api/v1/rag/reindex`

## Documentation

- [Product Notes](docs/PRODUCT.md)
- [Architecture](docs/ARCHITECTURE.md)
- [Agents](docs/AGENTS.md)
- [ChromaDB RAG](docs/CHROMADB_RAG.md)
- [API Contracts](docs/API_CONTRACTS.md)
- [Implementation Notes](docs/CODEX_IMPLEMENTATION_NOTES.md)
