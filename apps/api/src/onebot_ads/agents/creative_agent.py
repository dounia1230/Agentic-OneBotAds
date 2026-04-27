from textwrap import dedent

from onebot_ads.agents._llm import build_chat_model, extract_json_payload
from onebot_ads.core.config import Settings
from onebot_ads.schemas.campaigns import ABVariant, CreativeCopyResponse, RAGAgentResponse
from onebot_ads.tools.creative_tools import build_hashtags, normalize_platform

SYSTEM_PROMPT = """
You are the Creative Copywriting Agent of Agentic OneBotAds.

Your role is to create high-quality advertising copy.

You must generate:
- headline
- primary_text
- description
- slogan
- CTA
- hashtags
- A/B test variants

Use the RAG context when provided.
Adapt the copy to:
- platform
- audience
- campaign goal
- brand tone
- product value proposition

Rules:
1. Keep copy clear, persuasive, and specific.
2. Avoid exaggerated claims like "guaranteed success" unless the brand context explicitly allows it.
3. Do not invent customer counts, percentages, time-saved claims, ROI claims, guarantees, trials,
   testimonials, or proof points unless they are explicitly present in the user request or RAG context.
4. If proof is limited, use qualitative trust language instead of numbers.
5. Keep CTA aligned with the actual offer. Do not invent "free trial", "demo", "guarantee", or
   discount language unless it is grounded in context.
6. Write in the same language as the user unless instructed otherwise.
7. For LinkedIn, use a professional and business-focused tone.
8. For Instagram, use a short, visual, energetic tone.
9. For Facebook, use a friendly and direct tone.
10. For Google Ads, keep copy concise and conversion-focused.
11. Always provide at least 2 A/B variants when generating ads.
""".strip()


class CreativeCopywritingAgent:
    def __init__(self, settings: Settings) -> None:
        self.settings = settings

    def run(
        self,
        *,
        user_request: str,
        platform: str,
        audience: str,
        goal: str,
        product_name: str,
        tone: str,
        rag_context: RAGAgentResponse | None = None,
    ) -> CreativeCopyResponse:
        if self.settings.enable_live_llm:
            try:
                return self._generate_with_llm(
                    user_request=user_request,
                    platform=platform,
                    audience=audience,
                    goal=goal,
                    product_name=product_name,
                    tone=tone,
                    rag_context=rag_context,
                )
            except Exception:
                pass

        platform_name = normalize_platform(platform)
        context_line = (
            rag_context.answer
            if rag_context and rag_context.answer
            else "AI-assisted campaign analysis, content generation, and optimization."
        )
        headline = f"{product_name}: smarter ads for {audience}"
        primary_text = (
            f"Help {audience} {goal.lower()} with {product_name}. "
            f"{context_line} Built for a {tone} {platform_name} campaign."
        )
        description = "Your AI co-pilot for campaign performance and publication drafting."
        slogan = "Smarter ads. Faster decisions."
        cta = {
            "LinkedIn": "Discover the solution",
            "Instagram": "See it in action",
            "Facebook": "Learn more",
            "Google Ads": "Start optimizing today",
        }.get(platform_name, "Start optimizing today")
        hashtags = build_hashtags(product_name, platform_name)
        return CreativeCopyResponse(
            headline=headline,
            primary_text=primary_text,
            description=description,
            slogan=slogan,
            cta=cta,
            hashtags=hashtags,
            ab_variants=[
                ABVariant(
                    headline=f"Turn campaign data into better ads with {product_name}",
                    primary_text=(
                        f"Give {audience} a faster route to stronger performance insights and "
                        "publication-ready copy."
                    ),
                ),
                ABVariant(
                    headline=f"Your AI assistant for {platform_name} advertising",
                    primary_text=(
                        f"Create, review, and optimize campaigns with grounded brand context and a "
                        f"{tone} tone."
                    ),
                ),
            ],
        )

    def _generate_with_llm(
        self,
        *,
        user_request: str,
        platform: str,
        audience: str,
        goal: str,
        product_name: str,
        tone: str,
        rag_context: RAGAgentResponse | None,
    ) -> CreativeCopyResponse:
        from langchain_core.prompts import ChatPromptTemplate

        prompt = ChatPromptTemplate.from_messages(
            [
                ("system", SYSTEM_PROMPT),
                (
                    "human",
                    dedent(
                        """
                        User request: {user_request}
                        Platform: {platform}
                        Audience: {audience}
                        Goal: {goal}
                        Product: {product_name}
                        Tone: {tone}
                        RAG context: {rag_context}

                        Return only valid JSON with keys:
                        headline, primary_text, description, slogan, cta, hashtags, ab_variants

                        Safety requirements:
                        - Do not invent numbers, percentages, customer counts, guarantees, or offers.
                        - Keep proof language qualitative unless the context explicitly provides the proof.
                        - Keep the CTA commercially aligned with the grounded offer.
                        """
                    ).strip(),
                ),
            ]
        )
        llm = build_chat_model(self.settings)
        response = llm.invoke(
            prompt.format_messages(
                user_request=user_request,
                platform=platform,
                audience=audience,
                goal=goal,
                product_name=product_name,
                tone=tone,
                rag_context=(rag_context.model_dump_json() if rag_context else "null"),
            )
        )
        payload = extract_json_payload(getattr(response, "content", str(response)))
        return CreativeCopyResponse.model_validate(payload)
