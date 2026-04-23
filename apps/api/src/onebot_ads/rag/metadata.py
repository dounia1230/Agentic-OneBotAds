import re
from pathlib import Path

from llama_index.core.vector_stores import (
    FilterCondition,
    FilterOperator,
    MetadataFilter,
    MetadataFilters,
)

from onebot_ads.schemas.knowledge import KnowledgeScope


def normalize_scope_value(value: str | None) -> str:
    if value is None:
        return ""
    normalized = re.sub(r"[^a-z0-9]+", "_", value.strip().lower())
    return normalized.strip("_")


def build_knowledge_file_metadata(
    file_path: str | Path,
    *,
    root_directory: Path,
    default_brand_slug: str,
) -> dict[str, str]:
    path = Path(file_path)
    try:
        relative_path = path.relative_to(root_directory)
    except ValueError:
        relative_path = path

    parts = [part for part in relative_path.parts[:-1] if part]
    metadata = {
        "file_name": path.name,
        "relative_path": relative_path.as_posix(),
        "knowledge_scope": "brand",
        "brand_slug": default_brand_slug,
        "campaign_slug": "",
    }

    if parts and parts[0] == "shared":
        metadata["knowledge_scope"] = "shared"
        metadata["brand_slug"] = ""
        return metadata

    if len(parts) >= 2 and parts[0] == "brands":
        metadata["brand_slug"] = normalize_scope_value(parts[1])
        metadata["knowledge_scope"] = "brand"
        if len(parts) >= 4 and parts[2] == "campaigns":
            metadata["knowledge_scope"] = "campaign"
            metadata["campaign_slug"] = normalize_scope_value(parts[3])
        return metadata

    return metadata


def build_retrieval_filters(scope: KnowledgeScope | None) -> MetadataFilters | None:
    if scope is None:
        return None

    brand_slug = normalize_scope_value(scope.brand_name)
    campaign_slug = normalize_scope_value(scope.campaign_name)
    if not brand_slug and not campaign_slug:
        return None

    shared_filter = MetadataFilter(
        key="knowledge_scope",
        value="shared",
        operator=FilterOperator.EQ,
    )
    filter_groups: list[MetadataFilter | MetadataFilters] = [shared_filter]

    if brand_slug and campaign_slug:
        filter_groups.append(
            MetadataFilters(
                filters=[
                    MetadataFilter(key="brand_slug", value=brand_slug),
                    MetadataFilter(
                        key="knowledge_scope",
                        value="brand",
                        operator=FilterOperator.EQ,
                    ),
                ],
                condition=FilterCondition.AND,
            )
        )
        filter_groups.append(
            MetadataFilters(
                filters=[
                    MetadataFilter(key="brand_slug", value=brand_slug),
                    MetadataFilter(key="campaign_slug", value=campaign_slug),
                ],
                condition=FilterCondition.AND,
            )
        )
    elif brand_slug:
        filter_groups.append(
            MetadataFilter(key="brand_slug", value=brand_slug, operator=FilterOperator.EQ)
        )
    else:
        filter_groups.append(
            MetadataFilter(
                key="campaign_slug",
                value=campaign_slug,
                operator=FilterOperator.EQ,
            )
        )

    return MetadataFilters(filters=filter_groups, condition=FilterCondition.OR)
