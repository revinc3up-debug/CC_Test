"""Tests for the iteration engine."""

import pytest
from pathlib import Path

from framework.adapter import LLMAdapter, LLMResponse
from framework.context import ProjectContext
from framework.role import RoleLoader
from framework.iteration import IterationEngine, IterationResult


ROLES_DIR = str(Path(__file__).parent.parent / "roles")


class SequenceAdapter(LLMAdapter):
    """Adapter that returns a sequence of predefined responses."""

    def __init__(self, responses: list[str]):
        self._responses = responses
        self._call_count = 0

    def send(self, prompt: str, system_prompt: str = "", **kwargs) -> LLMResponse:
        idx = min(self._call_count, len(self._responses) - 1)
        content = self._responses[idx]
        self._call_count += 1
        return LLMResponse(content=content, model="test")

    def name(self) -> str:
        return "test-sequence"


class TestReviewLoop:
    def _make_engine(self, responses: list[str]):
        adapter = SequenceAdapter(responses)
        role_loader = RoleLoader(ROLES_DIR)
        context = ProjectContext(project_name="Test")
        return IterationEngine(adapter, role_loader, context)

    def test_converges_on_approval(self):
        engine = self._make_engine([
            "Initial design output",     # produce
            "Looks good. APPROVED.",      # review → approve
        ])
        result = engine.review_loop(
            producer_role="architect",
            producer_skill="design_system",
            reviewer_role="architect",
            reviewer_skill="review_architecture",
            initial_context={"requirements": "Build something"},
            max_iterations=3,
        )
        assert result.converged
        assert result.total_iterations == 1
        assert len(result.steps) == 2

    def test_revises_when_not_approved(self):
        engine = self._make_engine([
            "Initial design",            # produce iter 1
            "Needs work. Fix X.",        # review iter 1 → revise
            "Revised design",            # produce iter 2
            "Better. APPROVED.",         # review iter 2 → approve
        ])
        result = engine.review_loop(
            producer_role="architect",
            producer_skill="design_system",
            reviewer_role="architect",
            reviewer_skill="review_architecture",
            initial_context={"requirements": "Build something"},
            max_iterations=3,
        )
        assert result.converged
        assert result.total_iterations == 2

    def test_stops_at_max_iterations(self):
        engine = self._make_engine([
            "Design v1", "Needs work",
            "Design v2", "Still needs work",
        ])
        result = engine.review_loop(
            producer_role="architect",
            producer_skill="design_system",
            reviewer_role="architect",
            reviewer_skill="review_architecture",
            initial_context={"requirements": "x"},
            max_iterations=2,
        )
        assert not result.converged
        assert result.total_iterations == 2
        assert result.final_output == "Design v2"

    def test_progress_callback_called(self):
        engine = self._make_engine(["Design", "APPROVED"])
        calls = []
        engine.review_loop(
            producer_role="architect",
            producer_skill="design_system",
            reviewer_role="architect",
            reviewer_skill="review_architecture",
            initial_context={"requirements": "x"},
            on_iteration=lambda i, p: calls.append((i, p)),
        )
        assert len(calls) >= 2


class TestResearchLoop:
    def _make_engine(self, responses: list[str]):
        adapter = SequenceAdapter(responses)
        role_loader = RoleLoader(ROLES_DIR)
        context = ProjectContext(project_name="Test")
        return IterationEngine(adapter, role_loader, context)

    def test_converges_on_complete(self):
        engine = self._make_engine([
            "Finding: PostgreSQL is good for this.",  # research
            "Synthesis complete. RESEARCH COMPLETE",  # synthesize → done
        ])
        result = engine.research_loop(
            research_role="product_manager",
            research_skill="research_topic",
            synthesis_role="product_manager",
            synthesis_skill="research_topic",
            question="Best database?",
            max_depth=3,
        )
        assert result.converged
        assert result.total_iterations == 1

    def test_deepens_with_gaps(self):
        engine = self._make_engine([
            "Initial research",
            "Synthesis with gaps.\n## GAPS\n- What about scaling?\n",
            "Scaling research",
            "Full synthesis. RESEARCH COMPLETE",
        ])
        result = engine.research_loop(
            research_role="product_manager",
            research_skill="research_topic",
            synthesis_role="product_manager",
            synthesis_skill="research_topic",
            question="Best database?",
            max_depth=3,
        )
        assert result.converged
        assert result.total_iterations == 2


class TestSchemeIteration:
    def _make_engine(self, responses: list[str]):
        adapter = SequenceAdapter(responses)
        role_loader = RoleLoader(ROLES_DIR)
        context = ProjectContext(project_name="Test")
        return IterationEngine(adapter, role_loader, context)

    def test_converges_when_all_approve(self):
        engine = self._make_engine([
            "Architecture design v1",     # designer
            "APPROVED. Looks solid.",     # critic 1 (architect)
            "APPROVED. Well designed.",   # critic 2 (architect again)
        ])
        result = engine.scheme_iteration(
            designer_role="architect",
            designer_skill="design_system",
            critic_roles=["architect"],
            critic_skill="review_architecture",
            requirements={"requirements": "Build X"},
        )
        assert result.converged
        assert result.total_iterations == 1

    def test_iterates_when_critics_disagree(self):
        engine = self._make_engine([
            "Design v1",                  # designer iter 1
            "Needs security fixes",       # critic 1 → revise
            "Design v2 with security",    # designer iter 2
            "APPROVED",                   # critic 1 → approve
        ])
        result = engine.scheme_iteration(
            designer_role="architect",
            designer_skill="design_system",
            critic_roles=["architect"],
            critic_skill="review_architecture",
            requirements={"requirements": "Build X"},
            max_iterations=3,
        )
        assert result.converged
        assert result.total_iterations == 2


class TestIterationResult:
    def test_summary_format(self):
        result = IterationResult(loop_type="review", total_iterations=2, converged=True)
        summary = result.summary()
        assert "Converged" in summary
        assert "review" in summary

    def test_summary_not_converged(self):
        result = IterationResult(loop_type="scheme", total_iterations=3, converged=False)
        summary = result.summary()
        assert "Max iterations" in summary
