# Decisions

## Confirmed

- The project is a combined AI tool, backend service, and web app.
- The first milestone optimizes for fastest MVP with maintainable separation of concerns.
- The repository stays as a single codebase with `apps/api` and `apps/web`, not a heavier workspace toolchain.
- Ollama is the default local provider, with `qwen3:8b` for chat and `nomic-embed-text:latest` for embeddings.
- LlamaIndex plus Chroma is the RAG path.

## Intentional Tradeoffs

- The backend includes a deterministic fallback when local model dependencies are missing or unavailable.
- Image generation is scaffolded as a configuration boundary, but generation execution is deferred until the text path is stable.
- CI/CD is deferred; the repo is optimized for local development first.

## Deferred Decisions

- whether to move orchestration to a graph runtime once the workflow becomes multi-step
- which exact image model to standardize on for local creative generation
- how draft outputs will be persisted and reviewed over time
