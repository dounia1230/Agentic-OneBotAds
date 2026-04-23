import re
from dataclasses import dataclass

from onebot_ads.agents.analyst_agent import CampaignDataAnalystAgent
from onebot_ads.agents.compliance_agent import BrandSafetyComplianceAgent
from onebot_ads.agents.creative_agent import CreativeCopywritingAgent
from onebot_ads.agents.image_agent import ImageGenerationAgent
from onebot_ads.agents.optimization_agent import OptimizationStrategyAgent
from onebot_ads.agents.publication_agent import PublicationAgent
from onebot_ads.agents.rag_agent import RAGMarketingKnowledgeAgent
from onebot_ads.agents.reporting_agent import ReportingAgent
from onebot_ads.core.config import Settings
from onebot_ads.rag.knowledge_base import KnowledgeBaseService
from onebot_ads.schemas.campaigns import AssistantResponse, OrchestrationPlan
from onebot_ads.schemas.knowledge import KnowledgeScope

SYSTEM_PROMPT = """
You are the Orchestrator Agent of Agentic OneBotAds.

You are responsible for understanding the user request and coordinating
the correct specialized agents.

Your available agent capabilities are:

1. RAG Marketing Knowledge Agent:
   Use for brand guidelines, product context, private marketing strategy,
   audience personas, platform rules, and previous ads.

2. Campaign Data Analyst Agent:
   Use for analyzing campaign CSV data, KPIs, CTR, CPA, ROAS, ROI,
   conversion rate, and performance problems.

3. Creative Copywriting Agent:
   Use for generating headlines, captions, slogans, descriptions, CTAs, hashtags, and A/B variants.

4. Image Generation Agent:
   Use for generating detailed image prompts and calling image
   generation tools when the user requests a visual or publication
   with image.

5. Publication Agent:
   Use for assembling a complete post or ad package with platform,
   caption, headline, CTA, hashtags, image prompt, image path,
   alt text, and status.

6. Optimization Strategy Agent:
   Use for budget recommendations, audience recommendations, A/B tests,
   campaign improvements, and targeting changes.

7. Brand Safety & Compliance Agent:
   Use before finalizing ads or publications to check brand tone,
   exaggerated claims, unsafe content, and platform rule issues.

8. Reporting Agent:
   Use for generating campaign reports, summaries, exported report files, or executive insights.

When the user asks for:
- campaign analysis: call Campaign Data Analyst, then Optimization Strategy.
- brand/product advice: call RAG Marketing Knowledge.
- ad copy: call RAG Marketing Knowledge, then Creative Copywriting, then Compliance.
- publication with image: call RAG Marketing Knowledge, Creative
  Copywriting, Image Generation, Compliance, then Publication.
- optimization: call Campaign Data Analyst if data is needed, then Optimization Strategy.
- full report: call Campaign Data Analyst, Optimization Strategy, and Reporting.

Always return the final answer in a clear structured format.

If the user request is missing details, infer reasonable defaults:
- default platform: LinkedIn
- default audience: SMEs and marketing teams
- default tone: professional, modern, direct
- default language: same language as the user
- default status: ready_for_review

Never claim that an image was generated unless the image tool returns an actual image path.
""".strip()


@dataclass
class RequestContext:
    user_message: str
    intent: str
    platform: str
    audience: str
    tone: str
    goal: str
    product_name: str
    knowledge_scope: KnowledgeScope | None
    wants_image_prompt: bool
    wants_image_generation: bool
    wants_report_export: bool
    run_all_agents: bool


