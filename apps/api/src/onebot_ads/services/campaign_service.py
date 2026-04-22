from onebot_ads.agents.campaign_copy_agent import CampaignCopyAgent
from onebot_ads.agents.orchestrator_agent import OrchestratorAgent
from onebot_ads.core.config import Settings
from onebot_ads.rag.knowledge_base import KnowledgeBaseService
from onebot_ads.schemas.campaigns import (
    AssistantResponse,
    CampaignBrief,
    CampaignDraftResponse,
    ReindexResponse,
    RuntimeSummary,
)


class CampaignService:
    def __init__(
        self,
        settings: Settings,
        knowledge_base: KnowledgeBaseService | None = None,
    ) -> None:
        self.settings = settings
        self.knowledge_base = knowledge_base or KnowledgeBaseService(settings)
        self.campaign_agent = CampaignCopyAgent(settings, self.knowledge_base)
        self.orchestrator_agent = OrchestratorAgent(settings, self.knowledge_base)

    def draft_campaign(self, brief: CampaignBrief) -> CampaignDraftResponse:
        return self.campaign_agent.draft(brief)

    def handle_request(self, user_message: str) -> AssistantResponse:
        return self.orchestrator_agent.run(user_message)

    def reindex_knowledge_base(self) -> ReindexResponse:
        return self.knowledge_base.reindex()

    def runtime_summary(self) -> RuntimeSummary:
        return RuntimeSummary(
            app_name=self.settings.app_name,
            environment=self.settings.environment,
            api_prefix=self.settings.api_prefix,
            ollama_base_url=self.settings.ollama_base_url,
            ollama_chat_model=self.settings.llm_model,
            ollama_embedding_model=self.settings.embed_model,
            rag_enabled=self.settings.enable_rag,
            image_generation_enabled=self.settings.enable_image_generation,
            image_provider=self.settings.image_provider,
            knowledge_base_directory=str(self.settings.knowledge_base_path),
            outputs_directory=str(self.settings.outputs_directory),
        )
