"""
Iteration engine — feedback loops for review, refinement, and convergence.

Supports three iteration patterns:
1. Review Loop: produce → review → revise (until approved or max iterations)
2. Research Loop: question → investigate → synthesize → verify
3. Scheme Iteration: design → critique → refine (progressive improvement)
"""

from dataclasses import dataclass, field
from typing import Any, Callable

from .adapter import LLMAdapter, LLMResponse
from .context import ProjectContext
from .role import RoleLoader


@dataclass
class IterationStep:
    """A single iteration within a loop."""
    iteration: int
    role_id: str
    skill_name: str
    prompt: str
    response: str
    verdict: str = ""  # approve | revise | needs_research


@dataclass
class IterationResult:
    """Result of a complete iteration loop."""
    loop_type: str  # review | research | scheme
    steps: list[IterationStep] = field(default_factory=list)
    final_output: str = ""
    converged: bool = False
    total_iterations: int = 0

    def summary(self) -> str:
        status = "Converged" if self.converged else "Max iterations reached"
        lines = [
            f"# Iteration Result ({self.loop_type})",
            f"Status: {status}",
            f"Iterations: {self.total_iterations}",
            "",
        ]
        for step in self.steps:
            lines.append(f"  [{step.iteration}] {step.role_id}/{step.skill_name} → {step.verdict}")
        return "\n".join(lines)


