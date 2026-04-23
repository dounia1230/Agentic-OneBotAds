from pathlib import Path

from onebot_ads.agents.campaign_copy_agent import CampaignCopyAgent
from onebot_ads.agents.orchestrator_agent import OrchestratorAgent
from onebot_ads.core.config import PROJECT_ROOT, Settings
from onebot_ads.rag.knowledge_base import KnowledgeBaseService
from onebot_ads.schemas.campaigns import (
    AssistantResponse,
    CampaignBrief,
    CampaignDraftResponse,
    ReindexResponse,
    RuntimeSummary,
)
from onebot_ads.tools.output_tools import build_assistant_output_path, save_assistant_output


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

    def handle_request(
        self,
        user_message: str,
        *,
        product_name: str | None = None,
        audience: str | None = None,
        goal: str | None = None,
        platform: str | None = None,
        campaign_csv_content: str | None = None,
        campaign_csv_filename: str | None = None,
        knowledge_scope=None,
        run_all_agents: bool = False,
        save_output: bool = False,
        export_report: bool = False,
        use_web_search: bool = False,
    ) -> AssistantResponse:
        result = self.orchestrator_agent.run(
            user_message,
            product_name=product_name,
            audience=audience,
            goal=goal,
            platform=platform,
            campaign_csv_content=campaign_csv_content,
            campaign_csv_filename=campaign_csv_filename,
            knowledge_scope=knowledge_scope,
            run_all_agents=run_all_agents,
            export_report=export_report,
            use_web_search=use_web_search,
        )
        result.artifact_paths = self._collect_artifact_paths(result)

        if save_output:
            result.saved_output_path = build_assistant_output_path(
                user_message,
                settings=self.settings,
            )
            result.artifact_paths.append(result.saved_output_path)
            save_assistant_output(
                result,
                user_message,
                settings=self.settings,
                output_path=result.saved_output_path,
            )
        return result

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
            image_model=self.settings.image_model_id,
            knowledge_base_directory=self._serialize_runtime_path(self.settings.knowledge_base_path),
            outputs_directory=self._serialize_runtime_path(self.settings.outputs_directory),
        )

    @staticmethod
    def _serialize_runtime_path(path: Path) -> str:
        if not path.is_absolute():
            return path.as_posix()
        try:
            return path.relative_to(PROJECT_ROOT).as_posix()
        except ValueError:
            return path.as_posix()

    def _collect_artifact_paths(self, result: AssistantResponse) -> list[str]:
        artifact_paths: list[str] = []
        if result.image and result.image.image_path:
            artifact_paths.append(result.image.image_path)
        if result.report and result.report.report_path:
            artifact_paths.append(result.report.report_path)
        return artifact_paths
