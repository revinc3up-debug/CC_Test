# Code Review Standards

## Review Process
- All code changes must be reviewed before merge. No exceptions.
- Reviews should be completed within 4 business hours of request.
- Reviewer must understand the purpose of the change (read the ticket/issue).
- At least one approving review required for merge.

## Review Quality
- Every review must check: correctness, security, testing, readability.
- Blocker comments must include a suggested fix or clear explanation.
- Reviews should not block on style preferences — use linters for that.
- Acknowledge good patterns — review is for learning, not just criticism.

## Feedback Standards
- Be specific — "this could fail when X is null" not "needs error handling".
- Provide context — explain WHY something is a problem, not just that it is.
- Use severity labels consistently (Blocker/Major/Minor/Nit).
- One comment per issue — don't pile multiple concerns into one comment.
