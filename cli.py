#!/usr/bin/env python3
"""
CLI for the LLM Dev Organization framework.

Usage:
    python cli.py roles                          # List all roles
    python cli.py role <role_id>                 # Show role details
    python cli.py workflows                      # List all workflows
    python cli.py plan <workflow_id>             # Show workflow execution plan
    python cli.py invoke <role_id> <skill>       # Build a prompt for a role+skill
    python cli.py org                            # Show the full org chart
"""

import argparse
import sys
import json
import shutil
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

from framework.engine import DevOrganization
from framework.validation import validate_all
from framework.role import RoleLoader
from framework.workflow import WorkflowLoader


def get_org(config_path: str = "config.yaml") -> DevOrganization:
    """Load the organization from config."""
    config = Path(config_path)
    if not config.exists():
        print(f"Error: Config file not found: {config_path}")
        print("Run from the project root or specify --config path/to/config.yaml")
        sys.exit(1)
    return DevOrganization.from_config(str(config))


def cmd_roles(args):
    """List all available roles."""
    org = get_org(args.config)
    roles = org.list_roles()
    print(f"Available Roles ({len(roles)}):\n")
    for role_id in sorted(roles):
        role = org.get_role(role_id)
        skills = ", ".join(s.name for s in role.skills)
        print(f"  {role_id:<25} {role.title}")
        print(f"  {'':25} Skills: {skills}\n")


def cmd_role(args):
    """Show details for a specific role."""
    org = get_org(args.config)
    print(org.get_role_summary(args.role_id))


def cmd_workflows(args):
    """List all available workflows."""
    org = get_org(args.config)
    workflows = org.list_workflows()
    print(f"Available Workflows ({len(workflows)}):\n")
    for wf_id in sorted(workflows):
        wf = org.load_workflow(wf_id)
        print(f"  {wf_id:<25} {wf.name}")
        print(f"  {'':25} {wf.description.strip()[:80]}")
        print(f"  {'':25} Steps: {len(wf.steps)}\n")


def cmd_plan(args):
    """Show the execution plan for a workflow."""
    org = get_org(args.config)
    print(org.plan_workflow(args.workflow_id))


def cmd_invoke(args):
    """Build and display a prompt for a role+skill invocation."""
    org = get_org(args.config)

    # Parse context from --context key=value pairs
    context = {}
    if args.context:
        for item in args.context:
            key, _, value = item.partition("=")
            context[key] = value

    prompt = org.invoke_role(args.role_id, args.skill, context)

    if args.json:
        print(json.dumps({"role": args.role_id, "skill": args.skill, "prompt": prompt}))
    else:
        print(prompt)


def cmd_org(args):
    """Show the full organization chart."""
    org = get_org(args.config)
    print(org.get_org_chart())


def cmd_validate(args):
    """Validate all role and workflow configurations."""
    org = get_org(args.config)
    result = validate_all(org.roles, org.workflows)
    print(result)
    if not result.is_valid:
        sys.exit(1)


def cmd_init(args):
    """Scaffold a new project with the framework."""
    target = Path(args.directory)
    framework_root = Path(__file__).parent

    if target.exists() and any(target.iterdir()):
        print(f"Error: Directory '{target}' is not empty.")
        print("Use an empty directory or a new path.")
        sys.exit(1)

    target.mkdir(parents=True, exist_ok=True)

    # Copy framework essentials
    dirs_to_copy = ["framework", "roles", "workflows"]
    for dirname in dirs_to_copy:
        src = framework_root / dirname
        dst = target / dirname
        if src.exists():
            shutil.copytree(src, dst, ignore=shutil.ignore_patterns("__pycache__"))
            print(f"  Copied {dirname}/")

    # Copy files
    files_to_copy = ["cli.py", "requirements.txt", ".gitignore"]
    for filename in files_to_copy:
        src = framework_root / filename
        if src.exists():
            shutil.copy2(src, target / filename)
            print(f"  Copied {filename}")

    # Generate project config with user's project name
    project_name = args.name or target.name
    config_content = f"""# LLM Dev Organization - Project Configuration

roles_dir: roles
workflows_dir: workflows

project:
  name: "{project_name}"
  description: "TODO: Describe your project here."
  tech_stack:
    frontend: []
    backend: []
    infrastructure: []
  constraints: []
"""
    (target / "config.yaml").write_text(config_content)
    print(f"  Created config.yaml")

    # Generate CLAUDE.md
    src_claude = framework_root / "CLAUDE.md"
    if src_claude.exists():
        shutil.copy2(src_claude, target / "CLAUDE.md")
        print(f"  Copied CLAUDE.md")

    print(f"\nProject '{project_name}' initialized at: {target}")
    print(f"\nNext steps:")
    print(f"  1. cd {target}")
    print(f"  2. Edit config.yaml with your project details")
    print(f"  3. python cli.py roles          # See your team")
    print(f"  4. python cli.py plan feature_development  # Plan a feature")


def main():
    parser = argparse.ArgumentParser(
        description="LLM Dev Organization - Multi-role development framework",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python cli.py roles                              # List all roles
  python cli.py role architect                     # Show architect details
  python cli.py workflows                          # List all workflows
  python cli.py plan feature_development           # Show feature dev plan
  python cli.py invoke architect design_system \\
    --context requirements="Build a todo app"      # Generate a prompt
  python cli.py org                                # Full org chart
        """,
    )
    parser.add_argument(
        "--config", default="config.yaml", help="Path to config file (default: config.yaml)"
    )

    subparsers = parser.add_subparsers(dest="command", help="Command to run")

    # roles
    subparsers.add_parser("roles", help="List all available roles")

    # role <id>
    p_role = subparsers.add_parser("role", help="Show role details")
    p_role.add_argument("role_id", help="Role ID (e.g., architect, tester)")

    # workflows
    subparsers.add_parser("workflows", help="List all available workflows")

    # plan <id>
    p_plan = subparsers.add_parser("plan", help="Show workflow execution plan")
    p_plan.add_argument("workflow_id", help="Workflow ID (e.g., feature_development)")

    # invoke <role> <skill>
    p_invoke = subparsers.add_parser("invoke", help="Build a prompt for a role+skill")
    p_invoke.add_argument("role_id", help="Role ID")
    p_invoke.add_argument("skill", help="Skill name")
    p_invoke.add_argument("--context", nargs="*", help="Context variables as key=value")
    p_invoke.add_argument("--json", action="store_true", help="Output as JSON")

    # org
    subparsers.add_parser("org", help="Show organization chart")

    # validate
    subparsers.add_parser("validate", help="Validate all role and workflow configs")

    # init
    p_init = subparsers.add_parser("init", help="Scaffold a new project with the framework")
    p_init.add_argument("directory", help="Target directory for the new project")
    p_init.add_argument("--name", help="Project name (defaults to directory name)")

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        sys.exit(0)

    commands = {
        "roles": cmd_roles,
        "role": cmd_role,
        "workflows": cmd_workflows,
        "plan": cmd_plan,
        "invoke": cmd_invoke,
        "org": cmd_org,
        "validate": cmd_validate,
        "init": cmd_init,
    }

    commands[args.command](args)


if __name__ == "__main__":
    main()
