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

## Local Setup

### Backend on Windows

Use Python `3.11` or `3.12`. The project metadata intentionally rejects Python `3.13+`.

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

### Backend on Linux or macOS

Use `python3.12` when available, otherwise `python3.11`.

If you use `pyenv`, a good local setup is:

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

If `python3.12` is not available, use `python3.11` instead. On Bazzite, Homebrew or a dev container is usually the easiest way to add a compatible Python version.

### Frontend

Vite `7` requires Node.js `20.19+` or `22.12+`.

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

### Optional Ollama bootstrap

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

On Bazzite, the first-class container path is `podman` plus Quadlet rather than Docker. The app still only needs Ollama to answer on `http://localhost:11434`.

Frontend runs on `http://localhost:5173`. Backend runs on `http://127.0.0.1:8000`.

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

## Useful Commands

```text
pytest
ruff check .
npm run build --prefix apps/web
```

## Documentation

- [Product Notes](docs/PRODUCT.md)
- [Architecture](docs/ARCHITECTURE.md)
- [Agents](docs/AGENTS.md)
- [ChromaDB RAG](docs/CHROMADB_RAG.md)
- [API Contracts](docs/API_CONTRACTS.md)
- [Implementation Notes](docs/CODEX_IMPLEMENTATION_NOTES.md)
