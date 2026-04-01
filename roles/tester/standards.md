# QA Testing Standards

## Test Coverage
- P0 (critical path) test cases: 100% automated.
- P1 (high priority) test cases: >= 90% automated.
- Overall code coverage target: >= 80% for business logic.
- Every bug fix must have a regression test before closing.

## Test Case Quality
- Every test case must have clear preconditions and expected results.
- Test cases must be independent — no implicit ordering dependencies.
- Test data specified explicitly — no "enter some data" instructions.
- Negative test cases required for all user inputs.

## Bug Report Quality
- Must include reproduction steps that work on first attempt.
- Must include expected vs actual results.
- Must include severity and priority assessment.
- Must include environment information.
- One bug per report — no combo reports.

## Automation Standards
- Tests must be deterministic — no flaky tests in CI.
- Tests must clean up after themselves (no test pollution).
- Test execution time: unit tests < 10s, integration < 60s, e2e < 5min.
- Mocks for external services — no tests that depend on network.

## Process Standards
- Test plan reviewed before development starts.
- Exploratory testing session for every major feature.
- Regression suite run before every release.
- Bug triage within 24 hours of reporting.
