# Product Catalog

## Purpose

This file is the normalized source of truth for every offer, package, workflow, or product capability the assistant may mention.

Do not let the assistant invent pricing, deliverables, or proof. If a field is unknown, leave it explicit.

## Catalog Entry Schema

Each catalog entry should include:
- name
- category
- short_description
- audience_fit
- problem_solved
- included_deliverables
- exclusions
- pricing_model
- onboarding_steps
- proof_points
- safe_claims
- related_pages
- status
- last_updated

## Product Summary

Agentic OneBotAds is an AI advertising assistant for SMEs, agencies, and marketing teams.

Core capabilities:
- campaign performance analysis
- RAG-based marketing knowledge search
- ad copy generation
- image prompt generation
- publication package creation
- optimization recommendations

## Starter Catalog Entries

### Entry: Knowledge Base Setup

- name: Knowledge Base Setup
- category: service_or_workflow
- short_description: structure brand, product, audience, and campaign documents for retrieval
- audience_fit: SMEs, agencies, in-house marketers
- problem_solved: scattered marketing knowledge is hard to reuse
- included_deliverables: markdown knowledge files, content structure, retrieval-ready formatting
- exclusions: unknown until defined
- pricing_model: not yet defined
- onboarding_steps: gather source material, normalize docs, place files under data/knowledge_base, reindex
- proof_points: not yet defined
- safe_claims: improves organization and reuse of internal marketing context
- related_pages: internal knowledge base docs
- status: active
- last_updated: 2026-04-23

### Entry: RAG Index Build

- name: RAG Index Build
- category: workflow
- short_description: embed and index local knowledge into ChromaDB for retrieval
- audience_fit: internal team, implementation workflow
- problem_solved: knowledge files are not searchable until indexed
- included_deliverables: indexed local knowledge, persisted vectors
- exclusions: does not validate content quality by itself
- pricing_model: not applicable
- onboarding_steps: add files, run reindex, verify retrieval
- proof_points: persistent local index in ChromaDB
- safe_claims: makes the local knowledge base queryable by the assistant
- related_pages: docs/CHROMADB_RAG.md
- status: active
- last_updated: 2026-04-23

### Entry: Campaign Context Pack

- name: Campaign Context Pack
- category: workflow
- short_description: package offer, audience, channel, and policy context for campaign generation
- audience_fit: marketers, agencies, founders
- problem_solved: campaign generation lacks grounded context
- included_deliverables: audience, offer, tone, and rules context
- exclusions: final performance outcomes
- pricing_model: not yet defined
- onboarding_steps: confirm product, audience, goal, channel, and constraints
- proof_points: not yet defined
- safe_claims: improves grounding for campaign drafts
- related_pages: data/knowledge_base
- status: active
- last_updated: 2026-04-23

### Entry: Ad Compliance Review

- name: Ad Compliance Review
- category: workflow
- short_description: check copy and landing page framing against brand and platform rules
- audience_fit: marketers and agencies
- problem_solved: unsafe claims or mismatched landing page promises
- included_deliverables: issue list, suggested fixes, safer version
- exclusions: legal approval outside defined policy rules
- pricing_model: not yet defined
- onboarding_steps: submit draft, compare against rules, revise
- proof_points: not yet defined
- safe_claims: helps surface risky wording before publication
- related_pages: data/knowledge_base/platform_ads_rules.md
- status: active
- last_updated: 2026-04-23

### Entry: Creative Inspiration Workflow

- name: Creative Inspiration Workflow
- category: workflow
- short_description: collect and tag relevant ad examples from internal history and official ad libraries
- audience_fit: agencies, marketers, creative operators
- problem_solved: teams need better reference material for hooks and angles
- included_deliverables: tagged examples, lessons, pattern library
- exclusions: direct copying of competitor ads
- pricing_model: not yet defined
- onboarding_steps: collect examples, summarize, tag, store in KB
- proof_points: not yet defined
- safe_claims: helps identify reusable message patterns
- related_pages: data/knowledge_base/previous_ads_examples.md
- status: active
- last_updated: 2026-04-23

## Retrieval Notes

When the assistant is asked what the product does, what workflows exist, or what can safely be claimed, this file should be treated as the normalized source of truth.
