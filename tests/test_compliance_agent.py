from onebot_ads.agents.compliance_agent import BrandSafetyComplianceAgent
from onebot_ads.core.config import Settings
from onebot_ads.schemas.campaigns import CreativeCopyResponse


def test_compliance_agent_returns_human_readable_quantified_claim_warning() -> None:
    agent = BrandSafetyComplianceAgent(Settings())

    result = agent.run(
        CreativeCopyResponse(
            headline="Save 10+ hours every week",
            primary_text="Teams can start saving 10+ hours on repetitive ad setup.",
            description="AI-assisted ad operations",
            slogan="Spend less time on setup",
            cta="Book a demo",
            hashtags=["#OneBotAds"],
        )
    )

    assert result.approved is False
    assert "Avoid specific time-saving claims unless they are supported by evidence." in result.issues
