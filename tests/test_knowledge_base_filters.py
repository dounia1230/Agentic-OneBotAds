from pathlib import Path

from onebot_ads.core.config import Settings
from onebot_ads.rag.knowledge_base import KnowledgeBaseService
from onebot_ads.rag.metadata import build_knowledge_file_metadata, normalize_scope_value
from onebot_ads.schemas.knowledge import KnowledgeScope


def test_build_knowledge_file_metadata_scopes_paths() -> None:
    root = Path("data/knowledge_base")
    default_brand = normalize_scope_value("Agentic OneBotAds")

    shared = build_knowledge_file_metadata(
        root / "shared" / "platform_rules.md",
        root_directory=root,
        default_brand_slug=default_brand,
    )
    brand = build_knowledge_file_metadata(
        root / "brands" / "cuddlenest-plushies" / "brand_guidelines.md",
        root_directory=root,
        default_brand_slug=default_brand,
    )
    campaign = build_knowledge_file_metadata(
        root / "brands" / "cuddlenest-plushies" / "campaigns" / "spring-launch" / "brief.md",
        root_directory=root,
        default_brand_slug=default_brand,
    )
    legacy = build_knowledge_file_metadata(
        root / "brand_guidelines.md",
        root_directory=root,
        default_brand_slug=default_brand,
    )

    assert shared["knowledge_scope"] == "shared"
    assert shared["brand_slug"] == ""
    assert brand["knowledge_scope"] == "brand"
    assert brand["brand_slug"] == "cuddlenest_plushies"
    assert campaign["knowledge_scope"] == "campaign"
    assert campaign["campaign_slug"] == "spring_launch"
    assert legacy["brand_slug"] == default_brand


def test_retrieve_builds_scoped_filters(monkeypatch) -> None:
    settings = Settings(enable_live_llm=False, enable_rag=True)
    service = KnowledgeBaseService(settings)
    captured = {}

    class FakeRetriever:
        def retrieve(self, query: str):
            captured["query"] = query
            return []

    class FakeIndex:
        def as_retriever(self, similarity_top_k: int, filters=None):
            captured["top_k"] = similarity_top_k
            captured["filters"] = filters
            return FakeRetriever()

    monkeypatch.setattr(service, "_load_or_build_index", lambda: FakeIndex())

    service.retrieve(
        "launch messaging",
        top_k=4,
        scope=KnowledgeScope(
            brand_name="CuddleNest Plushies",
            campaign_name="Spring Launch",
        ),
    )

    filters = captured["filters"]
    assert captured["top_k"] == 4
    assert captured["query"] == "launch messaging"
    assert filters is not None
    assert filters.condition.value == "or"
    assert any(
        getattr(filter_item, "key", None) == "knowledge_scope"
        and getattr(filter_item, "value", None) == "shared"
        for filter_item in filters.filters
    )
