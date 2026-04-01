"""Tests for the auto-review pipeline."""

import pytest
from pathlib import Path

from framework.adapter import LLMAdapter, LLMResponse
from framework.context import ProjectContext
from framework.role import RoleLoader
from framework.review import AutoReviewer, ReviewReport, ReviewFinding


ROLES_DIR = str(Path(__file__).parent.parent / "roles")


class MockReviewAdapter(LLMAdapter):
    """Adapter that returns review-like responses."""

    def __init__(self):
        self._call_count = 0

    def send(self, prompt: str, system_prompt: str = "", **kwargs) -> LLMResponse:
        self._call_count += 1

        if "consolidat" in prompt.lower():
            # Consolidation prompt — return structured findings
            return LLMResponse(
                content=(
                    "FINDING|blocker|security|Code Reviewer|SQL injection in login handler|Use parameterized queries\n"
                    "FINDING|major|performance|Code Reviewer|N+1 query in user list|Add eager loading\n"
                    "FINDING|minor|style|Code Reviewer|Inconsistent naming|Use camelCase consistently\n"
                    "VERDICT: request_changes\n"
                    "SUMMARY: Security issue must be fixed before merge."
                ),
                model="mock",
            )
        else:
            # Individual review
            return LLMResponse(
                content=f"Review feedback #{self._call_count}: Found some issues.",
                model="mock",
            )

    def name(self) -> str:
        return "mock-review"


class TestAutoReviewer:
    def _make_reviewer(self):
        adapter = MockReviewAdapter()
        role_loader = RoleLoader(ROLES_DIR)
        context = ProjectContext(project_name="Test")
        return AutoReviewer(adapter, role_loader, context)

    def test_review_code(self):
        reviewer = self._make_reviewer()
        report = reviewer.review_code("function login(user, pass) { ... }")
        assert report.verdict in ("approve", "request_changes", "needs_discussion")
        assert len(report.raw_reviews) > 0

    def test_review_architecture(self):
        reviewer = self._make_reviewer()
        report = reviewer.review_architecture("## System Design\nMicroservices with REST...")
        assert len(report.raw_reviews) > 0

    def test_review_prd(self):
        reviewer = self._make_reviewer()
        report = reviewer.review_prd("## PRD: User Auth\nObjectives: ...")
        assert len(report.raw_reviews) > 0

    def test_review_parses_findings(self):
        reviewer = self._make_reviewer()
        report = reviewer.review_code("some code")
        assert len(report.findings) == 3
        assert report.blocker_count == 1
        assert report.major_count == 1

    def test_review_verdict(self):
        reviewer = self._make_reviewer()
        report = reviewer.review_code("some code")
        assert report.verdict == "request_changes"

    def test_review_custom_perspectives(self):
        reviewer = self._make_reviewer()
        report = reviewer.review(
            content="some code",
            content_type="code",
            perspectives=[
                ("code_reviewer", "review_pull_request"),
            ],
        )
        # One perspective + consolidation = 2 adapter calls
        assert len(report.raw_reviews) == 1

    def test_format_report(self):
        reviewer = self._make_reviewer()
        report = reviewer.review_code("x")
        formatted = report.format_report()
        assert "Automated Review Report" in formatted
        assert "BLOCKER" in formatted
        assert "SQL injection" in formatted


class TestReviewReport:
    def test_empty_report(self):
        report = ReviewReport()
        assert report.blocker_count == 0
        assert report.major_count == 0

    def test_counts(self):
        report = ReviewReport(findings=[
            ReviewFinding("r1", "blocker", "security", "issue 1"),
            ReviewFinding("r2", "blocker", "correctness", "issue 2"),
            ReviewFinding("r3", "major", "performance", "issue 3"),
            ReviewFinding("r4", "minor", "style", "issue 4"),
        ])
        assert report.blocker_count == 2
        assert report.major_count == 1

    def test_format_empty(self):
        report = ReviewReport(verdict="approve")
        formatted = report.format_report()
        assert "APPROVE" in formatted
