# CLAUDE.md - Project Intelligence for Claude Code

## Project Overview

This is the **LLM Dev Organization** framework — a multi-role, LLM-powered
development team that orchestrates specialized AI agents (Product Manager,
Architect, Developers, Tester, DevOps, etc.) across structured workflows.
Apply it to any software project to produce higher-quality outputs through
role-based prompt composition, dependency-aware execution, and iterative
refinement.

## Quick Reference

### Running the CLI
```bash
python cli.py roles                    # List all 9 roles
python cli.py role <role_id>           # Role details (skills, responsibilities)
python cli.py workflows                # List all 5 workflows
python cli.py plan <workflow_id>       # Show phased execution plan
python cli.py invoke <role> <skill>    # Generate a prompt (no LLM call)
python cli.py org                      # Show full organization chart
python cli.py validate                 # Validate all role/workflow configs
python cli.py init <dir>               # Scaffold a new project

# Execution (requires LLM adapter)
python cli.py run <workflow_id> --provider anthropic --var key=value
python cli.py run <workflow_id> --provider file --output ./out  # Save prompts to files
python cli.py review --file code.py --type code                 # Multi-perspective review
python cli.py iterate review --producer-role backend_developer  # Iterative refinement
```

### Running Tests
```bash
python -m pytest tests/ -v
```

All tests are in `tests/` and cover role loading, workflow resolution, context
management, validation, adapters, engine, runner, iteration, and review modules.

## Architecture

```
CC_Test/
├── framework/           # Core Python engine
│   ├── __init__.py      # Package marker (version 0.1.0)
│   ├── role.py          # Role/RoleSkill dataclasses, RoleLoader (YAML + Markdown)
│   ├── workflow.py      # Workflow/WorkflowStep dataclasses, WorkflowExecutor (topological sort)
│   ├── context.py       # ProjectContext and Artifact dataclasses (shared state)
│   ├── validation.py    # Config validation with structured error reporting
│   ├── adapter.py       # LLM adapters: Anthropic, OpenAI, File (pluggable)
│   ├── engine.py        # DevOrganization facade (wires roles, workflows, context)
│   ├── runner.py        # WorkflowRunner — end-to-end execution with LLM adapter
│   ├── iteration.py     # IterationEngine — review_loop, research_loop, scheme_iteration
│   └── review.py        # AutoReviewer — multi-perspective review pipeline
├── roles/               # 9 role definitions
│   ├── product_manager/ # PRDs, user stories, requirements analysis
│   ├── architect/       # System design, API contracts, database schemas
│   ├── frontend_developer/
│   ├── backend_developer/
│   ├── ui_ux_designer/
│   ├── tester/
│   ├── devops/
│   ├── code_reviewer/
│   └── technical_writer/
├── workflows/           # 5 workflow templates
│   ├── feature_development.yaml   # Full feature lifecycle (18 steps)
│   ├── bug_fix.yaml
│   ├── code_review.yaml
│   ├── new_project_setup.yaml
│   └── release.yaml
├── examples/            # Example project configs
│   └── todo_app_project.yaml
├── cli.py               # CLI entry point (argparse subcommands)
├── config.yaml          # Default project configuration
├── requirements.txt     # Only PyYAML>=6.0
└── tests/               # Unit tests (pytest)
```

### Module Relationships

```
cli.py → engine.DevOrganization → role.RoleLoader + workflow.WorkflowLoader + context.ProjectContext
                                → workflow.WorkflowExecutor (prompt building, dependency resolution)
                                → runner.WorkflowRunner + adapter.LLMAdapter (execution)
                                → iteration.IterationEngine (refinement loops)
                                → review.AutoReviewer (multi-perspective review)
                                → validation.validate_all (config checking)
```

### Data Flow

1. **Roles** are loaded from `roles/<id>/role.yaml` + `prompts/*.md` + `standards.md`
2. **Workflows** define step sequences with `depends_on` and `input_mapping`
3. **WorkflowExecutor** resolves execution order via topological sort into parallelizable layers
4. **Prompt composition**: system_prompt + standards + skill_template (with `{{variable}}` interpolation) + output_format
5. **Artifacts** (outputs) are stored in `ProjectContext` and referenced by downstream steps via `input_mapping` (`"step:<id>"` or `"artifact:<type>"`)
6. **LLM Adapter** sends the prompt and returns `LLMResponse` (content, usage, model)

## Role System

Each role directory contains:
- `role.yaml` — metadata: name, title, responsibilities, skills, tools, collaborations, input/output artifacts
- `prompts/system.md` — base system prompt for the role
- `prompts/<skill_name>.md` — skill-specific prompt templates with `{{placeholder}}` variables
- `standards.md` — quality standards injected into every prompt

### Available Roles
| Role ID | Title | Key Skills |
|---------|-------|------------|
| `product_manager` | Product Manager | analyze_requirements, write_prd, write_user_stories, prioritize_backlog |
| `architect` | Software Architect | design_system, design_api, design_database, review_architecture, define_tech_stack |
| `frontend_developer` | Frontend Developer | implement_component, implement_page, optimize_performance, review_frontend |
| `backend_developer` | Backend Developer | implement_api, implement_service, implement_data_layer, debug_issue, review_backend |
| `ui_ux_designer` | UI/UX Designer | design_wireframe, design_user_flow, create_design_system, review_ui_implementation |
| `tester` | QA Engineer | create_test_plan, design_test_cases, write_test_code, review_test_coverage, report_bug |
| `devops` | DevOps Engineer | setup_infrastructure, design_cicd, setup_monitoring, optimize_deployment, incident_response |
| `code_reviewer` | Code Reviewer | review_pull_request, review_security, suggest_refactoring |
| `technical_writer` | Technical Writer | write_api_docs, write_user_guide, write_architecture_doc, write_changelog |

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

## Key Design Decisions

- **LLM-agnostic**: Framework generates prompts; LLM calls are pluggable via adapters (Anthropic, OpenAI, File).
- **YAML + Markdown**: Roles and workflows defined declaratively, not in code. New roles/workflows require zero framework changes.
- **Artifact passing**: Outputs from one role feed into the next role's context via `ProjectContext`.
- **Parallel execution**: Topological sort groups independent steps into layers that can run concurrently.
- **Convergence detection**: Iteration engines use keyword matching ("APPROVED", "RESEARCH COMPLETE") for loop termination.
- **Minimal dependencies**: Only PyYAML is required. LLM SDKs (anthropic, openai) are optional lazy imports.

## Iteration Patterns

The `IterationEngine` supports three refinement patterns:

1. **Review Loop** — Produce → Review → Revise (converges on "APPROVED")
2. **Research Loop** — Research → Synthesize → Deepen (converges on "RESEARCH COMPLETE", parses `## GAPS` section)
3. **Scheme Iteration** — Design → Multi-Critic Review → Refine (converges when ALL critics say "APPROVED")

## Coding Standards for This Project

- Python 3.10+ with type hints on all public functions.
- Dataclasses for all data structures (`Role`, `Workflow`, `Artifact`, `ProjectContext`, etc.).
- No external dependencies beyond PyYAML (keep it lightweight).
- Adapter pattern for LLM providers — add new adapters in `framework/adapter.py`.
- Tests alongside changes — run `pytest tests/ -v` to verify.
- CLI commands follow the `cmd_<name>(args)` pattern in `cli.py`.
- Validation runs before execution — use `validate_all()` to catch config errors early.
- Template variables use `{{double_braces}}` syntax in prompt markdown files.
