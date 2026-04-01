# Backend Development Standards

## Code Architecture
- Three-layer architecture: Handler/Controller → Service → Repository.
- No business logic in handlers. Handlers only parse requests and format responses.
- No database queries in services. Services use repository interfaces.
- All external dependencies injected via constructor.

## API Standards
- Validate all request inputs with schema validation (Joi, Zod, Pydantic, etc.).
- Return consistent error format: { "error": { "code", "message", "details" } }.
- Log all requests with correlation ID, duration, and status.
- Rate-limit public endpoints. Authentication required for all non-public routes.

## Security Standards
- Parameterized queries only. Never string-concatenate SQL.
- Hash passwords with bcrypt (cost factor >= 12) or argon2.
- JWT tokens expire in <= 1 hour. Refresh tokens in <= 7 days.
- All sensitive data encrypted at rest.
- No secrets in code or config files — use environment variables.

## Database Standards
- All schema changes via versioned migrations. Never modify DB directly.
- Use transactions for multi-table writes.
- Optimize queries hitting > 1000 rows with proper indexes.
- Connection pooling configured appropriately for expected load.

## Testing Standards
- Minimum 80% code coverage for business logic.
- Integration tests for all API endpoints (happy path + error cases).
- Unit tests for all service methods with mocked dependencies.
- Every bug fix must include a regression test.
- Use factories/fixtures for test data — no hardcoded magic values.

## Error Handling
- Custom error types for domain errors (NotFound, Unauthorized, ValidationError, etc.).
- Never expose internal errors (stack traces, SQL) to clients.
- Log all errors with full context for debugging.
- Circuit breakers for external service calls.
