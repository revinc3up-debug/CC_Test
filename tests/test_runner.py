"""Tests for the workflow runner."""

import pytest
from pathlib import Path

from framework.adapter import LLMAdapter, LLMResponse, FileAdapter
from framework.context import ProjectContext
from framework.role import RoleLoader
from framework.runner import WorkflowRunner, RunResult, StepResult
from framework.workflow import Workflow, WorkflowStep, WorkflowLoader


ROLES_DIR = str(Path(__file__).parent.parent / "roles")
WORKFLOWS_DIR = str(Path(__file__).parent.parent / "workflows")


class MockAdapter(LLMAdapter):
    """Test adapter that returns predictable responses."""

    def __init__(self, responses: list[str] | None = None):
        self._responses = responses or []
        self._call_count = 0
        self.prompts_received: list[str] = []

    def send(self, prompt: str, system_prompt: str = "", **kwargs) -> LLMResponse:
        self.prompts_received.append(prompt)
        idx = min(self._call_count, len(self._responses) - 1)
        content = self._responses[idx] if self._responses else f"Response {self._call_count + 1}"
        self._call_count += 1
        return LLMResponse(content=content, model="mock", usage={"input_tokens": 10, "output_tokens": 20})

    def name(self) -> str:
        return "mock"


class TestWorkflowRunner:
    def _make_runner(self, responses: list[str] | None = None):
        adapter = MockAdapter(responses)
        role_loader = RoleLoader(ROLES_DIR)
        context = ProjectContext(project_name="Test")
        return WorkflowRunner(adapter, role_loader, context), adapter

    def test_run_simple_workflow(self):
        runner, adapter = self._make_runner(["Design output", "API output"])
        wf = Workflow(
            id="test",
            name="Test",
            description="",
            steps=[
                WorkflowStep(id="a", role_id="architect", skill_name="design_system"),
                WorkflowStep(id="b", role_id="architect", skill_name="design_api", depends_on=["a"]),
            ],
        )
        result = runner.run(wf)
        assert result.status == "completed"
        assert len(result.step_results) == 2
        assert result.step_results[0].response.content == "Design output"
        assert result.step_results[1].response.content == "API output"

    def test_run_records_artifacts(self):
        runner, _ = self._make_runner(["Output A", "Output B"])
        wf = Workflow(
            id="test",
            name="Test",
            description="",
            steps=[
                WorkflowStep(id="a", role_id="architect", skill_name="design_system"),
                WorkflowStep(id="b", role_id="architect", skill_name="design_api",
                             depends_on=["a"],
                             input_mapping={"architecture": "step:a"}),
            ],
        )
        result = runner.run(wf)
        assert result.status == "completed"
        # Step b's prompt should contain output from step a
        assert len(runner.executor.completed_steps) == 2

    def test_run_saves_artifacts(self, tmp_path):
        runner, _ = self._make_runner(["Design output"])
        wf = Workflow(
            id="test",
            name="Test",
            description="",
            steps=[
                WorkflowStep(id="step1", role_id="architect", skill_name="design_system"),
            ],
        )
        result = runner.run(wf, save_to=str(tmp_path))
        assert result.status == "completed"
        files = list(tmp_path.glob("*.md"))
        assert len(files) >= 1

    def test_run_progress_callback(self):
        runner, _ = self._make_runner()
        wf = Workflow(
            id="test",
            name="Test",
            description="",
            steps=[
                WorkflowStep(id="a", role_id="architect", skill_name="design_system"),
                WorkflowStep(id="b", role_id="tester", skill_name="create_test_plan"),
            ],
        )
        progress_messages = []

        def on_progress(msg, step, current, total):
            progress_messages.append((msg, current, total))

        runner.run(wf, on_progress=on_progress)
        assert len(progress_messages) == 2
        assert progress_messages[0][1] == 1  # step 1
        assert progress_messages[1][2] == 2  # total 2

    def test_run_real_bug_fix_workflow(self):
        """Verify the runner can execute the real bug_fix workflow."""
        loader = WorkflowLoader(WORKFLOWS_DIR)
        wf = loader.load("bug_fix")
        runner, adapter = self._make_runner(["Fix it"] * 10)
        result = runner.run(wf)
        assert result.status == "completed"
        assert len(result.step_results) == 6
        assert adapter._call_count == 6

    def test_run_step_individually(self):
        runner, _ = self._make_runner(["Single step output"])
        wf = Workflow(
            id="test",
            name="Test",
            description="",
            steps=[
                WorkflowStep(id="a", role_id="architect", skill_name="design_system"),
            ],
        )
        result = runner.run_step(wf, "a")
        assert result.status == "completed"
        assert result.step_id == "a"

    def test_run_step_unknown_raises(self):
        runner, _ = self._make_runner()
        wf = Workflow(id="test", name="Test", description="", steps=[])
        with pytest.raises(ValueError, match="not found"):
            runner.run_step(wf, "nonexistent")


class TestRunResult:
    def test_summary(self):
        result = RunResult(workflow_id="test", workflow_name="Test Workflow")
        result.step_results.append(StepResult(
            step_id="a", role_id="arch", skill_name="design",
            prompt="p", response=LLMResponse(content="r", usage={"input_tokens": 10, "output_tokens": 20}),
            duration_secs=1.5,
        ))
        summary = result.summary()
        assert "Test Workflow" in summary
        assert "1.5s" in summary

    def test_total_tokens(self):
        result = RunResult(workflow_id="test", workflow_name="Test")
        result.step_results.append(StepResult(
            step_id="a", role_id="x", skill_name="y",
            prompt="", response=LLMResponse(content="", usage={"input_tokens": 100, "output_tokens": 50}),
            duration_secs=0,
        ))
        result.step_results.append(StepResult(
            step_id="b", role_id="x", skill_name="y",
            prompt="", response=LLMResponse(content="", usage={"input_tokens": 200, "output_tokens": 100}),
            duration_secs=0,
        ))
        assert result.total_tokens == {"input_tokens": 300, "output_tokens": 150}
