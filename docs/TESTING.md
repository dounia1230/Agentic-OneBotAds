# Testing Guide

## Backend

Run the backend tests after installing dependencies:

```powershell
pytest
ruff check .
```

Current backend coverage focuses on:
- API health wiring
- deterministic campaign draft fallback behavior

## Frontend

Run a build and the lightweight Vitest suite:

```powershell
npm run build --prefix apps/web
npm run test --prefix apps/web
```

Current frontend coverage focuses on:
- basic rendering sanity for the operator UI

## What Is Intentionally Deferred

- end-to-end browser automation
- load or concurrency testing
- RAG integration tests against a provisioned Ollama stack
