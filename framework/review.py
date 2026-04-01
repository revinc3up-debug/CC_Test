"""
Auto-review pipeline — multi-perspective automated code/design review.

Orchestrates parallel reviews from different specialist roles, then
consolidates findings into a unified, prioritized review report.
"""

from dataclasses import dataclass, field

from .adapter import LLMAdapter, LLMResponse
from .context import ProjectContext
from .role import RoleLoader


@dataclass
class ReviewFinding:
    """A single finding from a review."""
    reviewer: str  # role title
    severity: str  # blocker | major | minor | nit
    category: str  # correctness | security | performance | style | architecture
    description: str
    suggestion: str = ""


@dataclass
class ReviewReport:
    """Consolidated review report from multiple reviewers."""
    findings: list[ReviewFinding] = field(default_factory=list)
    raw_reviews: dict[str, str] = field(default_factory=dict)
    consolidated_summary: str = ""
    verdict: str = ""  # approve | request_changes | needs_discussion

    @property
    def blocker_count(self) -> int:
        return sum(1 for f in self.findings if f.severity == "blocker")

    @property
    def major_count(self) -> int:
        return sum(1 for f in self.findings if f.severity == "major")

    def format_report(self) -> str:
        """Generate a human-readable review report."""
        lines = [
            "# Automated Review Report",
            f"\nVerdict: **{self.verdict.upper()}**",
            f"Findings: {self.blocker_count} blockers, {self.major_count} major, "
            f"{len(self.findings) - self.blocker_count - self.major_count} other\n",
        ]

        if self.consolidated_summary:
            lines.append(f"## Summary\n{self.consolidated_summary}\n")

        # Group findings by severity
        for severity in ["blocker", "major", "minor", "nit"]:
            group = [f for f in self.findings if f.severity == severity]
            if group:
                lines.append(f"## {severity.upper()} ({len(group)})")
                for f in group:
                    lines.append(f"- **[{f.category}]** ({f.reviewer}): {f.description}")
                    if f.suggestion:
                        lines.append(f"  Suggestion: {f.suggestion}")
                lines.append("")

        if self.raw_reviews:
            lines.append("---\n## Raw Reviews")
            for reviewer, content in self.raw_reviews.items():
                lines.append(f"\n### {reviewer}\n{content}\n")

        return "\n".join(lines)


