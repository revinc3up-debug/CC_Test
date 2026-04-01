"""
Workflow runner — executes workflows end-to-end with an LLM adapter.

Bridges the gap between prompt generation (WorkflowExecutor) and actual
LLM invocation. Handles phased execution, progress reporting, artifact
persistence, and error recovery.
"""

import json
import os
import time
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any, Callable

from .adapter import LLMAdapter, LLMResponse
from .context import ProjectContext, Artifact
from .role import RoleLoader
from .workflow import Workflow, WorkflowLoader, WorkflowExecutor, WorkflowStep


@dataclass
class StepResult:
    """Result of executing a single workflow step."""
    step_id: str
    role_id: str
    skill_name: str
    prompt: str
    response: LLMResponse
    duration_secs: float
    status: str = "completed"  # completed | failed | skipped


@dataclass
class RunResult:
    """Result of executing an entire workflow."""
    workflow_id: str
    workflow_name: str
    step_results: list[StepResult] = field(default_factory=list)
    started_at: str = field(default_factory=lambda: datetime.now().isoformat())
    finished_at: str = ""
    status: str = "running"  # running | completed | failed

    @property
    def total_duration(self) -> float:
        return sum(r.duration_secs for r in self.step_results)

    @property
    def total_tokens(self) -> dict[str, int]:
        totals: dict[str, int] = {"input_tokens": 0, "output_tokens": 0}
        for r in self.step_results:
            for key in totals:
                totals[key] += r.response.usage.get(key, 0)
        return totals

    def summary(self) -> str:
        lines = [
            f"# Run Summary: {self.workflow_name}",
            f"Status: {self.status}",
            f"Duration: {self.total_duration:.1f}s",
            f"Steps: {len(self.step_results)}",
        ]
        tokens = self.total_tokens
        if any(tokens.values()):
            lines.append(f"Tokens: {tokens['input_tokens']} in / {tokens['output_tokens']} out")
        lines.append("")
        for r in self.step_results:
            icon = "+" if r.status == "completed" else "x" if r.status == "failed" else "-"
            lines.append(f"  [{icon}] {r.step_id} ({r.role_id}/{r.skill_name}) — {r.duration_secs:.1f}s")
        return "\n".join(lines)


# Type for progress callbacks
ProgressCallback = Callable[[str, WorkflowStep, int, int], None]


class WorkflowRunner:
    """
    Runs a workflow end-to-end by invoking an LLM adapter for each step.

    Usage:
        runner = WorkflowRunner(adapter, role_loader, context)
        result = runner.run(workflow, on_progress=print_progress)
    """

    def __init__(
        self,
        adapter: LLMAdapter,
        role_loader: RoleLoader,
        context: ProjectContext,
    ):
        self.adapter = adapter
        self.executor = WorkflowExecutor(role_loader, context)
        self.context = context

    def run(
        self,
        workflow: Workflow,
        on_progress: ProgressCallback | None = None,
        save_to: str | None = None,
    ) -> RunResult:
        """
        Execute a workflow from start to finish.

        Args:
            workflow: The workflow to execute.
            on_progress: Optional callback called before each step.
            save_to: Optional directory to save artifacts as files.
        """
        result = RunResult(
            workflow_id=workflow.id,
            workflow_name=workflow.name,
        )

        layers = self.executor.resolve_execution_order(workflow)
        total_steps = sum(len(layer) for layer in layers)
        step_num = 0

        if save_to:
            os.makedirs(save_to, exist_ok=True)

        try:
            for phase_idx, layer in enumerate(layers):
                for step in layer:
                    step_num += 1

                    if on_progress:
                        on_progress(
                            f"Phase {phase_idx + 1}: {step.role_id}/{step.skill_name}",
                            step,
                            step_num,
                            total_steps,
                        )

                    step_result = self._execute_step(step, workflow)
                    result.step_results.append(step_result)

                    if step_result.status == "failed":
                        result.status = "failed"
                        result.finished_at = datetime.now().isoformat()
                        return result

                    # Save artifact to file if requested
                    if save_to:
                        self._save_artifact(save_to, step, step_result)

            result.status = "completed"

        except Exception as e:
            result.status = "failed"
            result.step_results.append(StepResult(
                step_id="__error__",
                role_id="system",
                skill_name="error",
                prompt="",
                response=LLMResponse(content=str(e)),
                duration_secs=0,
                status="failed",
            ))

        result.finished_at = datetime.now().isoformat()
        return result

    def run_step(self, workflow: Workflow, step_id: str) -> StepResult:
        """Execute a single step from a workflow (useful for selective re-runs)."""
        step = next((s for s in workflow.steps if s.id == step_id), None)
        if not step:
            raise ValueError(f"Step '{step_id}' not found in workflow '{workflow.id}'")
        return self._execute_step(step, workflow)

    def _execute_step(self, step: WorkflowStep, workflow: Workflow) -> StepResult:
        """Execute a single workflow step."""
        prompt = self.executor.build_step_prompt(step, workflow)

        start = time.time()
        try:
            response = self.adapter.send(prompt)
            duration = time.time() - start

            # Record the result so downstream steps can reference it
            self.executor.record_step_result(step, response.content)

            return StepResult(
                step_id=step.id,
                role_id=step.role_id,
                skill_name=step.skill_name,
                prompt=prompt,
                response=response,
                duration_secs=duration,
                status="completed",
            )
        except Exception as e:
            duration = time.time() - start
            return StepResult(
                step_id=step.id,
                role_id=step.role_id,
                skill_name=step.skill_name,
                prompt=prompt,
                response=LLMResponse(content=f"Error: {e}"),
                duration_secs=duration,
                status="failed",
            )

    def _save_artifact(self, output_dir: str, step: WorkflowStep, result: StepResult) -> None:
        """Save a step result as a markdown file."""
        filename = f"{step.id}__{step.role_id}__{step.skill_name}.md"
        filepath = os.path.join(output_dir, filename)
        with open(filepath, "w") as f:
            f.write(f"# {step.id}\n")
            f.write(f"**Role**: {step.role_id} | **Skill**: {step.skill_name}\n")
            f.write(f"**Duration**: {result.duration_secs:.1f}s\n\n---\n\n")
            f.write(result.response.content)
