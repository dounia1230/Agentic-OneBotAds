from functools import lru_cache

from langchain.tools import tool

from onebot_ads.core.config import get_settings
from onebot_ads.rag.knowledge_base import KnowledgeBaseService


@lru_cache
def get_knowledge_base_service() -> KnowledgeBaseService:
    return KnowledgeBaseService(get_settings())


@tool
def marketing_rag_search(question: str) -> str:
    """
    Search the private marketing knowledge base using RAG.
    Use this for brand guidelines, marketing rules, product context,
    audience personas, platform rules, and previous ads.
    """
    snippets = get_knowledge_base_service().retrieve(question, top_k=5)
    if not snippets:
        return "No grounded marketing context was found in the knowledge base."

    lines = []
    for snippet in snippets:
        score = f"{snippet.score:.2f}" if snippet.score is not None else "n/a"
        lines.append(f"[{snippet.source} | score={score}] {snippet.excerpt}")
    return "\n".join(lines)
