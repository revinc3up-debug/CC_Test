Review the following frontend code.

## Project Context
{{project_summary}}

## Code to Review
{{code}}

## Review Checklist
1. **Correctness** — Does the code work as intended?
2. **Component Design** — Single responsibility, proper prop drilling vs context.
3. **TypeScript** — Type safety, no `any` leaks, proper generics.
4. **Accessibility** — WCAG 2.1 AA compliance, semantic HTML, ARIA.
5. **Performance** — Unnecessary re-renders, missing memoization, bundle impact.
6. **Error Handling** — All async operations handled, user-friendly error states.
7. **Testing** — Adequate test coverage, testing behavior not implementation.
8. **Code Style** — Consistent with project patterns, readable, maintainable.

Provide specific line-level feedback with severity (blocker/major/minor/nit).
