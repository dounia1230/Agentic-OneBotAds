# Codex Implementation Notes

## MVP Priority

Build first:
1. ChromaDB RAG indexing
2. RAG query tool
3. Campaign analytics tool
4. Main LangChain agent
5. Publication generation workflow
6. Image prompt generation
7. Optional image generation with Diffusers

Then add:
1. Full separate agent modules
2. Compliance review
3. Reporting output files
4. Better CLI formatting
5. Tests

## Important Implementation Rules

- Do not hardcode private facts outside `data/knowledge_base`.
- Do not claim image generation succeeded unless a file path is returned.
- Use the same language as the user.
- Keep JSON outputs parseable.
- Handle missing CSV columns safely.
- Keep ChromaDB persistent at `vector_store/chroma`.
