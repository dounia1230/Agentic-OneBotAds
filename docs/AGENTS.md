# Agents

## Orchestrator Agent

- Purpose: classifies user intent, picks the agent sequence, and assembles the final structured response.
- Input: raw user request text.
- Output: orchestration plan plus agent outputs such as RAG context, analysis, creative, compliance, publication, or report.
- When to call: always first.
- System prompt summary: route campaign analysis, RAG, creative, image, optimization, compliance, publication, and reporting in the correct order with sensible defaults.
- Example response:

```json
{
  "intent": "generate_publication",
  "agents_to_call": ["rag_agent", "creative_agent", "image_agent", "compliance_agent", "publication_agent"],
  "final_format": "publication_package"
}
```

## RAG Marketing Knowledge Agent

- Purpose: retrieves grounded brand, product, strategy, persona, and rules context from the private knowledge base.
- Input: a marketing question or the full user request.
- Output: `answer`, `relevant_context`, `source_documents`, `confidence`.
- When to call: any time the request needs private brand facts or message constraints.
- System prompt summary: answer only from the knowledge base and state what is missing if the KB is insufficient.
- Example response:

```json
{
  "answer": "The brand tone should be professional, modern, helpful, and direct.",
  "relevant_context": ["Avoid exaggerated promises such as guaranteed sales or instant success."],
  "source_documents": ["brand_guidelines.md"],
  "confidence": "medium"
}
```

## Campaign Data Analyst Agent

- Purpose: calculates campaign KPIs and identifies top and weak performers.
- Input: campaign CSV path, defaulting to `data/campaigns.csv`.
- Output: KPI summary, best campaign, weakest campaign, main problem, insights, campaign breakdown.
- When to call: campaign analysis, optimization, and reporting flows.
- System prompt summary: use the analytics tool, never invent numbers, and surface the biggest performance issue.
- Example response:

```json
{
  "summary": {
    "ctr": "4.30%",
    "conversion_rate": "7.95%",
    "cpa": "22.30",
    "roas": "3.00",
    "roi": "199.50%"
  },
  "best_campaign": "CAMP003",
  "weakest_campaign": "CAMP001",
  "main_problem": "Some campaigns are spending budget without matching conversion efficiency.",
  "insights": ["LinkedIn SMEs is the strongest revenue-efficient segment."]
}
```

## Creative Copywriting Agent

- Purpose: creates structured ad copy with A/B variants.
- Input: request text plus platform, audience, goal, product, tone, and optional RAG context.
- Output: headline, primary text, description, slogan, CTA, hashtags, and variants.
- When to call: ad copy and publication flows.
- System prompt summary: adapt copy to platform and audience, keep it specific, and avoid exaggerated claims.
- Example response:

```json
{
  "headline": "Agentic OneBotAds: smarter ads for SMEs",
  "primary_text": "Help SMEs increase qualified leads with Agentic OneBotAds.",
  "description": "Your AI co-pilot for campaign performance and publication drafting.",
  "slogan": "Smarter ads. Faster decisions.",
  "cta": "Discover the solution",
  "hashtags": ["#AgenticOnebotads", "#MarketingAutomation"],
  "ab_variants": [
    {"headline": "Turn campaign data into better ads", "primary_text": "Faster route to stronger performance insights."},
    {"headline": "Your AI assistant for LinkedIn advertising", "primary_text": "Create and optimize campaigns with grounded context."}
  ]
}
```

## Image Generation Agent

- Purpose: generates a detailed image prompt, negative prompt, alt text, and optionally an image file.
- Input: product, audience, platform, goal, style, and whether actual image generation was requested.
- Output: `image_prompt`, `negative_prompt`, `alt_text`, `image_path`, `status`, `notes`.
- When to call: publication flows that include a visual request.
- System prompt summary: create prompt specs for ads and only claim generation if the tool returns a real file path.
- Example response:

```json
{
  "image_prompt": "Professional LinkedIn ad visual for Agentic OneBotAds...",
  "negative_prompt": "blurry, low quality, distorted text, watermark, unreadable UI, fake logos",
  "alt_text": "A modern AI advertising dashboard supporting SMEs.",
  "image_path": null,
  "status": "disabled"
}
```

## Publication Agent

- Purpose: assembles the final publication-ready package.
- Input: platform, approved creative, image result, compliance review, and optimization notes.
- Output: headline, caption, CTA, hashtags, image data, schedule, compliance status, and workflow status.
- When to call: after compliance in publication flows.
- System prompt summary: package approved assets without inventing new copy.
- Example response:

```json
{
  "platform": "LinkedIn",
  "headline": "Agentic OneBotAds: smarter ads for SMEs",
  "caption": "Help SMEs increase qualified leads with Agentic OneBotAds.",
  "cta": "Discover the solution",
  "recommended_schedule": "Tuesday or Thursday morning",
  "compliance_status": "approved",
  "status": "ready_for_review"
}
```

## Optimization Strategy Agent

- Purpose: converts analytics into budget, audience, creative, and experiment recommendations.
- Input: campaign analysis plus optional RAG context.
- Output: quick wins, strategic changes, and A/B tests with priorities.
- When to call: after analysis or inside reporting.
- System prompt summary: justify recommendations with ROAS, CPA, CTR, and conversion rate, and separate quick wins from longer changes.
- Example response:

```json
{
  "quick_wins": [
    {"priority": "high", "recommendation": "Increase budget on CAMP003 by 15-20%.", "reason": "It is the strongest ROAS campaign."}
  ],
  "strategic_changes": [
    {"priority": "medium", "recommendation": "Create a second creative focused on time savings for SMEs.", "reason": "This aligns with product positioning."}
  ],
  "ab_tests": ["Test benefit-focused headline vs. automation-focused headline."]
}
```

## Brand Safety & Compliance Agent

- Purpose: checks copy and image specs for unsupported claims, tone drift, and accessibility issues.
- Input: creative output, optional image output, and optional RAG context.
- Output: `approved`, `issues`, `suggested_fixes`, and `final_safe_version`.
- When to call: before returning ad copy or publication packages.
- System prompt summary: do not approve unsupported promises or invented product capabilities.
- Example response:

```json
{
  "approved": true,
  "issues": [],
  "suggested_fixes": [],
  "final_safe_version": {
    "headline": "Agentic OneBotAds: smarter ads for SMEs",
    "caption": "Help SMEs increase qualified leads with Agentic OneBotAds."
  }
}
```

## Reporting Agent

- Purpose: turns analytics and optimization outputs into an executive-friendly report and optional Markdown export.
- Input: campaign analysis, optimization plan, original request text, and export flag.
- Output: executive summary, KPI overview, insights, actions, experiments, and optional `report_path`.
- When to call: full-report requests.
- System prompt summary: keep reports readable for business users and only include metrics supplied by analytics.
- Example response:

```json
{
  "executive_summary": "The account is currently led by CAMP003 while CAMP001 needs attention.",
  "kpi_overview": {"CTR": "4.30%", "ROAS": "3.00"},
  "best_performing_campaign": "CAMP003",
  "weakest_campaign": "CAMP001",
  "report_path": "outputs/reports/campaign_report_20260422_120000.md"
}
```
