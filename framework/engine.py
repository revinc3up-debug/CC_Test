"""
Core engine that ties together roles, workflows, and context.

Provides the main entry point for using the LLM Dev Organization framework.
"""

import yaml
from pathlib import Path
from typing import Any, Callable

from .role import Role, RoleLoader
from .context import ProjectContext
from .workflow import Workflow, WorkflowLoader, WorkflowExecutor


class DevOrganization:
    """
    The main entry point for the LLM Dev Organization framework.

    Usage:
        org = DevOrganization.from_config("config.yaml")
        roles = org.list_roles()
        prompt = org.invoke_role("architect", "design_system", {...})
        plan = org.plan_workflow("feature_development")
    """

    def __init__(
        self,
        role_loader: RoleLoader,
        workflow_loader: WorkflowLoader,
        project_context: ProjectContext,
    ):
        self.roles = role_loader
        self.workflows = workflow_loader
        self.context = project_context

    @classmethod
    def from_config(cls, config_path: str) -> "DevOrganization":
        """Initialize from a project config YAML file."""
        config_path = Path(config_path)
        base_dir = config_path.parent

        with open(config_path) as f:
            config = yaml.safe_load(f)

        # Resolve directories relative to config file
        roles_dir = base_dir / config.get("roles_dir", "roles")
        workflows_dir = base_dir / config.get("workflows_dir", "workflows")

        role_loader = RoleLoader(str(roles_dir))
        workflow_loader = WorkflowLoader(str(workflows_dir))

        project = config.get("project", {})
        context = ProjectContext(
            project_name=project.get("name", "Unnamed Project"),
            project_description=project.get("description", ""),
            tech_stack=project.get("tech_stack", {}),
            constraints=project.get("constraints", []),
        )

        return cls(role_loader, workflow_loader, context)

    # --- Role Operations ---

    def list_roles(self) -> list[str]:
        """List all available role IDs."""
        return self.roles.list_roles()

    def get_role(self, role_id: str) -> Role:
        """Get a role definition."""
        return self.roles.load(role_id)

    def invoke_role(self, role_id: str, skill_name: str, context: dict | None = None) -> str:
        """
        Build a complete prompt for a role+skill invocation.

        Returns the prompt string ready to send to an LLM.
        The caller is responsible for the actual LLM call.
        """
        role = self.roles.load(role_id)
        merged_context = {
            "project_summary": self.context.to_summary(),
            **self.context.variables,
            **(context or {}),
        }
        return role.build_prompt(skill_name, merged_context)

    def get_role_summary(self, role_id: str) -> str:
        """Get a human-readable summary of a role."""
        role = self.roles.load(role_id)
        lines = [
            f"# {role.title}",
            f"\n{role.description}",
            "\n## Responsibilities",
        ]
        for r in role.responsibilities:
            lines.append(f"- {r}")

        lines.append("\n## Skills")
        for s in role.skills:
            lines.append(f"- **{s.name}**: {s.description}")

        if role.collaborates_with:
            lines.append("\n## Collaborates With")
            for c in role.collaborates_with:
                lines.append(f"- {c}")

        return "\n".join(lines)

    def get_org_chart(self) -> str:
        """Get a summary of the entire organization."""
        roles = self.roles.load_all()
        lines = ["# LLM Dev Organization\n"]

        for role_id, role in sorted(roles.items()):
            skills_str = ", ".join(s.name for s in role.skills)
            lines.append(f"## {role.title}")
            lines.append(f"{role.description}")
            lines.append(f"Skills: {skills_str}\n")

        return "\n".join(lines)

    # --- Workflow Operations ---

    def list_workflows(self) -> list[str]:
        """List all available workflow IDs."""
        return self.workflows.list_workflows()

    def load_workflow(self, workflow_id: str) -> Workflow:
        """Load a workflow definition."""
        return self.workflows.load(workflow_id)

    def create_executor(self) -> WorkflowExecutor:
        """Create a workflow executor bound to the current context."""
        return WorkflowExecutor(self.roles, self.context)

    def plan_workflow(self, workflow_id: str) -> str:
        """Generate an execution plan for a workflow."""
        workflow = self.workflows.load(workflow_id)
        executor = self.create_executor()
        return executor.get_execution_plan(workflow)
