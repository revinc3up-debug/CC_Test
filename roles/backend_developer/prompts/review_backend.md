Review the following backend code.

## Project Context
{{project_summary}}

## Code to Review
{{code}}

## Review Checklist
1. **Correctness** — Does it implement the spec correctly?
2. **Security** — SQL injection, auth bypass, data exposure, input validation.
3. **Error handling** — All error paths handled, proper status codes, no leaks.
4. **Performance** — N+1 queries, missing indexes, unnecessary data loading.
5. **Testing** — Adequate coverage, meaningful assertions, edge cases.
6. **Architecture** — Proper layer separation, dependency injection, SOLID.
7. **Observability** — Logging, metrics, error tracking.

Provide specific line-level feedback with severity (blocker/major/minor/nit).