class IterationEngine:
    """
    Engine for iterative refinement loops.

    Orchestrates produce → review → revise cycles across different roles
    until convergence criteria are met or max iterations are reached.
    """

    def __init__(
        self,
        adapter: LLMAdapter,
        role_loader: RoleLoader,
        context: ProjectContext,
    ):
        self.adapter = adapter
        self.role_loader = role_loader
        self.context = context

    def review_loop(
        self,
        producer_role: str,
        producer_skill: str,
        reviewer_role: str,
        reviewer_skill: str,
        initial_context: dict[str, str],
        max_iterations: int = 3,
        on_iteration: Callable[[int, str], None] | None = None,
    ) -> IterationResult:
        """
        Run a produce → review → revise loop.

        1. Producer creates initial output
        2. Reviewer evaluates and provides feedback
        3. If not approved, producer revises based on feedback
        4. Repeat until approved or max_iterations reached

        The reviewer's response must contain 'APPROVED' to stop the loop.
        """
        result = IterationResult(loop_type="review")
        current_context = dict(initial_context)
        current_output = ""

        for i in range(1, max_iterations + 1):
            result.total_iterations = i

            if on_iteration:
                on_iteration(i, "producing" if i == 1 else "revising")

            # Step 1: Produce (or revise)
            if i > 1:
                current_context["previous_output"] = current_output
                current_context["review_feedback"] = result.steps[-1].response
                produce_prompt = self._build_revision_prompt(
                    producer_role, producer_skill, current_context
                )
            else:
                produce_prompt = self._build_prompt(
                    producer_role, producer_skill, current_context
                )

            produce_response = self.adapter.send(produce_prompt)
            current_output = produce_response.content

            result.steps.append(IterationStep(
                iteration=i,
                role_id=producer_role,
                skill_name=producer_skill,
                prompt=produce_prompt,
                response=current_output,
                verdict="produced",
            ))

            if on_iteration:
                on_iteration(i, "reviewing")

            # Step 2: Review
            review_context = {
                **current_context,
                "content_to_review": current_output,
            }
            review_prompt = self._build_prompt(
                reviewer_role, reviewer_skill, review_context
            )
            review_response = self.adapter.send(review_prompt)

            # Determine verdict
            review_text = review_response.content
            verdict = "approve" if "APPROVED" in review_text.upper() else "revise"

            result.steps.append(IterationStep(
                iteration=i,
                role_id=reviewer_role,
                skill_name=reviewer_skill,
                prompt=review_prompt,
                response=review_text,
                verdict=verdict,
            ))

            if verdict == "approve":
                result.converged = True
                result.final_output = current_output
                return result

        # Max iterations reached — use the last output
        result.final_output = current_output
        return result

    def research_loop(
        self,
        research_role: str,
        research_skill: str,
        synthesis_role: str,
        synthesis_skill: str,
        question: str,
        sub_questions: list[str] | None = None,
        max_depth: int = 3,
        on_iteration: Callable[[int, str], None] | None = None,
    ) -> IterationResult:
        """
        Run a research → synthesize → deepen loop.

        1. Research role investigates the question
        2. Synthesis role consolidates findings and identifies gaps
        3. If gaps remain, research deepens on those areas
        4. Repeat until no gaps or max_depth reached
        """
        result = IterationResult(loop_type="research")
        all_findings: list[str] = []
        current_question = question
        remaining_questions = list(sub_questions or [])

        for i in range(1, max_depth + 1):
            result.total_iterations = i

            if on_iteration:
                on_iteration(i, f"researching: {current_question[:60]}")

            # Step 1: Research
            research_context = {
                "question": current_question,
                "previous_findings": "\n\n---\n\n".join(all_findings) if all_findings else "None yet.",
                "project_summary": self.context.to_summary(),
            }
            research_prompt = self._build_prompt(
                research_role, research_skill, research_context
            )
            research_response = self.adapter.send(research_prompt)
            all_findings.append(research_response.content)

            result.steps.append(IterationStep(
                iteration=i,
                role_id=research_role,
                skill_name=research_skill,
                prompt=research_prompt,
                response=research_response.content,
                verdict="researched",
            ))

            if on_iteration:
                on_iteration(i, "synthesizing")

            # Step 2: Synthesize and identify gaps
            synthesis_context = {
                "original_question": question,
                "all_findings": "\n\n---\n\n".join(all_findings),
                "project_summary": self.context.to_summary(),
                "instruction": (
                    "Synthesize all findings into a comprehensive answer. "
                    "If there are remaining gaps or unanswered questions, "
                    "list them under a '## GAPS' section. "
                    "If the research is complete, write 'RESEARCH COMPLETE' at the end."
                ),
            }
            synthesis_prompt = self._build_prompt(
                synthesis_role, synthesis_skill, synthesis_context
            )
            synthesis_response = self.adapter.send(synthesis_prompt)

            verdict = "complete" if "RESEARCH COMPLETE" in synthesis_response.content.upper() else "deepen"

            result.steps.append(IterationStep(
                iteration=i,
                role_id=synthesis_role,
                skill_name=synthesis_skill,
                prompt=synthesis_prompt,
                response=synthesis_response.content,
                verdict=verdict,
            ))

            if verdict == "complete":
                result.converged = True
                result.final_output = synthesis_response.content
                return result

            # Extract next question from gaps
            if remaining_questions:
                current_question = remaining_questions.pop(0)
            else:
                # Extract gap from synthesis response
                current_question = self._extract_gap(synthesis_response.content)
                if not current_question:
                    result.converged = True
                    result.final_output = synthesis_response.content
                    return result

        result.final_output = all_findings[-1] if all_findings else ""
        return result

    def scheme_iteration(
        self,
        designer_role: str,
        designer_skill: str,
        critic_roles: list[str],
        critic_skill: str,
        requirements: dict[str, str],
        max_iterations: int = 3,
        on_iteration: Callable[[int, str], None] | None = None,
    ) -> IterationResult:
        """
        Run a design → multi-perspective critique → refine loop.

        1. Designer creates initial design
        2. Multiple critic roles review from their perspectives
        3. Designer incorporates all feedback into refined design
        4. Repeat until all critics approve or max_iterations

        This is the core scheme iteration pattern — a single design
        gets progressively refined through diverse expert feedback.
        """
        result = IterationResult(loop_type="scheme")
        current_context = dict(requirements)
        current_design = ""

        for i in range(1, max_iterations + 1):
            result.total_iterations = i

            if on_iteration:
                on_iteration(i, "designing" if i == 1 else "refining")

            # Step 1: Design (or refine)
            if i > 1:
                current_context["previous_design"] = current_design
                current_context["consolidated_feedback"] = self._consolidate_feedback(
                    [s for s in result.steps if s.iteration == i - 1 and s.verdict != "designed"]
                )
                design_prompt = self._build_revision_prompt(
                    designer_role, designer_skill, current_context
                )
            else:
                design_prompt = self._build_prompt(
                    designer_role, designer_skill, current_context
                )

            design_response = self.adapter.send(design_prompt)
            current_design = design_response.content

            result.steps.append(IterationStep(
                iteration=i,
                role_id=designer_role,
                skill_name=designer_skill,
                prompt=design_prompt,
                response=current_design,
                verdict="designed",
            ))

            # Step 2: Multi-perspective critique
            all_approved = True
            for critic_role in critic_roles:
                if on_iteration:
                    on_iteration(i, f"critique by {critic_role}")

                critic_context = {
                    **current_context,
                    "proposal": current_design,
                    "content_to_review": current_design,
                    "code_changes": current_design,
                    "code": current_design,
                    "pr_description": requirements.get("requirements", ""),
                }
                critic_prompt = self._build_prompt(
                    critic_role, critic_skill, critic_context
                )
                critic_response = self.adapter.send(critic_prompt)

                verdict = "approve" if "APPROVED" in critic_response.content.upper() or "APPROVE" in critic_response.content.upper() else "revise"
                if verdict != "approve":
                    all_approved = False

                result.steps.append(IterationStep(
                    iteration=i,
                    role_id=critic_role,
                    skill_name=critic_skill,
                    prompt=critic_prompt,
                    response=critic_response.content,
                    verdict=verdict,
                ))

            if all_approved:
                result.converged = True
                result.final_output = current_design
                return result

        result.final_output = current_design
        return result

    # --- Internal helpers ---

    def _build_prompt(self, role_id: str, skill_name: str, context: dict) -> str:
        """Build a prompt from role + skill + context."""
        role = self.role_loader.load(role_id)
        merged = {
            "project_summary": self.context.to_summary(),
            **context,
        }
        return role.build_prompt(skill_name, merged)

    def _build_revision_prompt(self, role_id: str, skill_name: str, context: dict) -> str:
        """Build a revision prompt that includes previous output and feedback."""
        role = self.role_loader.load(role_id)

        revision_header = (
            "## Previous Output\n"
            f"{context.get('previous_output', context.get('previous_design', ''))}\n\n"
            "## Feedback to Address\n"
            f"{context.get('review_feedback', context.get('consolidated_feedback', ''))}\n\n"
            "## Revision Instructions\n"
            "Carefully review the feedback above. Revise your previous output to address "
            "all concerns while preserving what was already good. Produce a complete, "
            "improved version — not a diff.\n"
        )

        merged = {
            "project_summary": self.context.to_summary(),
            **context,
        }
        base_prompt = role.build_prompt(skill_name, merged)
        return f"{base_prompt}\n\n{revision_header}"

    def _consolidate_feedback(self, critic_steps: list[IterationStep]) -> str:
        """Merge feedback from multiple critics into a consolidated summary."""
        if not critic_steps:
            return "No feedback provided."
        parts = []
        for step in critic_steps:
            role = self.role_loader.load(step.role_id)
            parts.append(f"### Feedback from {role.title}\n{step.response}")
        return "\n\n---\n\n".join(parts)

    def _extract_gap(self, synthesis_text: str) -> str:
        """Extract the first gap/question from a synthesis response."""
        lines = synthesis_text.split("\n")
        in_gaps = False
        for line in lines:
            if "## GAPS" in line.upper() or "## GAP" in line.upper():
                in_gaps = True
                continue
            if in_gaps and line.strip().startswith(("-", "*", "1")):
                # Return the first gap as the next question
                return line.strip().lstrip("-*0123456789. ")
            if in_gaps and line.startswith("##"):
                break  # Next section
        return ""
