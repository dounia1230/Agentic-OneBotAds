# Setup Guide

## Prerequisites

- Python `3.11` or `3.12`
- Node.js `20.19+` or `22.12+` and npm
- Ollama available at `http://localhost:11434` if you want live model responses

## Frontend-First Workflow

If you are mainly working in `apps/web`, you can install frontend dependencies and start the Vite dev server independently:

Windows:

```powershell
npm install --prefix apps/web
npm run dev --prefix apps/web
```

Linux or macOS:

```bash
npm install --prefix apps/web
npm run dev --prefix apps/web
```

The UI will still render if the backend is unavailable, but API-backed draft generation requires the FastAPI app.

## Backend on Windows

Use a compatible interpreter. Python `3.13+` is not supported by this project.

Package-based FastAPI setup:

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip setuptools wheel
pip install -e .[dev]
copy .env.example .env
python -m uvicorn onebot_ads.main:app --reload
```

Legacy CLI or `app.py` path:

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
copy .env.example .env
python rag/build_index.py
python app.py
```

## Backend on Linux or macOS

Use a compatible interpreter. Python `3.13+` is not supported by this project.

If you use `pyenv`, you can pin the repo first:

```bash
pyenv install 3.12.13
pyenv local 3.12.13
```

Package-based FastAPI setup:

```bash
python3.12 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip setuptools wheel
pip install -e ".[dev]"
cp .env.example .env
python -m uvicorn onebot_ads.main:app --reload
```

Legacy CLI or `app.py` path:

```bash
python3.12 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
python rag/build_index.py
python app.py
```

If `python3.12` is unavailable, substitute `python3.11`.

### Bazzite Notes

- The host image may not expose a compatible Python or Node version by default.
- Homebrew is a good fit for user-space CLI tooling on Bazzite.
- For containerized services, Bazzite documents `podman` plus Quadlet as the preferred host workflow.
- Use `rpm-ostree` package layering only as a last resort for system-level packages.

## Ollama Models

Windows:

```powershell
ollama pull qwen3:8b
ollama pull nomic-embed-text:latest
```

Linux or macOS:

```bash
ollama pull qwen3:8b
ollama pull nomic-embed-text:latest
```

The default app configuration expects Ollama at `http://localhost:11434`.

## Knowledge Base

Build the initial index with:

Windows:

```powershell
python rag/build_index.py
```

Linux or macOS:

```bash
python rag/build_index.py
```

If you are using the FastAPI app, you can also reindex through the API:

Windows:

```powershell
Invoke-RestMethod -Method Post -Uri http://127.0.0.1:8000/api/v1/rag/reindex
```

Linux or macOS:

```bash
curl -X POST http://127.0.0.1:8000/api/v1/rag/reindex
```

## Environment Notes

- Keep `.env` local; it is ignored by git.
- Generated images stay under `outputs/images`.
- Report exports stay under `outputs/reports`.
- Chroma persistence stays under `vector_store/chroma`.
