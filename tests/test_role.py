"""Tests for role loading and prompt building."""

import pytest
from pathlib import Path

from framework.role import Role, RoleSkill, RoleLoader


ROLES_DIR = str(Path(__file__).parent.parent / "roles")


class TestRoleSkill:
    def test_basic_creation(self):
        skill = RoleSkill(name="test", description="A test skill")
        assert skill.name == "test"
        assert skill.description == "A test skill"
        assert skill.prompt_template == ""

    def test_with_template(self):
        skill = RoleSkill(
            name="test",
            description="desc",
            prompt_template="Do {{task}} for {{project}}",
            output_format="Markdown",
        )
        assert "{{task}}" in skill.prompt_template


class TestRole:
    def _make_role(self, **kwargs):
        defaults = dict(
            id="test_role",
            name="Test",
            title="Test Role",
            description="A test role",
            system_prompt="You are a test role.",
            skills=[
                RoleSkill(
                    name="do_thing",
                    description="Does a thing",
                    prompt_template="Do {{task}} now.",
                    output_format="Plain text",
                ),
            ],
        )
        defaults.update(kwargs)
        return Role(**defaults)

    def test_get_skill_found(self):
        role = self._make_role()
        skill = role.get_skill("do_thing")
        assert skill is not None
        assert skill.name == "do_thing"

    def test_get_skill_not_found(self):
        role = self._make_role()
        assert role.get_skill("nonexistent") is None

    def test_build_prompt_includes_system(self):
        role = self._make_role()
        prompt = role.build_prompt("do_thing", {"task": "testing"})
        assert "You are a test role." in prompt

    def test_build_prompt_renders_variables(self):
        role = self._make_role()
        prompt = role.build_prompt("do_thing", {"task": "refactoring"})
        assert "Do refactoring now." in prompt
        assert "{{task}}" not in prompt

    def test_build_prompt_includes_standards(self):
        role = self._make_role(standards="Always test your code.")
        prompt = role.build_prompt("do_thing", {"task": "x"})
        assert "Always test your code." in prompt

    def test_build_prompt_includes_output_format(self):
        role = self._make_role()
        prompt = role.build_prompt("do_thing", {"task": "x"})
        assert "Plain text" in prompt

    def test_build_prompt_unknown_skill_raises(self):
        role = self._make_role()
        with pytest.raises(ValueError, match="no skill 'bad'"):
            role.build_prompt("bad", {})


class TestRoleLoader:
    def test_list_roles(self):
        loader = RoleLoader(ROLES_DIR)
        roles = loader.list_roles()
        assert len(roles) == 9
        assert "architect" in roles
        assert "product_manager" in roles
        assert "tester" in roles

    def test_load_architect(self):
        loader = RoleLoader(ROLES_DIR)
        role = loader.load("architect")
        assert role.title == "Software Architect"
        assert len(role.skills) == 5
        assert role.system_prompt  # Not empty
        assert role.standards  # Not empty

    def test_load_all(self):
        loader = RoleLoader(ROLES_DIR)
        all_roles = loader.load_all()
        assert len(all_roles) == 9

    def test_load_caches(self):
        loader = RoleLoader(ROLES_DIR)
        r1 = loader.load("architect")
        r2 = loader.load("architect")
        assert r1 is r2

    def test_load_nonexistent_raises(self):
        loader = RoleLoader(ROLES_DIR)
        with pytest.raises(FileNotFoundError):
            loader.load("nonexistent_role")

    def test_every_role_has_system_prompt(self):
        loader = RoleLoader(ROLES_DIR)
        for role_id in loader.list_roles():
            role = loader.load(role_id)
            assert role.system_prompt, f"{role_id} has empty system prompt"

    def test_every_role_has_skills(self):
        loader = RoleLoader(ROLES_DIR)
        for role_id in loader.list_roles():
            role = loader.load(role_id)
            assert len(role.skills) > 0, f"{role_id} has no skills"

    def test_every_skill_has_prompt_template(self):
        loader = RoleLoader(ROLES_DIR)
        for role_id in loader.list_roles():
            role = loader.load(role_id)
            for skill in role.skills:
                assert skill.prompt_template, (
                    f"{role_id}/{skill.name} has empty prompt template"
                )
