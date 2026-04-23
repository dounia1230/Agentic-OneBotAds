from pydantic import BaseModel, Field


class KnowledgeScope(BaseModel):
    brand_name: str | None = Field(default=None, max_length=120)
    campaign_name: str | None = Field(default=None, max_length=120)
