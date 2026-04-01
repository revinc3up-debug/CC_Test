"""Tests for the DevOrganization engine."""

import pytest
from pathlib import Path

from framework.engine import DevOrganization


CONFIG_PATH = str(Path(__file__).parent.parent / "config.yaml")


class TestDevOrganization:
    def test_from_config(self):
        org = DevOrganization.from_config(CONFIG_PATH)
        assert org.context.project_name == "My Project"

    def test_list_roles(self):
        org = DevOrganization.from_config(CONFIG_PATH)
        roles = org.list_roles()
        assert len(roles) == 9

    def test_get_role(self):
        org = DevOrganization.from_config(CONFIG_PATH)
        role = org.get_role("architect")
        assert role.title == "Software Architect"

    def test_invoke_role(self):
        org = DevOrganization.from_config(CONFIG_PATH)
        prompt = org.invoke_role("architect", "design_system", {
            "requirements": "Build a REST API",
        })
        assert "Software Architect" in prompt or "Design" in prompt
        assert "My Project" in prompt

    def test_list_workflows(self):
        org = DevOrganization.from_config(CONFIG_PATH)
        wfs = org.list_workflows()
        assert "feature_development" in wfs

    def test_plan_workflow(self):
        org = DevOrganization.from_config(CONFIG_PATH)
        plan = org.plan_workflow("feature_development")
        assert "Phase 1" in plan
        assert "Product Manager" in plan

    def test_get_role_summary(self):
        org = DevOrganization.from_config(CONFIG_PATH)
        summary = org.get_role_summary("tester")
        assert "QA Engineer" in summary
        assert "Skills" in summary

    def test_get_org_chart(self):
        org = DevOrganization.from_config(CONFIG_PATH)
        chart = org.get_org_chart()
        assert "LLM Dev Organization" in chart
        assert "Software Architect" in chart
        assert "Frontend Developer" in chart

    def test_create_executor(self):
        org = DevOrganization.from_config(CONFIG_PATH)
        executor = org.create_executor()
        assert executor is not None
        assert executor.context.project_name == "My Project"
