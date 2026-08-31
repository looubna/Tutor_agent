"""The router diamond and the two planners."""

from __future__ import annotations

import json

import pytest
from pydantic import ValidationError

from zanoba_agent.agents.language_planner import language_lesson_planner
from zanoba_agent.agents.stem_planner import stem_lesson_planner
from zanoba_agent.schemas.lesson_plan import (
    LANGUAGE_PHASES, STEM_PHASES, LessonActivity, LessonPlan)
from zanoba_agent.schemas.objectives import LessonObjective
from zanoba_agent.workflows.preparation import preparation_workflow
from zanoba_agent.workflows.routing import route_by_domain


def _route(payload) -> str:
    # A route is carried on actions, not on the event itself.
    return route_by_domain(payload).actions.route


def test_a_language_subject_routes_to_the_language_branch():
    assert _route({"subject": "german"}) == "language"
    assert _route({"subject": "korean"}) == "language"


def test_a_stem_subject_routes_to_the_stem_branch():
    assert _route({"subject": "mathematics"}) == "stem"


def test_the_router_reads_a_json_string_too():
    # State values arrive as a dict or as the JSON the model emitted.
    assert _route(json.dumps({"subject": "german"})) == "language"


def test_an_unknown_subject_falls_back_rather_than_failing():
    # STEM's structure is the more general one; a lesson with a spare
    # prerequisite review is recoverable, no lesson at all is not.
    assert _route({"subject": "klingon"}) == "stem"
    assert _route({}) == "stem"
    assert _route("not json at all") == "stem"


def test_the_graph_branches_on_the_two_routes():
    edges = [(e.from_node.name, e.to_node.name, e.route) for e in preparation_workflow.graph.edges]
    assert ("route_by_domain", "language_lesson_planner", "language") in edges
    assert ("route_by_domain", "stem_lesson_planner", "stem") in edges


def test_the_router_sits_after_the_objective_agent():
    edges = [(e.from_node.name, e.to_node.name) for e in preparation_workflow.graph.edges]
    assert ("objective_agent", "route_by_domain") in edges


def test_both_planners_share_the_five_drawn_tools():
    lang = {t.__name__ for t in language_lesson_planner.tools}
    stem = {t.__name__ for t in stem_lesson_planner.tools}
    assert lang == stem == {
        "get_curriculum_lesson", "get_prerequisites", "get_student_profile",
        "get_student_mastery", "get_previous_lesson",
    }


def test_both_planners_write_the_same_state_key():
    # Only one branch runs, so downstream reads one key either way.
    assert language_lesson_planner.output_key == stem_lesson_planner.output_key == "lesson_plan"


def test_the_language_planner_carries_all_four_focus_structures():
    instruction = language_lesson_planner.instruction
    for focus, phases in LANGUAGE_PHASES.items():
        assert focus in instruction
        assert phases[0] in instruction


def test_the_stem_planner_requires_prerequisite_review():
    assert "prerequisite-review" in STEM_PHASES
    assert "Prerequisite review is not optional" in stem_lesson_planner.instruction


def _obj(oid="o1"):
    return LessonObjective(id=oid, statement="I can do it.",
                           measurable_by="Three correct unaided.",
                           covers_item_id="a1-1.classroom.l3", estimated_minutes=20)


def _act(aid, minutes, serves=("o1",), phase="explanation"):
    return LessonActivity(id=aid, phase=phase, title="t", description="d",
                          minutes=minutes, serves_objective_ids=list(serves))


def _plan(activities, objectives=None):
    return LessonPlan(student_id="s1", subject="german", domain="language",
                      level_id="a1-1", target_item_id="a1-1.classroom.l3", focus="grammar",
                      objectives=objectives or [_obj()], activities=activities,
                      reason="because")


def test_a_plan_may_not_overrun_the_paid_hour():
    with pytest.raises(ValidationError, match="ends on time"):
        _plan([_act("a1", 40), _act("a2", 30)])


def test_a_plan_must_fill_the_paid_hour():
    with pytest.raises(ValidationError, match="fills only"):
        _plan([_act("a1", 10), _act("a2", 10)])


def test_an_objective_no_activity_serves_is_rejected():
    # The quiet failure: the plan lists the objective, reads fine, and contains
    # nothing that teaches it.
    with pytest.raises(ValidationError, match="have no activity serving them"):
        _plan([_act("a1", 30, serves=()), _act("a2", 25, serves=())])


def test_a_valid_plan_passes():
    plan = _plan([_act("a1", 30), _act("a2", 25, phase="assessment")])
    assert plan.total_minutes == 55


def test_activity_ids_must_be_unique():
    with pytest.raises(ValidationError, match="duplicate activity ids"):
        _plan([_act("a1", 30), _act("a1", 25)])
