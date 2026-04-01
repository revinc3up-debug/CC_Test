# UI/UX Design Standards

## Design Tokens
- All colors, spacing, and typography must reference design tokens, not raw values.
- 4px grid for all spacing. No arbitrary pixel values.
- Color palette must pass WCAG 2.1 AA contrast requirements.

## Component Standards
- Every component must define all interactive states: default, hover, active, focus, disabled.
- Loading states required for all async operations.
- Empty states required for all lists and data-driven views.
- Error states with clear recovery actions for all forms.

## Accessibility Standards
- WCAG 2.1 Level AA compliance minimum.
- Focus indicators visible for all interactive elements.
- Touch targets minimum 44x44px on mobile.
- No information conveyed by color alone.

## Responsive Design
- Mobile-first design approach.
- Breakpoints: 320px (mobile), 768px (tablet), 1024px (desktop), 1440px (wide).
- Content hierarchy maintained across all breakpoints.

## Specification Standards
- Every design deliverable must include interaction annotations.
- All text content specified (no lorem ipsum in final specs).
- Responsive behavior documented for each breakpoint.
