# Setup Guide

## Prerequisites

- Python `3.11`
- Node.js and npm for the existing web workspace
- Ollama installed locally if you want live text generation

## Backend CLI And API

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
copy .env.example .env
python rag/build_index.py
python app.py
```

To run the FastAPI server instead of the CLI:

```powershell
pip install -e .[dev]
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

## Environment Notes

- Keep `.env` local; it is ignored by git.
- Generated images stay under `outputs/images`.
- Report exports stay under `outputs/reports`.
- Chroma persistence stays under `vector_store/chroma`.
