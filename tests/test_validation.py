"""Tests for configuration validation."""

import pytest
from pathlib import Path

from framework.validation import validate_roles, validate_workflows, validate_all
from framework.role import RoleLoader
from framework.workflow import WorkflowLoader


ROLES_DIR = str(Path(__file__).parent.parent / "roles")
WORKFLOWS_DIR = str(Path(__file__).parent.parent / "workflows")


class TestValidation:
    def test_all_roles_valid(self):
        result = validate_roles(RoleLoader(ROLES_DIR))
        errors = [e for e in result.errors if e.level == "error"]
        assert len(errors) == 0, f"Role validation errors: {errors}"

    def test_all_workflows_valid(self):
        result = validate_workflows(
            WorkflowLoader(WORKFLOWS_DIR),
            RoleLoader(ROLES_DIR),
        )
        errors = [e for e in result.errors if e.level == "error"]
        assert len(errors) == 0, f"Workflow validation errors: {errors}"

    def test_validate_all_passes(self):
        result = validate_all(
            RoleLoader(ROLES_DIR),
            WorkflowLoader(WORKFLOWS_DIR),
        )
        assert result.is_valid, f"Validation failed:\n{result}"

    def test_missing_roles_dir_handled(self):
        result = validate_roles(RoleLoader("/nonexistent/path"))
        assert not result.is_valid

    def test_empty_roles_dir(self, tmp_path):
        result = validate_roles(RoleLoader(str(tmp_path)))
        assert result.warning_count > 0


class TestValidationEngine:
    def test_all_roles_have_system_prompts(self):
        """Structural test: every role must have a non-empty system prompt."""
        loader = RoleLoader(ROLES_DIR)
        for role_id in loader.list_roles():
            role = loader.load(role_id)
            assert role.system_prompt.strip(), f"{role_id}: empty system prompt"

    def test_all_workflow_steps_reference_valid_roles(self):
        """Structural test: every workflow step must reference an existing role."""
        role_loader = RoleLoader(ROLES_DIR)
        wf_loader = WorkflowLoader(WORKFLOWS_DIR)
        valid_roles = set(role_loader.list_roles())

        for wf_id in wf_loader.list_workflows():
            wf = wf_loader.load(wf_id)
            for step in wf.steps:
                assert step.role_id in valid_roles, (
                    f"Workflow '{wf_id}' step '{step.id}' references "
                    f"unknown role '{step.role_id}'"
                )

    def test_all_workflow_steps_reference_valid_skills(self):
        """Structural test: every workflow step must reference a valid skill."""
        role_loader = RoleLoader(ROLES_DIR)
        wf_loader = WorkflowLoader(WORKFLOWS_DIR)

        role_skills: dict[str, set[str]] = {}
        for role_id in role_loader.list_roles():
            role = role_loader.load(role_id)
            role_skills[role_id] = {s.name for s in role.skills}

        for wf_id in wf_loader.list_workflows():
            wf = wf_loader.load(wf_id)
            for step in wf.steps:
                if step.role_id in role_skills:
                    assert step.skill_name in role_skills[step.role_id], (
                        f"Workflow '{wf_id}' step '{step.id}': "
                        f"role '{step.role_id}' has no skill '{step.skill_name}'"
                    )
