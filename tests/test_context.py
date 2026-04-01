"""Tests for project context and artifact management."""

from framework.context import ProjectContext, Artifact


class TestArtifact:
    def test_creation(self):
        a = Artifact(
            id="test-1",
            role_id="architect",
            skill_name="design_system",
            content="Architecture document...",
            artifact_type="architecture",
        )
        assert a.id == "test-1"
        assert a.created_at  # Auto-generated


class TestProjectContext:
    def _make_context(self):
        return ProjectContext(
            project_name="Test Project",
            project_description="A test project",
            tech_stack={"backend": ["Python", "FastAPI"]},
            constraints=["Must be fast"],
        )

    def test_basic_creation(self):
        ctx = self._make_context()
        assert ctx.project_name == "Test Project"
        assert len(ctx.artifacts) == 0

    def test_add_artifact(self):
        ctx = self._make_context()
        a = Artifact("1", "pm", "write_prd", "PRD content", "prd")
        ctx.add_artifact(a)
        assert len(ctx.artifacts) == 1

    def test_get_artifacts_by_role(self):
        ctx = self._make_context()
        ctx.add_artifact(Artifact("1", "pm", "write_prd", "PRD", "prd"))
        ctx.add_artifact(Artifact("2", "arch", "design", "Arch", "architecture"))
        ctx.add_artifact(Artifact("3", "pm", "stories", "Stories", "user_stories"))

        pm_artifacts = ctx.get_artifacts_by_role("pm")
        assert len(pm_artifacts) == 2

    def test_get_artifacts_by_type(self):
        ctx = self._make_context()
        ctx.add_artifact(Artifact("1", "pm", "write_prd", "PRD1", "prd"))
        ctx.add_artifact(Artifact("2", "pm", "write_prd", "PRD2", "prd"))

        prds = ctx.get_artifacts_by_type("prd")
        assert len(prds) == 2

    def test_get_latest_artifact(self):
        ctx = self._make_context()
        ctx.add_artifact(Artifact("1", "pm", "write_prd", "PRD v1", "prd"))
        ctx.add_artifact(Artifact("2", "pm", "write_prd", "PRD v2", "prd"))

        latest = ctx.get_latest_artifact("prd")
        assert latest is not None
        assert latest.content == "PRD v2"

    def test_get_latest_artifact_none(self):
        ctx = self._make_context()
        assert ctx.get_latest_artifact("nonexistent") is None

    def test_to_summary_includes_project_info(self):
        ctx = self._make_context()
        summary = ctx.to_summary()
        assert "Test Project" in summary
        assert "Python" in summary
        assert "Must be fast" in summary

    def test_to_summary_includes_artifacts(self):
        ctx = self._make_context()
        ctx.add_artifact(Artifact("1", "pm", "write_prd", "content", "prd"))
        summary = ctx.to_summary()
        assert "[prd]" in summary
        assert "pm/write_prd" in summary