class AutoReviewer:
    """
    Automated multi-perspective review pipeline.

    Runs the content through multiple specialist reviewers in parallel
    (conceptually), then consolidates findings into a prioritized report.
    """

    # Default review perspectives
    DEFAULT_PERSPECTIVES = [
        ("code_reviewer", "review_pull_request"),
        ("code_reviewer", "review_security"),
    ]

    def __init__(
        self,
        adapter: LLMAdapter,
        role_loader: RoleLoader,
        context: ProjectContext,
    ):
        self.adapter = adapter
        self.role_loader = role_loader
        self.context = context

    def review(
        self,
        content: str,
        content_type: str = "code",
        perspectives: list[tuple[str, str]] | None = None,
        extra_context: dict[str, str] | None = None,
    ) -> ReviewReport:
        """
        Run automated review from multiple perspectives.

        Args:
            content: The content to review (code, design doc, PRD, etc.)
            content_type: Type of content being reviewed.
            perspectives: List of (role_id, skill_name) tuples for reviewers.
            extra_context: Additional context to pass to reviewers.
        """
        if perspectives is None:
            perspectives = self._default_perspectives_for(content_type)

        report = ReviewReport()

        # Run each review perspective
        for role_id, skill_name in perspectives:
            role = self.role_loader.load(role_id)
            review_context = {
                "project_summary": self.context.to_summary(),
                "code_changes": content,
                "code": content,
                "content_to_review": content,
                "pr_description": f"Review of {content_type} content",
                "proposal": content,
                **(extra_context or {}),
            }

            prompt = role.build_prompt(skill_name, review_context)
            response = self.adapter.send(prompt)
            report.raw_reviews[f"{role.title} ({skill_name})"] = response.content

        # Consolidate reviews into structured findings
        report = self._consolidate(report, content_type)

        return report

    def review_architecture(self, design_doc: str, **kwargs) -> ReviewReport:
        """Shortcut: review an architecture design."""
        return self.review(
            content=design_doc,
            content_type="architecture",
            perspectives=[
                ("architect", "review_architecture"),
                ("code_reviewer", "review_security"),
                ("devops", "setup_monitoring"),  # operational readiness check
            ],
            **kwargs,
        )

    def review_code(self, code: str, **kwargs) -> ReviewReport:
        """Shortcut: review code changes."""
        return self.review(
            content=code,
            content_type="code",
            **kwargs,
        )

    def review_prd(self, prd: str, **kwargs) -> ReviewReport:
        """Shortcut: review a Product Requirements Document."""
        return self.review(
            content=prd,
            content_type="prd",
            perspectives=[
                ("architect", "review_architecture"),
                ("tester", "review_test_coverage"),
            ],
            **kwargs,
        )

    def _default_perspectives_for(self, content_type: str) -> list[tuple[str, str]]:
        """Choose review perspectives based on content type."""
        perspectives_map = {
            "code": [
                ("code_reviewer", "review_pull_request"),
                ("code_reviewer", "review_security"),
            ],
            "frontend": [
                ("code_reviewer", "review_pull_request"),
                ("frontend_developer", "review_frontend"),
            ],
            "backend": [
                ("code_reviewer", "review_pull_request"),
                ("code_reviewer", "review_security"),
                ("backend_developer", "review_backend"),
            ],
            "architecture": [
                ("architect", "review_architecture"),
                ("code_reviewer", "review_security"),
            ],
            "prd": [
                ("architect", "review_architecture"),
                ("tester", "review_test_coverage"),
            ],
        }
        return perspectives_map.get(content_type, self.DEFAULT_PERSPECTIVES)

    def _consolidate(self, report: ReviewReport, content_type: str) -> ReviewReport:
        """
        Consolidate raw reviews into structured findings using the LLM.
        """
        if not report.raw_reviews:
            report.verdict = "approve"
            report.consolidated_summary = "No reviews performed."
            return report

        all_reviews = "\n\n---\n\n".join(
            f"## {reviewer}\n{content}"
            for reviewer, content in report.raw_reviews.items()
        )

        consolidation_prompt = f"""You are a senior engineering lead consolidating multiple code review perspectives into a single, actionable report.

## Reviews to Consolidate
{all_reviews}

## Your Task
1. Extract all distinct findings (deduplicate across reviewers).
2. For each finding, provide:
   - SEVERITY: blocker | major | minor | nit
   - CATEGORY: correctness | security | performance | architecture | style | testing
   - REVIEWER: which reviewer found it
   - DESCRIPTION: clear one-line description
   - SUGGESTION: how to fix it (one line)

3. Determine overall VERDICT:
   - APPROVE: no blockers, <= 2 major issues
   - REQUEST_CHANGES: any blockers or > 2 major issues
   - NEEDS_DISCUSSION: ambiguous or conflicting feedback

Format each finding as:
FINDING|severity|category|reviewer|description|suggestion

End with:
VERDICT: approve/request_changes/needs_discussion
SUMMARY: one-paragraph overall assessment
"""

        response = self.adapter.send(consolidation_prompt)
        report = self._parse_consolidated(response.content, report)
        return report

    def _parse_consolidated(self, text: str, report: ReviewReport) -> ReviewReport:
        """Parse the consolidation LLM response into structured findings."""
        for line in text.split("\n"):
            line = line.strip()

            if line.startswith("FINDING|"):
                parts = line.split("|")
                if len(parts) >= 6:
                    report.findings.append(ReviewFinding(
                        severity=parts[1].strip().lower(),
                        category=parts[2].strip().lower(),
                        reviewer=parts[3].strip(),
                        description=parts[4].strip(),
                        suggestion=parts[5].strip() if len(parts) > 5 else "",
                    ))

            elif line.upper().startswith("VERDICT:"):
                verdict = line.split(":", 1)[1].strip().lower()
                if verdict in ("approve", "request_changes", "needs_discussion"):
                    report.verdict = verdict

            elif line.upper().startswith("SUMMARY:"):
                report.consolidated_summary = line.split(":", 1)[1].strip()

        # Default verdict if not parsed
        if not report.verdict:
            report.verdict = "request_changes" if report.blocker_count > 0 else "approve"

        return report
