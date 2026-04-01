"""
Role definition and loading system.

Each role is defined by a YAML config + markdown prompt files.
Roles encapsulate: identity, skills, standards, tools, and prompt templates.
"""

import os
import yaml
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional


@dataclass
class RoleSkill:
    """A specific skill/capability a role possesses."""
    name: str
    description: str
    prompt_template: str = ""
    output_format: str = ""


@dataclass
class Role:
    """Represents a specialized role in the dev organization."""
    id: str
    name: str
    title: str
    description: str
    system_prompt: str
    responsibilities: list[str] = field(default_factory=list)
    skills: list[RoleSkill] = field(default_factory=list)
    standards: str = ""
    tools: list[str] = field(default_factory=list)
    collaborates_with: list[str] = field(default_factory=list)
    input_artifacts: list[str] = field(default_factory=list)
    output_artifacts: list[str] = field(default_factory=list)

    def get_skill(self, skill_name: str) -> Optional[RoleSkill]:
        """Look up a skill by name."""
        for skill in self.skills:
            if skill.name == skill_name:
                return skill
        return None

    def build_prompt(self, skill_name: str, context: dict) -> str:
        """Build a complete prompt for a given skill with context."""
        skill = self.get_skill(skill_name)
        if not skill:
            raise ValueError(f"Role '{self.id}' has no skill '{skill_name}'")

        prompt_parts = [self.system_prompt]

        if self.standards:
            prompt_parts.append(f"\n## Standards & Guidelines\n{self.standards}")

        if skill.prompt_template:
            rendered = skill.prompt_template
            for key, value in context.items():
                rendered = rendered.replace(f"{{{{{key}}}}}", str(value))
            prompt_parts.append(f"\n## Task\n{rendered}")

        if skill.output_format:
            prompt_parts.append(f"\n## Expected Output Format\n{skill.output_format}")

        return "\n".join(prompt_parts)


class RoleLoader:
    """Loads role definitions from the roles/ directory."""

    def __init__(self, roles_dir: str):
        self.roles_dir = Path(roles_dir)
        self._cache: dict[str, Role] = {}

    def list_roles(self) -> list[str]:
        """List all available role IDs."""
        return [
            d.name for d in self.roles_dir.iterdir()
            if d.is_dir() and (d / "role.yaml").exists()
        ]

    def load(self, role_id: str) -> Role:
        """Load a role by its directory name."""
        if role_id in self._cache:
            return self._cache[role_id]

        role_dir = self.roles_dir / role_id
        config_path = role_dir / "role.yaml"

        if not config_path.exists():
            raise FileNotFoundError(f"Role config not found: {config_path}")

        with open(config_path) as f:
            config = yaml.safe_load(f)

        # Load system prompt from markdown file
        system_prompt = self._load_prompt(role_dir / "prompts" / "system.md")

        # Load standards
        standards = ""
        standards_path = role_dir / "standards.md"
        if standards_path.exists():
            with open(standards_path) as f:
                standards = f.read()

        # Load skills with their prompt templates
        skills = []
        for skill_def in config.get("skills", []):
            prompt_template = ""
            prompt_file = skill_def.get("prompt_file")
            if prompt_file:
                prompt_template = self._load_prompt(role_dir / "prompts" / prompt_file)

            skills.append(RoleSkill(
                name=skill_def["name"],
                description=skill_def.get("description", ""),
                prompt_template=prompt_template,
                output_format=skill_def.get("output_format", ""),
            ))

        role = Role(
            id=role_id,
            name=config["name"],
            title=config.get("title", config["name"]),
            description=config.get("description", ""),
            system_prompt=system_prompt,
            responsibilities=config.get("responsibilities", []),
            skills=skills,
            standards=standards,
            tools=config.get("tools", []),
            collaborates_with=config.get("collaborates_with", []),
            input_artifacts=config.get("input_artifacts", []),
            output_artifacts=config.get("output_artifacts", []),
        )

        self._cache[role_id] = role
        return role

    def load_all(self) -> dict[str, Role]:
        """Load all available roles."""
        return {rid: self.load(rid) for rid in self.list_roles()}

    def _load_prompt(self, path: Path) -> str:
        """Load a markdown prompt file."""
        if path.exists():
            with open(path) as f:
                return f.read().strip()
        return ""
