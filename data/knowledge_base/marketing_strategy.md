# Marketing Strategy

## Purpose

This file defines how Agentic OneBotAds should use the knowledge base to improve marketing output quality, consistency, and speed.

This is a starter operating strategy, not a finalized growth plan.

## Primary Goal

Use the knowledge base to improve:
- landing page messaging
- ad copy quality
- offer clarity
- email and nurture consistency
- internal answer quality
- reuse of winning campaign knowledge

## Strategic Rule

Do not treat the knowledge base as a brand brochure.

Treat it as an operational source of truth that answers exact situations:
- who the audience is
- what they care about
- what offer fits
- what claims are safe
- what messages have worked before

## Core Growth Model

1. Capture real business context in markdown under `data/knowledge_base/`.
2. Reindex after changes.
3. Use the assistant to answer grounded questions for campaigns, sales enablement, and landing page work.
4. Feed campaign learnings back into the knowledge base.

## Measurement Model

Track strategy quality using:
- GA4 User acquisition for first-touch acquisition patterns
- GA4 Traffic acquisition for session source patterns
- Search Console Performance for queries, pages, clicks, CTR, and impressions
- Search Console Insights for simple trend monitoring
- Keyword Planner and Google Trends for language and demand discovery
- Microsoft Clarity for heatmaps, recordings, and visible UX friction

## Channel Priorities

1. Search-driven intent capture
2. High-clarity landing pages
3. Retargeting and nurture
4. Social proof and educational content
5. Internal reuse of winning messages

## Recommended Knowledge Loops

### Loop 1: Offer Clarity

- capture objections
- update offer framing
- test revised copy
- store learnings

### Loop 2: Audience Language

- collect real search queries and call notes
- refine persona wording
- update hooks and headlines
- retest through campaigns and pages

### Loop 3: Safe Messaging

- compare draft claims against platform rules
- update compliant patterns
- store rejected claims and fixes

## Content Priorities For The Knowledge Base

Prefer adding documents that answer:
- what does this audience care about
- what offer should be mentioned
- what proof is safe to use
- what CTA fits this channel
- what message angles have already worked

## Weekly Review Checklist

- review acquisition and search query patterns
- review landing pages with strong or weak CTR
- review objections from leads or calls
- review campaign winners and weak performers
- update at least one KB file with a real learning

## Retrieval Notes

When the assistant is asked for strategy, it should combine this file with:
- audience personas
- previous ads examples
- platform ads rules

## Web Search Augmentation Strategy

When knowledge base files are insufficient to answer niche or up-to-date marketing queries (e.g., recent platform updates, trending hashtags, or emerging competitor strategies), the system supports real-time Web Search via SerpAPI.
- **Triggering:** Use the Web Search toggle in the UI.
- **Best Use Cases:** Validating trends, finding current examples of ads, fetching real-time compliance news.
- **Integration:** Web search results are appended alongside grounded context to provide a robust, comprehensive answer to the creative workflow.
