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
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

from framework.engine import DevOrganization


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
    }

    commands[args.command](args)


if __name__ == "__main__":
    main()
