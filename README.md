# Agentic OneBotAds

Agentic OneBotAds is a local-first campaign generation workspace for small teams that need AI-assisted ad copy, reusable brand context, and a lightweight review UI before production hardening.

This scaffold is opinionated around:
- `FastAPI` for the backend API
- `LangChain` for prompt orchestration and local-model access
- `LlamaIndex` plus `ChromaDB` for RAG over campaign knowledge
- `React` plus `Vite` for the operator-facing frontend
- `Ollama` with `qwen3:8b` and `nomic-embed-text:latest` for the default local model stack

## Repository Shape

```text
.
|- apps/api/src/onebot_ads
|- apps/web
|- data/knowledge_base
|- data/chroma
|- docs
|- outputs/ad_copy
|- outputs/images
`- tests
```

## MVP Scope

The current scaffold supports:
- a FastAPI app with health, runtime, campaign draft, and RAG reindex endpoints
- a LangChain-powered draft path with deterministic fallback if local AI services are unavailable
- a LlamaIndex plus Chroma knowledge base service boundary
- a React dashboard for entering a campaign brief and reviewing draft output
- starter docs, sample knowledge-base content, and baseline tests

## Local Setup

Backend:

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -e .[dev]
copy .env.example .env
python -m uvicorn onebot_ads.main:app --reload
```

Frontend:

```powershell
npm install --prefix apps/web
npm run dev --prefix apps/web
```

Optional Ollama bootstrap:

```powershell
ollama pull qwen3:8b
ollama pull nomic-embed-text:latest
```

Frontend runs on `http://localhost:5173`. Backend runs on `http://127.0.0.1:8000`.

## Useful Commands

```powershell
pytest
ruff check .
npm run build --prefix apps/web
```

## Documentation

- [Product Notes](docs/PRODUCT.md)
- [Architecture](docs/ARCHITECTURE.md)
- [Setup Guide](docs/SETUP.md)
- [Testing Guide](docs/TESTING.md)
- [Roadmap](docs/ROADMAP.md)
- [Decisions](docs/DECISIONS.md)
