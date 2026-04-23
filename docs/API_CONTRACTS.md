# API Contracts

## Runtime Summary

`image_provider` is `qwen_image` when hosted image generation is enabled. `image_model`
reflects the configured Hugging Face Space id.

```json
{
  "app_name": "Agentic OneBotAds",
  "environment": "development",
  "api_prefix": "/api/v1",
  "ollama_base_url": "http://localhost:11434",
  "ollama_chat_model": "qwen3:8b",
  "ollama_embedding_model": "nomic-embed-text:latest",
  "rag_enabled": true,
  "image_generation_enabled": true,
  "image_provider": "qwen_image",
  "image_model": "Qwen/Qwen-Image-2512",
  "knowledge_base_directory": "data/knowledge_base",
  "outputs_directory": "outputs"
}
```

## Campaign Analysis

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
  "insights": ["LinkedIn SMEs is the strongest revenue-efficient segment."],
  "campaign_breakdown": []
}
```

## Creative Copy

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

## Image Generation

```json
{
  "image_prompt": "Professional LinkedIn ad visual for Agentic OneBotAds...",
  "negative_prompt": "blurry, low quality, distorted text, watermark, unreadable UI, fake logos",
  "alt_text": "A modern AI advertising dashboard supporting SMEs.",
  "image_path": null,
  "status": "prompt_only",
  "notes": []
}
```

## Compliance Review

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

## Publication Package

```json
{
  "platform": "LinkedIn",
  "headline": "Agentic OneBotAds: smarter ads for SMEs",
  "caption": "Help SMEs increase qualified leads with Agentic OneBotAds.",
  "cta": "Discover the solution",
  "hashtags": ["#AgenticOnebotads", "#MarketingAutomation"],
  "image_prompt": "Professional LinkedIn ad visual for Agentic OneBotAds...",
  "image_path": null,
  "alt_text": "A modern AI advertising dashboard supporting SMEs.",
  "recommended_schedule": "Tuesday or Thursday morning",
  "compliance_status": "approved",
  "optimization_notes": ["Increase budget on CAMP003 by 15-20%."],
  "status": "ready_for_review"
}
```

## Optimization Recommendations

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

## Report Summary

```json
{
  "executive_summary": "The account is currently led by CAMP003 while CAMP001 needs attention.",
  "kpi_overview": {
    "CTR": "4.30%",
    "Conversion Rate": "7.95%",
    "CPA": "22.30",
    "ROAS": "3.00",
    "ROI": "199.50%"
  },
  "best_performing_campaign": "CAMP003",
  "weakest_campaign": "CAMP001",
  "key_insights": ["LinkedIn SMEs is the strongest revenue-efficient segment."],
  "recommended_actions": ["Increase budget on CAMP003 by 15-20%."],
  "next_experiments": ["Test benefit-focused headline vs. automation-focused headline."],
  "report_path": "outputs/reports/campaign_report_20260422_120000.md"
}
```
