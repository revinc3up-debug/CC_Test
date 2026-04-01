Perform a security-focused review of the following code.

## Project Context
{{project_summary}}

## Code to Review
{{code}}

## Security Review Areas
1. **Injection** — SQL injection, command injection, XSS, template injection.
2. **Authentication** — Auth bypass, session management, token handling.
3. **Authorization** — Privilege escalation, IDOR, missing access checks.
4. **Data Exposure** — Sensitive data in logs, responses, or error messages.
5. **Input Validation** — Missing/incomplete validation, type confusion.
6. **Dependencies** — Known vulnerabilities in dependencies.
7. **Cryptography** — Weak algorithms, hardcoded keys, improper usage.
8. **Configuration** — Debug mode, verbose errors, insecure defaults.

For each finding:
- **Severity**: Critical / High / Medium / Low
- **Location**: File and line
- **Description**: What the issue is
- **Impact**: What an attacker could do
- **Remediation**: How to fix it with code example
