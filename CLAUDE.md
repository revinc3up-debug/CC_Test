# CLAUDE.md - Project Intelligence for Claude Code

## Project Overview
This is the **LLM Dev Organization** framework — a multi-role, LLM-powered
development team that you can apply to any software project.

## How to Use This Framework in Claude Code

When working on ANY project that includes this framework, you should leverage
the role definitions and standards to produce higher-quality outputs.

### Activating a Role
Before performing a task, load the relevant role's system prompt and standards:

1. **Writing requirements?** → Read `roles/product_manager/prompts/system.md` and `roles/product_manager/standards.md`
2. **Designing architecture?** → Read `roles/architect/prompts/system.md` and `roles/architect/standards.md`
3. **Writing frontend code?** → Read `roles/frontend_developer/prompts/system.md` and `roles/frontend_developer/standards.md`
4. **Writing backend code?** → Read `roles/backend_developer/prompts/system.md` and `roles/backend_developer/standards.md`
5. **Designing UI?** → Read `roles/ui_ux_designer/prompts/system.md` and `roles/ui_ux_designer/standards.md`
6. **Writing tests?** → Read `roles/tester/prompts/system.md` and `roles/tester/standards.md`
7. **Setting up infra/CI?** → Read `roles/devops/prompts/system.md` and `roles/devops/standards.md`
8. **Reviewing code?** → Read `roles/code_reviewer/prompts/system.md` and `roles/code_reviewer/standards.md`
9. **Writing docs?** → Read `roles/technical_writer/prompts/system.md` and `roles/technical_writer/standards.md`

### Running the CLI
```bash
python cli.py roles                    # List all roles
python cli.py role <role_id>           # Role details
python cli.py workflows                # List workflows
python cli.py plan <workflow_id>       # Show execution plan
python cli.py invoke <role> <skill>    # Generate prompt
python cli.py validate                 # Validate all configs
python cli.py init <dir>               # Scaffold new project
```

### Running Tests
```bash
python -m pytest tests/ -v
```

## Architecture

- `framework/` — Core Python engine (role loader, workflow orchestrator, context, validation, LLM adapter)
- `roles/` — 9 role definitions, each with `role.yaml`, `prompts/`, and `standards.md`
- `workflows/` — 5 workflow templates (feature_development, bug_fix, code_review, new_project_setup, release)
- `cli.py` — Command-line interface
- `tests/` — Unit tests for the framework

## Key Design Decisions
- **LLM-agnostic**: Framework generates prompts; LLM calls are pluggable via adapters.
- **YAML + Markdown**: Roles and workflows defined declaratively, not in code.
- **Artifact passing**: Outputs from one role feed into the next role's context.
- **Parallel execution planning**: Workflow steps with independent dependencies run concurrently.

## Coding Standards for This Project
- Python 3.10+ with type hints on all public functions.
- Dataclasses for data structures.
- No external dependencies beyond PyYAML (keep it lightweight).
- Tests alongside changes — run `pytest tests/` to verify.
