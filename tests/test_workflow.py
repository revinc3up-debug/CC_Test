"""Tests for workflow loading, dependency resolution, and execution."""

import pytest
from pathlib import Path

from framework.workflow import WorkflowStep, Workflow, WorkflowLoader, WorkflowExecutor
from framework.role import RoleLoader
from framework.context import ProjectContext


ROLES_DIR = str(Path(__file__).parent.parent / "roles")
WORKFLOWS_DIR = str(Path(__file__).parent.parent / "workflows")


class TestWorkflowLoader:
    def test_list_workflows(self):
        loader = WorkflowLoader(WORKFLOWS_DIR)
        wfs = loader.list_workflows()
        assert "feature_development" in wfs
        assert "bug_fix" in wfs
        assert len(wfs) == 5

    def test_load_feature_development(self):
        loader = WorkflowLoader(WORKFLOWS_DIR)
        wf = loader.load("feature_development")
        assert wf.name == "Feature Development"
        assert len(wf.steps) == 18

    def test_load_nonexistent_raises(self):
        loader = WorkflowLoader(WORKFLOWS_DIR)
        with pytest.raises(FileNotFoundError):
            loader.load("nonexistent_workflow")


class TestWorkflowExecutor:
    def _make_executor(self):
        role_loader = RoleLoader(ROLES_DIR)
        context = ProjectContext(project_name="Test")
        return WorkflowExecutor(role_loader, context)

    def test_resolve_linear_workflow(self):
        executor = self._make_executor()
        wf = Workflow(
            id="test",
            name="Test",
            description="",
            steps=[
                WorkflowStep(id="a", role_id="architect", skill_name="design_system"),
                WorkflowStep(id="b", role_id="architect", skill_name="design_api", depends_on=["a"]),
                WorkflowStep(id="c", role_id="tester", skill_name="create_test_plan", depends_on=["b"]),
            ],
        )
        layers = executor.resolve_execution_order(wf)
        assert len(layers) == 3
        assert layers[0][0].id == "a"
        assert layers[1][0].id == "b"
        assert layers[2][0].id == "c"

    def test_resolve_parallel_workflow(self):
        executor = self._make_executor()
        wf = Workflow(
            id="test",
            name="Test",
            description="",
            steps=[
                WorkflowStep(id="a", role_id="architect", skill_name="design_system"),
                WorkflowStep(id="b", role_id="tester", skill_name="create_test_plan"),
                WorkflowStep(id="c", role_id="devops", skill_name="design_cicd"),
            ],
        )
        layers = executor.resolve_execution_order(wf)
        # All three are independent, should be one parallel layer
        assert len(layers) == 1
        assert len(layers[0]) == 3

    def test_resolve_diamond_dependency(self):
        executor = self._make_executor()
        wf = Workflow(
            id="test",
            name="Test",
            description="",
            steps=[
                WorkflowStep(id="a", role_id="architect", skill_name="design_system"),
                WorkflowStep(id="b", role_id="architect", skill_name="design_api", depends_on=["a"]),
                WorkflowStep(id="c", role_id="architect", skill_name="design_database", depends_on=["a"]),
                WorkflowStep(id="d", role_id="tester", skill_name="create_test_plan", depends_on=["b", "c"]),
            ],
        )
        layers = executor.resolve_execution_order(wf)
        assert len(layers) == 3
        assert len(layers[1]) == 2  # b and c in parallel

    def test_resolve_circular_dependency_raises(self):
        executor = self._make_executor()
        wf = Workflow(
            id="test",
            name="Test",
            description="",
            steps=[
                WorkflowStep(id="a", role_id="architect", skill_name="design_system", depends_on=["b"]),
                WorkflowStep(id="b", role_id="tester", skill_name="create_test_plan", depends_on=["a"]),
            ],
        )
        with pytest.raises(ValueError, match="Circular"):
            executor.resolve_execution_order(wf)

    def test_build_step_prompt(self):
        executor = self._make_executor()
        step = WorkflowStep(id="a", role_id="architect", skill_name="design_system")
        wf = Workflow(id="test", name="Test", description="", steps=[step])
        prompt = executor.build_step_prompt(step, wf)
        assert "Software Architect" in prompt or "system" in prompt.lower()

    def test_record_step_result(self):
        executor = self._make_executor()
        step = WorkflowStep(id="a", role_id="architect", skill_name="design_system")
        artifact = executor.record_step_result(step, "Architecture output")
        assert artifact.content == "Architecture output"
        assert "a" in executor.completed_steps
        assert len(executor.context.artifacts) == 1

    def test_resolve_real_feature_workflow(self):
        """Verify the actual feature_development workflow resolves without errors."""
        loader = WorkflowLoader(WORKFLOWS_DIR)
        wf = loader.load("feature_development")
        executor = self._make_executor()
        layers = executor.resolve_execution_order(wf)
        assert len(layers) >= 5  # Should have multiple phases
        total_steps = sum(len(layer) for layer in layers)
        assert total_steps == 18

    def test_resolve_all_real_workflows(self):
        """Verify all workflows resolve without errors."""
        loader = WorkflowLoader(WORKFLOWS_DIR)
        executor = self._make_executor()
        for wf_id in loader.list_workflows():
            wf = loader.load(wf_id)
            layers = executor.resolve_execution_order(wf)
            assert len(layers) > 0, f"Workflow {wf_id} has no execution layers"
