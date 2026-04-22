import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
API_SRC = PROJECT_ROOT / "apps" / "api" / "src"
if str(API_SRC) not in sys.path:
    sys.path.insert(0, str(API_SRC))


if __name__ == "__main__":
    from onebot_ads.rag.build_index import build_rag_index

    build_rag_index()
    print("RAG index created successfully.")
