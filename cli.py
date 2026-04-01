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
from framework.adapter import create_adapter
from framework.runner import WorkflowRunner
from framework.review import AutoReviewer
from framework.iteration import IterationEngine


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


def _get_adapter(args):
    """Create an LLM adapter from CLI args."""
    provider = getattr(args, "provider", "file")
    kwargs = {}
    if provider == "file":
        output_dir = getattr(args, "output", None) or ".output"
        kwargs["output_dir"] = output_dir
    if hasattr(args, "model") and args.model:
        kwargs["model"] = args.model
    return create_adapter(provider, **kwargs)


def _progress_callback(message: str, step, current: int, total: int):
    """Print workflow progress."""
    pct = int(current / total * 100)
    print(f"  [{current}/{total}] ({pct}%) {message}")


def cmd_run(args):
    """Execute a workflow end-to-end with an LLM adapter."""
    org = get_org(args.config)
    adapter = _get_adapter(args)
    workflow = org.load_workflow(args.workflow_id)

    # Set workflow variables from CLI
    if args.var:
        for item in args.var:
            key, _, value = item.partition("=")
            workflow.variables[key] = value

    runner = WorkflowRunner(adapter, org.roles, org.context)

    print(f"Running workflow: {workflow.name}")
    print(f"Provider: {adapter.name()}")
    print(f"Steps: {len(workflow.steps)}\n")

    result = runner.run(
        workflow,
        on_progress=_progress_callback,
        save_to=args.output,
    )

    print(f"\n{result.summary()}")

    if args.output:
        # Save run summary
        summary_path = Path(args.output) / "_run_summary.md"
        summary_path.write_text(result.summary())
        print(f"\nArtifacts saved to: {args.output}/")


def cmd_review(args):
    """Run automated multi-perspective review."""
    org = get_org(args.config)
    adapter = _get_adapter(args)

    # Read content from file or stdin
    if args.file:
        content = Path(args.file).read_text()
    else:
        print("Reading from stdin (Ctrl+D to end)...")
        content = sys.stdin.read()

    reviewer = AutoReviewer(adapter, org.roles, org.context)

    print(f"Running review ({args.type})...")
    print(f"Provider: {adapter.name()}")

    if args.type == "architecture":
        report = reviewer.review_architecture(content)
    elif args.type == "frontend":
        report = reviewer.review_code(content)
    elif args.type == "backend":
        report = reviewer.review(content, content_type="backend")
    elif args.type == "prd":
        report = reviewer.review_prd(content)
    else:
        report = reviewer.review_code(content)

    print(report.format_report())

    if args.output:
        Path(args.output).write_text(report.format_report())
        print(f"\nReport saved to: {args.output}")


def cmd_iterate(args):
    """Run an iterative refinement loop."""
    org = get_org(args.config)
    adapter = _get_adapter(args)

    engine = IterationEngine(adapter, org.roles, org.context)

    def on_iteration(i: int, phase: str):
        print(f"  [Iteration {i}] {phase}")

    context = {}
    if args.var:
        for item in args.var:
            key, _, value = item.partition("=")
            context[key] = value

    if args.mode == "review":
        print(f"Review loop: {args.producer} → {args.reviewer}")
        print(f"Max iterations: {args.max_iter}\n")

        producer_role, producer_skill = args.producer.split("/")
        reviewer_role, reviewer_skill = args.reviewer.split("/")

        result = engine.review_loop(
            producer_role=producer_role,
            producer_skill=producer_skill,
            reviewer_role=reviewer_role,
            reviewer_skill=reviewer_skill,
            initial_context=context,
            max_iterations=args.max_iter,
            on_iteration=on_iteration,
        )
    elif args.mode == "research":
        print(f"Research loop on: {context.get('question', 'N/A')}")
        print(f"Max depth: {args.max_iter}\n")

        result = engine.research_loop(
            research_role="product_manager",
            research_skill="research_topic",
            synthesis_role="product_manager",
            synthesis_skill="research_topic",
            question=context.get("question", ""),
            max_depth=args.max_iter,
            on_iteration=on_iteration,
        )
    elif args.mode == "scheme":
        print(f"Scheme iteration: {args.producer}")
        critics = args.critics.split(",") if args.critics else ["code_reviewer", "architect"]
        print(f"Critics: {', '.join(critics)}")
        print(f"Max iterations: {args.max_iter}\n")

        producer_role, producer_skill = args.producer.split("/")

        result = engine.scheme_iteration(
            designer_role=producer_role,
            designer_skill=producer_skill,
            critic_roles=critics,
            critic_skill="review_architecture",
            requirements=context,
            max_iterations=args.max_iter,
            on_iteration=on_iteration,
        )
    else:
        print(f"Unknown iteration mode: {args.mode}")
        sys.exit(1)

    print(f"\n{result.summary()}")

    if result.final_output and args.output:
        Path(args.output).write_text(result.final_output)
        print(f"\nFinal output saved to: {args.output}")
    elif result.final_output and not args.output:
        print(f"\n--- Final Output ---\n{result.final_output[:500]}...")


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

    # run
    p_run = subparsers.add_parser("run", help="Execute a workflow end-to-end")
    p_run.add_argument("workflow_id", help="Workflow to execute")
    p_run.add_argument("--provider", default="file", help="LLM provider: anthropic|openai|file (default: file)")
    p_run.add_argument("--model", help="Model override (e.g., claude-opus-4-20250514)")
    p_run.add_argument("--output", default=".output", help="Output directory (default: .output)")
    p_run.add_argument("--var", nargs="*", help="Workflow variables as key=value")

    # review
    p_review = subparsers.add_parser("review", help="Run automated multi-perspective review")
    p_review.add_argument("--file", help="File to review (reads stdin if omitted)")
    p_review.add_argument("--type", default="code", choices=["code", "frontend", "backend", "architecture", "prd"],
                           help="Content type (default: code)")
    p_review.add_argument("--provider", default="file", help="LLM provider (default: file)")
    p_review.add_argument("--model", help="Model override")
    p_review.add_argument("--output", help="Save report to file")

    # iterate
    p_iter = subparsers.add_parser("iterate", help="Run iterative refinement loops")
    p_iter.add_argument("mode", choices=["review", "research", "scheme"],
                         help="Iteration mode: review|research|scheme")
    p_iter.add_argument("--producer", help="Producer role/skill (e.g., architect/design_system)")
    p_iter.add_argument("--reviewer", help="Reviewer role/skill (e.g., code_reviewer/review_pull_request)")
    p_iter.add_argument("--critics", help="Comma-separated critic role IDs (for scheme mode)")
    p_iter.add_argument("--max-iter", type=int, default=3, help="Max iterations (default: 3)")
    p_iter.add_argument("--var", nargs="*", help="Context variables as key=value")
    p_iter.add_argument("--provider", default="file", help="LLM provider (default: file)")
    p_iter.add_argument("--model", help="Model override")
    p_iter.add_argument("--output", help="Save final output to file")

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
        "run": cmd_run,
        "review": cmd_review,
        "iterate": cmd_iterate,
    }

    commands[args.command](args)


if __name__ == "__main__":
    main()
