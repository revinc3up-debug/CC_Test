# Architecture Standards

## Design Standards
- All architecture decisions must be documented as ADRs (Architecture Decision Records).
- Components must communicate through well-defined interfaces (API contracts first).
- Every service must have health checks, structured logging, and metrics endpoints.
- Database schema changes must be backwards-compatible and use migrations.

## API Standards
- RESTful APIs follow resource-oriented design.
- Use consistent naming: plural nouns for collections, kebab-case for URLs.
- All APIs must have versioning (URL prefix: /api/v1/).
- Pagination required for all list endpoints (cursor-based preferred).
- Consistent error response format: { "error": { "code", "message", "details" } }.

## Security Standards
- Authentication via JWT or OAuth2 — no session-based auth for APIs.
- All inputs validated and sanitized at the API boundary.
- Secrets never in code — use environment variables or secret managers.
- HTTPS everywhere. No exceptions.

## Data Standards
- All timestamps in UTC, stored as ISO 8601.
- UUIDs for public-facing IDs, auto-increment for internal PKs.
- Soft deletes for user-facing data, hard deletes only for truly ephemeral data.
- Audit columns (created_at, updated_at, created_by) on all tables.