class OrchestratorAgent:
    def __init__(
        self,
        settings: Settings,
        knowledge_base: KnowledgeBaseService,
    ) -> None:
        self.settings = settings
        self.knowledge_base = knowledge_base
        self.rag_agent = RAGMarketingKnowledgeAgent(settings, knowledge_base)
        self.analyst_agent = CampaignDataAnalystAgent(settings)
        self.creative_agent = CreativeCopywritingAgent(settings)
        self.image_agent = ImageGenerationAgent(settings)
        self.optimization_agent = OptimizationStrategyAgent(settings)
        self.compliance_agent = BrandSafetyComplianceAgent(settings)
        self.publication_agent = PublicationAgent(settings)
        self.reporting_agent = ReportingAgent(settings)

    def run(
        self,
        user_message: str,
        *,
        product_name: str | None = None,
        audience: str | None = None,
        goal: str | None = None,
        platform: str | None = None,
        knowledge_scope: KnowledgeScope | None = None,
        run_all_agents: bool = False,
        export_report: bool = False,
    ) -> AssistantResponse:
        context = self._build_request_context(
            user_message,
            product_name=product_name,
            audience=audience,
            goal=goal,
            platform=platform,
            knowledge_scope=knowledge_scope,
            run_all_agents=run_all_agents,
            export_report=export_report,
        )
        plan = self._build_plan(
            context.intent,
            context.wants_image_prompt,
            run_all_agents=context.run_all_agents,
        )
        response = AssistantResponse(intent=plan.intent, plan=plan)

        rag_result = None
        analysis_result = None
        creative_result = None
        image_result = None
        optimization_result = None
        compliance_result = None
        report_result = None
        publication_result = None

        if "rag_agent" in plan.agents_to_call:
            rag_result = self.rag_agent.run(user_message, knowledge_scope=context.knowledge_scope)
            response.rag = rag_result
        if "analyst_agent" in plan.agents_to_call:
            analysis_result = self.analyst_agent.run()
            response.analysis = analysis_result
        if "creative_agent" in plan.agents_to_call:
            creative_result = self.creative_agent.run(
                user_request=user_message,
                platform=context.platform,
                audience=context.audience,
                goal=context.goal,
                product_name=context.product_name,
                tone=context.tone,
                rag_context=rag_result,
            )
            response.creative = creative_result
        if "image_agent" in plan.agents_to_call:
            image_result = self.image_agent.run(
                product_name=context.product_name,
                audience=context.audience,
                platform=context.platform,
                goal=context.goal,
                style=(
                    "modern editorial SaaS advertising, strong contrast, "
                    "clean product storytelling"
                ),
                request_image_generation=context.wants_image_generation,
                headline=creative_result.headline if creative_result else None,
                cta=creative_result.cta if creative_result else None,
                compose_publication_image_flag=True,
                provider=self.settings.image_provider,
            )
            response.image = image_result
        if "optimization_agent" in plan.agents_to_call:
            optimization_result = self.optimization_agent.run(analysis_result, rag_result)
            response.optimization = optimization_result
        if "compliance_agent" in plan.agents_to_call and creative_result is not None:
            compliance_result = self.compliance_agent.run(
                creative=creative_result,
                image=image_result,
                rag_context=rag_result,
            )
            response.compliance = compliance_result
        if "publication_agent" in plan.agents_to_call and creative_result and compliance_result:
            publication_result = self.publication_agent.run(
                platform=context.platform,
                creative=creative_result,
                image=image_result,
                compliance=compliance_result,
                optimization=optimization_result,
            )
            response.publication = publication_result
            response.status = publication_result.status
        if "reporting_agent" in plan.agents_to_call and analysis_result:
            report_result = self.reporting_agent.run(
                analysis=analysis_result,
                optimization=optimization_result,
                request_text=user_message,
                export_markdown=context.wants_report_export,
            )
            response.report = report_result

        return response

    def _build_plan(
        self,
        intent: str,
        wants_image_prompt: bool,
        *,
        run_all_agents: bool = False,
    ) -> OrchestrationPlan:
        if run_all_agents:
            return OrchestrationPlan(
                intent="full_workflow",
                agents_to_call=[
                    "rag_agent",
                    "analyst_agent",
                    "creative_agent",
                    "image_agent",
                    "optimization_agent",
                    "compliance_agent",
                    "publication_agent",
                    "reporting_agent",
                ],
                final_format="full_workflow_bundle",
            )
        if intent == "campaign_analysis":
            return OrchestrationPlan(
                intent=intent,
                agents_to_call=["analyst_agent", "optimization_agent"],
                final_format="campaign_analysis",
            )
        if intent == "optimization":
            return OrchestrationPlan(
                intent=intent,
                agents_to_call=["analyst_agent", "optimization_agent"],
                final_format="optimization_recommendations",
            )
        if intent == "brand_advice":
            return OrchestrationPlan(
                intent=intent,
                agents_to_call=["rag_agent"],
                final_format="grounded_brand_guidance",
            )
        if intent == "full_report":
            return OrchestrationPlan(
                intent=intent,
                agents_to_call=["analyst_agent", "optimization_agent", "reporting_agent"],
                final_format="report_summary",
            )
        if wants_image_prompt:
            return OrchestrationPlan(
                intent="generate_publication",
                agents_to_call=[
                    "rag_agent",
                    "creative_agent",
                    "image_agent",
                    "compliance_agent",
                    "publication_agent",
                ],
                final_format="publication_package",
            )
        return OrchestrationPlan(
            intent="ad_copy",
            agents_to_call=["rag_agent", "creative_agent", "compliance_agent"],
            final_format="creative_copy",
        )

    def _build_request_context(
        self,
        user_message: str,
        *,
        product_name: str | None = None,
        audience: str | None = None,
        goal: str | None = None,
        platform: str | None = None,
        knowledge_scope: KnowledgeScope | None = None,
        run_all_agents: bool = False,
        export_report: bool = False,
    ) -> RequestContext:
        message = user_message.lower()
        intent = "ad_copy"
        if "report" in message:
            intent = "full_report"
        elif any(token in message for token in ["optimiz", "budget", "improve spend"]):
            intent = "optimization"
        elif any(token in message for token in ["analyze", "analysis", "performance", "campaigns"]):
            intent = "campaign_analysis"
        elif any(
            token in message
            for token in ["tone", "guideline", "brand", "persona", "positioning"]
        ):
            intent = "brand_advice"
        elif any(token in message for token in ["publication", "post", "ad package"]):
            intent = "generate_publication"

        resolved_platform = platform or self._match_platform(message)
        resolved_audience = audience or self._extract_value(
            user_message,
            r"(?:targeting|for)\s+([A-Za-z0-9 ,&-]+)",
        )
        resolved_goal = goal or self._extract_value(user_message, r"(?:goal|to)\s+([A-Za-z0-9 ,&-]+)")
        wants_image_prompt = (
            "image" in message or "visual" in message or intent == "generate_publication"
        )
        wants_image_generation = wants_image_prompt and (
            "generate image" in message or "with image" in message or "create image" in message
        )
        default_goal = (
            "increase qualified leads"
            if intent != "campaign_analysis"
            else "improve campaign performance"
        )
        return RequestContext(
            user_message=user_message,
            intent=intent,
            platform=resolved_platform,
            audience=resolved_audience or "SMEs and marketing teams",
            tone="professional, modern, direct",
            goal=resolved_goal or default_goal,
            product_name=product_name or "Agentic OneBotAds",
            knowledge_scope=knowledge_scope,
            wants_image_prompt=wants_image_prompt,
            wants_image_generation=wants_image_generation,
            wants_report_export=(
                export_report
                or "markdown" in message
                or "export" in message
                or "file" in message
            ),
            run_all_agents=run_all_agents,
        )

    @staticmethod
    def _match_platform(message: str) -> str:
        for platform in ["linkedin", "instagram", "facebook", "google ads", "google", "meta"]:
            if platform in message:
                return platform.title() if platform != "google ads" else "Google Ads"
        return "LinkedIn"

    @staticmethod
    def _extract_value(text: str, pattern: str) -> str | None:
        match = re.search(pattern, text, re.IGNORECASE)
        if not match:
            return None
        return match.group(1).strip().rstrip(".")
