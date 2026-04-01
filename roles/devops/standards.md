# DevOps Standards

## CI/CD
- All deployments through CI/CD pipeline. No manual deployments.
- CI pipeline must complete in < 10 minutes for feedback.
- All tests must pass before merge. No skipping CI.
- Production deploys require at least one approval.
- Every deploy must be rollbackable within 5 minutes.

## Infrastructure
- All infrastructure defined as code. No manual cloud console changes.
- Infrastructure changes go through the same review process as code.
- Environments (dev/staging/prod) must be structurally identical.
- Auto-scaling configured for production workloads.

## Security
- Secrets in secret managers (AWS Secrets Manager, Vault, etc.), never in code.
- Container images scanned for vulnerabilities before deployment.
- Network policies: default deny, explicit allow.
- IAM roles follow least-privilege principle.
- All data encrypted in transit (TLS 1.2+) and at rest.

## Monitoring
- Every service must have health check endpoints.
- Structured JSON logging with correlation IDs.
- Alerts must have runbooks. No alert without an action plan.
- SLO defined for every user-facing service.
- On-call rotation with clear escalation paths.

## Reliability
- Recovery Time Objective (RTO): < 30 minutes for SEV1.
- Recovery Point Objective (RPO): < 1 hour for critical data.
- Disaster recovery plan tested quarterly.
- Chaos engineering exercises for critical systems.
