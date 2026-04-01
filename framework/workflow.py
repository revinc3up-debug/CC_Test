"""
Workflow orchestrator for multi-role development processes.

Workflows define sequences of role+skill invocations, with dependency
resolution, artifact passing, and conditional branching.
"""

import yaml
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from .role import Role, RoleLoader
from .context import ProjectContext, Artifact


@dataclass
class WorkflowStep:
    """A single step in a workflow."""
    id: str
    role_id: str
    skill_name: str
    description: str = ""
    depends_on: list[str] = field(default_factory=list)
    input_mapping: dict[str, str] = field(default_factory=dict)
    condition: str = ""  # Optional condition to skip this step
    review_required: bool = False


@dataclass
class Workflow:
    """A complete workflow definition."""
    id: str
    name: str
    description: str
    steps: list[WorkflowStep]
    variables: dict[str, Any] = field(default_factory=dict)
    tags: list[str] = field(default_factory=list)


class WorkflowLoader:
    """Loads workflow definitions from YAML files."""

    def __init__(self, workflows_dir: str):
        self.workflows_dir = Path(workflows_dir)

    def list_workflows(self) -> list[str]:
        """List all available workflow IDs."""
        return [
            f.stem for f in self.workflows_dir.glob("*.yaml")
        ]

    def load(self, workflow_id: str) -> Workflow:
        """Load a workflow by its file name (without .yaml)."""
        path = self.workflows_dir / f"{workflow_id}.yaml"
        if not path.exists():
            raise FileNotFoundError(f"Workflow not found: {path}")

        with open(path) as f:
            config = yaml.safe_load(f)

        steps = []
        for step_def in config.get("steps", []):
            steps.append(WorkflowStep(
                id=step_def["id"],
                role_id=step_def["role"],
                skill_name=step_def["skill"],
                description=step_def.get("description", ""),
                depends_on=step_def.get("depends_on", []),
                input_mapping=step_def.get("input_mapping", {}),
                condition=step_def.get("condition", ""),
                review_required=step_def.get("review_required", False),
            ))

        return Workflow(
            id=workflow_id,
            name=config["name"],
            description=config.get("description", ""),
            steps=steps,
            variables=config.get("variables", {}),
            tags=config.get("tags", []),
        )


class WorkflowExecutor:
    """
    Executes a workflow by orchestrating role invocations.

    This is the abstract executor — it resolves dependencies and builds
    prompts. The actual LLM calls are delegated to a callback, making
    this framework LLM-provider agnostic.
    """

    def __init__(self, role_loader: RoleLoader, context: ProjectContext):
        self.role_loader = role_loader
        self.context = context
        self.completed_steps: dict[str, Artifact] = {}

    def resolve_execution_order(self, workflow: Workflow) -> list[list[WorkflowStep]]:
        """
        Resolve steps into execution layers (parallelizable groups).
        Steps with no unmet dependencies can run in parallel.
        """
        remaining = list(workflow.steps)
        completed_ids: set[str] = set()
        layers: list[list[WorkflowStep]] = []

        while remaining:
            # Find all steps whose dependencies are met
            ready = [
                s for s in remaining
                if all(dep in completed_ids for dep in s.depends_on)
            ]
            if not ready:
                unresolved = [s.id for s in remaining]
                raise ValueError(
                    f"Circular or unresolvable dependencies: {unresolved}"
                )

            layers.append(ready)
            for s in ready:
                completed_ids.add(s.id)
                remaining.remove(s)

        return layers

    def build_step_prompt(self, step: WorkflowStep, workflow: Workflow) -> str:
        """Build the complete prompt for a workflow step."""
        role = self.role_loader.load(step.role_id)

        # Build context dict from input mappings and project context
        step_context = {
            "project_summary": self.context.to_summary(),
            **self.context.variables,
            **workflow.variables,
        }

        # Resolve input mappings (artifact references from previous steps)
        for key, source in step.input_mapping.items():
            if source.startswith("step:"):
                ref_step_id = source.split(":", 1)[1]
                if ref_step_id in self.completed_steps:
                    step_context[key] = self.completed_steps[ref_step_id].content
            elif source.startswith("artifact:"):
                artifact_type = source.split(":", 1)[1]
                artifact = self.context.get_latest_artifact(artifact_type)
                if artifact:
                    step_context[key] = artifact.content

        return role.build_prompt(step.skill_name, step_context)

    def record_step_result(
        self, step: WorkflowStep, content: str, metadata: dict | None = None
    ) -> Artifact:
        """Record the result of a completed step."""
        artifact = Artifact(
            id=f"{step.id}",
            role_id=step.role_id,
            skill_name=step.skill_name,
            content=content,
            artifact_type=step.skill_name,
            metadata=metadata or {},
        )
        self.completed_steps[step.id] = artifact
        self.context.add_artifact(artifact)
        return artifact

    def get_execution_plan(self, workflow: Workflow) -> str:
        """Generate a human-readable execution plan."""
        layers = self.resolve_execution_order(workflow)
        lines = [f"# Execution Plan: {workflow.name}\n"]

        for i, layer in enumerate(layers, 1):
            parallel_note = " (parallel)" if len(layer) > 1 else ""
            lines.append(f"## Phase {i}{parallel_note}")
            for step in layer:
                role = self.role_loader.load(step.role_id)
                lines.append(f"  - **{role.title}** → {step.skill_name}")
                if step.description:
                    lines.append(f"    {step.description}")
                if step.depends_on:
                    lines.append(f"    Depends on: {', '.join(step.depends_on)}")
            lines.append("")

        return "\n".join(lines)
