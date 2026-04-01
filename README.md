# LLM Dev Organization

A multi-role LLM-powered development organization framework. Bring a full software team — Product Manager, Architect, Frontend/Backend Developers, Designer, Tester, DevOps, Code Reviewer, and Technical Writer — to any project through structured prompts, skills, and workflows.

## Quick Start

```bash
pip install pyyaml

# List all roles in your organization
python cli.py roles

# See the full org chart
python cli.py org

# View a workflow execution plan
python cli.py plan feature_development

# Generate a prompt for a specific role + skill
python cli.py invoke product_manager analyze_requirements \
  --context requirements_input="Build a user authentication system with OAuth"
```

## Architecture

```
├── framework/              # Core engine
│   ├── engine.py           # Main entry point (DevOrganization class)
│   ├── role.py             # Role definition and loading
│   ├── context.py          # Shared project context and artifacts
│   └── workflow.py         # Workflow orchestration and execution
├── roles/                  # Role definitions (9 roles)
│   ├── product_manager/    # Requirements, PRDs, user stories
│   ├── architect/          # System design, APIs, databases
│   ├── frontend_developer/ # UI components, pages, performance
│   ├── backend_developer/  # APIs, services, data layers
│   ├── ui_ux_designer/     # Wireframes, design systems, user flows
│   ├── tester/             # Test plans, test cases, bug reports
│   ├── devops/             # CI/CD, infrastructure, monitoring
│   ├── code_reviewer/      # Code review, security review
│   └── technical_writer/   # API docs, user guides, changelogs
├── workflows/              # Workflow templates (5 workflows)
│   ├── feature_development.yaml  # Full feature lifecycle (18 steps)
│   ├── bug_fix.yaml              # Bug diagnosis to fix (6 steps)
│   ├── code_review.yaml          # Multi-perspective review (4 steps)
│   ├── new_project_setup.yaml    # Project initialization (12 steps)
│   └── release.yaml              # Release preparation (5 steps)
├── config.yaml             # Project configuration
├── cli.py                  # Command-line interface
└── examples/               # Example project configurations
```

## Roles

| Role | Skills | Focus |
|------|--------|-------|
| **Product Manager** | analyze_requirements, write_prd, write_user_stories, prioritize_backlog | What to build and why |
| **Architect** | design_system, design_api, design_database, review_architecture, define_tech_stack | How to structure it |
| **Frontend Developer** | implement_component, implement_page, review_frontend, optimize_performance | User interface |
| **Backend Developer** | implement_api, implement_service, implement_data_layer, review_backend, debug_issue | Server-side logic |
| **UI/UX Designer** | design_wireframe, create_design_system, design_user_flow, review_ui_implementation | User experience |
| **QA Tester** | create_test_plan, design_test_cases, review_test_coverage, write_test_code, report_bug | Quality assurance |
| **DevOps** | design_cicd, setup_infrastructure, setup_monitoring, optimize_deployment, incident_response | Infrastructure & delivery |
| **Code Reviewer** | review_pull_request, review_security, suggest_refactoring | Code quality |
| **Technical Writer** | write_api_docs, write_user_guide, write_architecture_doc, write_changelog | Documentation |

Each role includes:
- **System prompt** — Defines the role's identity, principles, and communication style
- **Skill prompts** — Task-specific prompt templates with context variable injection
- **Standards** — Quality standards and guidelines the role follows

## Workflows

Workflows chain role+skill invocations with dependency resolution:

```bash
# See the phased execution plan
python cli.py plan feature_development
```

The feature development workflow resolves into 10 phases, automatically parallelizing independent work (e.g., UI design and system architecture happen concurrently after user stories are defined).

## Usage in Your Project

### 1. Configure for your project

Copy `config.yaml` and customize the project section:

```yaml
project:
  name: "Your Project"
  description: "What your project does"
  tech_stack:
    frontend: [React, TypeScript]
    backend: [Python, FastAPI]
  constraints:
    - "Must support 10k concurrent users"
```

### 2. Use roles directly

```python
from framework.engine import DevOrganization

org = DevOrganization.from_config("config.yaml")

# Generate a prompt for the architect to design your system
prompt = org.invoke_role("architect", "design_system", {
    "requirements": "Build a real-time chat application..."
})

# Send this prompt to any LLM (Claude, GPT, etc.)
response = your_llm_client.send(prompt)
```

### 3. Use workflows for multi-step processes

```python
org = DevOrganization.from_config("config.yaml")
workflow = org.load_workflow("feature_development")
executor = org.create_executor()

# Get the execution plan
plan = executor.resolve_execution_order(workflow)

# Execute each phase
for phase in plan:
    for step in phase:
        prompt = executor.build_step_prompt(step, workflow)
        response = your_llm_client.send(prompt)
        executor.record_step_result(step, response)
```

### 4. Extend with custom roles

Create a new directory in `roles/` with:
- `role.yaml` — Role definition, skills, collaborators
- `prompts/system.md` — System prompt
- `prompts/<skill>.md` — Skill-specific prompt templates
- `standards.md` — Quality standards

## Design Principles

- **LLM-agnostic** — Generates prompts, doesn't call LLMs. Use with any provider.
- **Role-based expertise** — Each role has deep, specialized knowledge and standards.
- **Workflow orchestration** — Automatic dependency resolution and parallel execution planning.
- **Artifact passing** — Outputs from one role feed into inputs for the next.
- **Project-aware** — All prompts include project context, tech stack, and constraints.
- **Extensible** — Add roles, skills, and workflows via YAML + Markdown.

## Requirements

- Python 3.10+
- PyYAML
