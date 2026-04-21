# Setup Guide

## Prerequisites

- Python `3.11`
- Node.js and npm
- Ollama installed locally if you want live model responses

## Backend

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -e .[dev]
copy .env.example .env
python -m uvicorn onebot_ads.main:app --reload
```

## Frontend

```powershell
npm install --prefix apps/web
npm run dev --prefix apps/web
```

## Ollama Models

```powershell
ollama pull qwen3:8b
ollama pull nomic-embed-text:latest
```

The default app configuration expects Ollama at `http://localhost:11434`.

## Knowledge Base

Starter knowledge documents live in [data/knowledge_base/example_brand_playbook.md](../data/knowledge_base/example_brand_playbook.md). Reindex them with:

```powershell
Invoke-RestMethod -Method Post -Uri http://127.0.0.1:8000/api/v1/rag/reindex
```

## Environment Notes

- Keep `.env` local; it is ignored by git.
- Generated artifacts stay under `outputs/`.
- Chroma persistence stays under `data/chroma/`.
