# Web UI

## Commands
- `npm run dev --prefix apps/web`
- `npm run build --prefix apps/web`
- `npm run test --prefix apps/web -- --run`

## Structure
- `src/app`
  App shell and workspace-level navigation.
- `src/components/ui`
  Reusable presentational primitives shared across tabs.
- `src/features`
  Feature modules grouped by workflow tab.
- `src/lib`
  Frontend-only shared helpers.
- `src/services/api`
  HTTP client and backend API wrappers.
- `src/styles`
  Theme, base, layout, and component CSS layers.
- `src/types`
  Shared TypeScript contracts for backend responses.

## Conventions
- Keep state local to the feature that owns it.
- Prefer derived values over duplicated state.
- Prefer semantic markup, visible labels, and accessible headings.
- Test user-visible behavior with roles, labels, and text instead of implementation details.
