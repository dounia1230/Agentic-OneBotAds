# AGENTS.md

## Working Rules
- Read the relevant docs and touched files before changing architecture or prompts.
- Keep the repo split cleanly: `apps/api` for backend and agent orchestration, `apps/web` for UI, `data` for local knowledge sources, `outputs` for generated artifacts.
- Prefer small, reversible changes. Update docs when behavior, setup, or structure changes.

## Architecture Guardrails
- Python is the backend language. FastAPI is the API layer.
- LangChain owns prompt orchestration and model interaction.
- LlamaIndex owns ingestion, indexing, and retrieval.
- ChromaDB is the vector store. Do not introduce a second vector DB without explicit approval.
- Keep model/provider access behind thin adapters or service boundaries so Ollama settings can change without rewriting business logic.

## Safety And Verification
- Never hard-code machine-specific absolute paths.
- Do not assume Ollama or models are installed; fail clearly and keep deterministic fallbacks for local UX.
- For backend changes, run at least the relevant tests or a syntax check.
- For frontend changes, run a build or test command when dependencies are available.

## What Not To Do
- Do not collapse agent, RAG, and API code into a single module.
- Do not add CI/CD, cloud infra, or production-only complexity unless requested.
- Do not overwrite user-authored docs or sample data without a reason documented in the diff.
