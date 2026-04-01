"""
Shared context management for cross-role collaboration.

The context holds project information, artifacts produced by each role,
and the conversation history for the current workflow execution.
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any


@dataclass
class Artifact:
    """An output produced by a role during workflow execution."""
    id: str
    role_id: str
    skill_name: str
    content: str
    artifact_type: str  # e.g. "prd", "architecture", "code", "test_plan"
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class ProjectContext:
    """Shared context accessible by all roles in a workflow."""
    project_name: str
    project_description: str = ""
    tech_stack: dict[str, list[str]] = field(default_factory=dict)
    constraints: list[str] = field(default_factory=list)
    artifacts: list[Artifact] = field(default_factory=list)
    variables: dict[str, Any] = field(default_factory=dict)

    def add_artifact(self, artifact: Artifact) -> None:
        """Add a new artifact to the context."""
        self.artifacts.append(artifact)

    def get_artifacts_by_role(self, role_id: str) -> list[Artifact]:
        """Get all artifacts produced by a specific role."""
        return [a for a in self.artifacts if a.role_id == role_id]

    def get_artifacts_by_type(self, artifact_type: str) -> list[Artifact]:
        """Get all artifacts of a specific type."""
        return [a for a in self.artifacts if a.artifact_type == artifact_type]

    def get_latest_artifact(self, artifact_type: str) -> Artifact | None:
        """Get the most recent artifact of a given type."""
        matching = self.get_artifacts_by_type(artifact_type)
        return matching[-1] if matching else None

    def to_summary(self) -> str:
        """Generate a text summary of the current context for prompt injection."""
        lines = [
            f"# Project: {self.project_name}",
            f"\n{self.project_description}" if self.project_description else "",
        ]

        if self.tech_stack:
            lines.append("\n## Tech Stack")
            for category, techs in self.tech_stack.items():
                lines.append(f"- **{category}**: {', '.join(techs)}")

        if self.constraints:
            lines.append("\n## Constraints")
            for c in self.constraints:
                lines.append(f"- {c}")

        if self.artifacts:
            lines.append("\n## Completed Artifacts")
            for a in self.artifacts:
                lines.append(f"- [{a.artifact_type}] by {a.role_id}/{a.skill_name}")

        return "\n".join(lines)
