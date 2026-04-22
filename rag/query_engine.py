import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
API_SRC = PROJECT_ROOT / "apps" / "api" / "src"
if str(API_SRC) not in sys.path:
    sys.path.insert(0, str(API_SRC))


def get_query_engine(similarity_top_k: int = 5):
    from onebot_ads.rag.query_engine import get_query_engine as backend_get_query_engine

    return backend_get_query_engine(similarity_top_k=similarity_top_k)


__all__ = ["get_query_engine"]
