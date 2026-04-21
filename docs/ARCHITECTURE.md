# Architecture

## Top-Level Shape

```text
apps/api
  FastAPI entrypoints, orchestration services, agent logic, RAG integration
apps/web
  React operator UI for campaign briefing and draft review
data/knowledge_base
  Local brand, offer, audience, and campaign reference material
data/chroma
  Persistent Chroma data created during local indexing
outputs
  Generated ad copy exports and image artifacts
```

## Backend Boundaries

- `api/`: HTTP routes and dependency wiring
- `services/`: application-level orchestration exposed to the API
- `agents/`: prompt-driven campaign drafting behavior
- `rag/`: document indexing and retrieval via LlamaIndex and Chroma
- `tools/`: deterministic helpers such as channel guardrails and CTA defaults
- `schemas/`: request and response contracts
- `core/`: env-driven configuration

## Request Flow

1. The frontend submits a `CampaignBrief` to `POST /api/v1/campaigns/draft`.
2. The backend optionally retrieves matching context from the local knowledge base.
3. The campaign agent composes prompt inputs and attempts live Ollama generation through LangChain.
4. If live generation is unavailable, the service falls back to deterministic template assembly so the UI stays usable.
5. Structured results are returned to the frontend, with warnings when the system had to degrade.

## Why This Shape

- It keeps the MVP runnable without cloud dependencies.
- It keeps agent logic separate from storage and transport.
- It avoids committing too early to a larger workflow engine while preserving a clean upgrade path.

## Upgrade Path

The current orchestration is intentionally bounded. If the product moves into multi-step approval loops, campaign planning graphs, or background task coordination, add a dedicated workflow layer instead of inflating route handlers or prompt modules.
