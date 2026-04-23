# UI TODO

## Working Principles
- Keep state as local and minimal as possible; derive display values instead of duplicating them.
- Keep the page structure explicit with clear headings, sections, and visible labels.
- Prefer user-facing tests that query by role, label, and text instead of implementation details.
- Keep each workflow in its own feature module so future redesigns can happen tab by tab.
- Keep the shell stable: navigation lives in the left sidebar, workflow content owns the remaining workspace.

## Design Structure
- App shell:
  A persistent left sidebar contains the placeholder logo, app name, workflow tabs, and the collapse/expand control. Collapsing the sidebar leaves only compact logo/navigation symbols visible and preserves the main workspace.
- Workspace:
  The selected tab renders directly in the main content area. Avoid marketing heroes, decorative wrappers, nested cards, and AI-demo gradients.
- Results:
  When a workflow produces results, scroll the result section into view and present values in flat, scan-friendly sections with subtle dividers instead of boxed cards.
- Visual language:
  Management-oriented, restrained, and efficient. Use the dark workspace with the background grid, light blue and purple accents, solid surfaces, clear labels, and dense but readable spacing.

## Current Feature Inventory
- Campaign Analysis
  Upload a CSV, analyze campaign KPIs locally, review a performance table, and read optimization recommendations.
- Publication Generator
  Capture product/platform/audience/goal inputs, request a publication package, and review warnings plus structured output.
- Knowledge Base Q&A
  Ask the assistant a question and review the grounded answer, confidence, context snippets, and source documents.
- Image Prompt
  Build a visual brief, request image guidance, and review prompt output, alt text, status, path, notes, and preview when available.

## Refactor Checklist
- [x] Split the root screen into per-feature tab modules.
- [x] Move API calls into shared service files.
- [x] Move shared backend contracts into a typed API module.
- [x] Extract reusable UI shell components.
- [x] Split the stylesheet into theme, base, layout, and component layers.
- [x] Add focused tests for shared app behavior and campaign-analysis logic.
- [x] Move workspace navigation into a collapsible left sidebar shell.

## Design Backlog
- [ ] Campaign Analysis
  Rework upload affordance, KPI hierarchy, table density, and recommendation readability.
- [ ] Publication Generator
  Improve form layout, output typography, status styling, and long-text scanning.
- [ ] Knowledge Base Q&A
  Improve answer readability, context/source presentation, and empty/error states.
- [ ] Image Prompt
  Improve prompt readability, preview treatment, and visual hierarchy for metadata.
- [x] Shell
  Replace the current generic hero and tab visuals with a more deliberate, product-specific design language.
