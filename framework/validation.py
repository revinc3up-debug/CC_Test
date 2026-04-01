"""
Configuration validation for roles and workflows.

Catches misconfiguration early with clear error messages.
"""

from pathlib import Path
from dataclasses import dataclass, field

from .role import RoleLoader
from .workflow import WorkflowLoader


@dataclass
class ValidationError:
    """A single validation error."""
    level: str  # "error" or "warning"
    source: str  # e.g. "role:architect" or "workflow:bug_fix"
    message: str

    def __str__(self) -> str:
        icon = "ERROR" if self.level == "error" else "WARN"
        return f"[{icon}] {self.source}: {self.message}"


@dataclass
class ValidationResult:
    """Result of validating the entire configuration."""
    errors: list[ValidationError] = field(default_factory=list)

    @property
    def is_valid(self) -> bool:
        return not any(e.level == "error" for e in self.errors)

    @property
    def error_count(self) -> int:
        return sum(1 for e in self.errors if e.level == "error")

    @property
    def warning_count(self) -> int:
        return sum(1 for e in self.errors if e.level == "warning")

    def add(self, level: str, source: str, message: str) -> None:
        self.errors.append(ValidationError(level, source, message))

    def __str__(self) -> str:
        if not self.errors:
            return "Validation passed: no issues found."
        lines = [str(e) for e in self.errors]
        summary = f"\n{self.error_count} error(s), {self.warning_count} warning(s)"
        return "\n".join(lines) + summary


def validate_roles(role_loader: RoleLoader) -> ValidationResult:
    """Validate all role definitions."""
    result = ValidationResult()

    try:
        role_ids = role_loader.list_roles()
    except Exception as e:
        result.add("error", "roles", f"Cannot list roles: {e}")
        return result

    if not role_ids:
        result.add("warning", "roles", "No roles found in roles directory")
        return result

    for role_id in role_ids:
        source = f"role:{role_id}"
        try:
            role = role_loader.load(role_id)
        except Exception as e:
            result.add("error", source, f"Failed to load: {e}")
            continue

        # Check required fields
        if not role.name:
            result.add("error", source, "Missing 'name' field")
        if not role.system_prompt:
            result.add("error", source, "Missing system prompt (prompts/system.md)")
        if not role.skills:
            result.add("warning", source, "No skills defined")
        if not role.description:
            result.add("warning", source, "Missing description")

        # Check skills have prompt templates
        for skill in role.skills:
            if not skill.prompt_template:
                result.add("warning", source, f"Skill '{skill.name}' has no prompt template")
            if not skill.description:
                result.add("warning", source, f"Skill '{skill.name}' has no description")

        # Check collaborates_with references exist
        for collab in role.collaborates_with:
            if collab not in role_ids:
                result.add("warning", source, f"Collaborates with unknown role: '{collab}'")

    return result


def validate_workflows(workflow_loader: WorkflowLoader, role_loader: RoleLoader) -> ValidationResult:
    """Validate all workflow definitions."""
    result = ValidationResult()

    try:
        workflow_ids = workflow_loader.list_workflows()
    except Exception as e:
        result.add("error", "workflows", f"Cannot list workflows: {e}")
        return result

    if not workflow_ids:
        result.add("warning", "workflows", "No workflows found")
        return result

    available_roles = set(role_loader.list_roles())
    available_skills: dict[str, set[str]] = {}
    for role_id in available_roles:
        try:
            role = role_loader.load(role_id)
            available_skills[role_id] = {s.name for s in role.skills}
        except Exception:
            pass

    for wf_id in workflow_ids:
        source = f"workflow:{wf_id}"
        try:
            wf = workflow_loader.load(wf_id)
        except Exception as e:
            result.add("error", source, f"Failed to load: {e}")
            continue

        if not wf.name:
            result.add("error", source, "Missing 'name' field")
        if not wf.steps:
            result.add("warning", source, "No steps defined")
            continue

        step_ids = {s.id for s in wf.steps}

        for step in wf.steps:
            step_source = f"{source}:step:{step.id}"

            # Check role exists
            if step.role_id not in available_roles:
                result.add("error", step_source, f"Unknown role: '{step.role_id}'")
            elif step.role_id in available_skills:
                # Check skill exists for this role
                if step.skill_name not in available_skills[step.role_id]:
                    result.add("error", step_source,
                               f"Role '{step.role_id}' has no skill '{step.skill_name}'")

            # Check dependencies reference valid step IDs
            for dep in step.depends_on:
                if dep not in step_ids:
                    result.add("error", step_source, f"Depends on unknown step: '{dep}'")

            # Check no self-dependency
            if step.id in step.depends_on:
                result.add("error", step_source, "Step depends on itself")

        # Check for duplicate step IDs
        seen_ids: set[str] = set()
        for step in wf.steps:
            if step.id in seen_ids:
                result.add("error", source, f"Duplicate step ID: '{step.id}'")
            seen_ids.add(step.id)

    return result


def validate_all(role_loader: RoleLoader, workflow_loader: WorkflowLoader) -> ValidationResult:
    """Validate everything — roles and workflows."""
    role_result = validate_roles(role_loader)
    wf_result = validate_workflows(workflow_loader, role_loader)

    combined = ValidationResult()
    combined.errors = role_result.errors + wf_result.errors
    return combined
