# Frontend Development Standards

## Code Quality
- TypeScript strict mode enabled. No `any` types without explicit justification.
- All components must have defined prop interfaces with JSDoc descriptions.
- Maximum component file length: 200 lines. Split if larger.
- No inline styles except for truly dynamic values.

## Component Standards
- One component per file. File name matches component name.
- Props interface exported separately for reuse.
- Default exports prohibited — use named exports only.
- All interactive elements must be keyboard accessible.

## State Management
- Local state for component-specific data.
- Shared state (Context/Store) only for truly shared data.
- Server state managed via data-fetching library (React Query, SWR, etc.).
- No prop drilling beyond 2 levels — use context or composition.

## Testing Standards
- Minimum 80% coverage for business-critical components.
- Test user behavior, not implementation details.
- Use Testing Library (not Enzyme).
- Every bug fix must include a regression test.

## Performance Standards
- Lighthouse score >= 90 for all metrics.
- First Contentful Paint < 1.5s.
- Bundle size budgets enforced per route.
- Images lazy-loaded and properly sized.

## Accessibility Standards
- WCAG 2.1 Level AA compliance required.
- All images must have alt text.
- Color contrast ratio >= 4.5:1 for text.
- All forms must have associated labels.
- Skip navigation link on all pages.
