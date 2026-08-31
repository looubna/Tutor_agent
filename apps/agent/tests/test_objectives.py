"""The objective schema, and the constraint that makes "achievable" real.

The diagram asks for objectives that are achievable within an hour. Four of the
five criteria are judgement; the count and the clock are arithmetic, and those
are what these tests hold.
"""

from __future__ import annotations

import pytest
from pydantic import ValidationError

from zanoba_agent.agents.objective_agent import objective_agent
from zanoba_agent.schemas.objectives import (
    TEACHING_MINUTES,
    LessonObjective,
    LessonObjectives,
)


def _obj(oid: str, minutes: int, **kw) -> LessonObjective:
    return LessonObjective(
        id=oid,
        statement=f"I can do thing {oid}.",
        measurable_by="The student produces three correct examples unaided.",
        covers_item_id="a1-1.classroom.l3",
        estimated_minutes=minutes,
        **kw,
    )


def _objectives(*objs: LessonObjective) -> LessonObjectives:
    return LessonObjectives(
        student_id="s1",
        subject="german",
        level_id="a1-1",
        target_item_id="a1-1.classroom.l3",
        focus="grammar",
        objectives=list(objs),
        reason="Because.",
    )


def test_a_plan_that_does_not_fit_the_hour_is_rejected():
    with pytest.raises(ValidationError, match="minutes of teaching but only"):
        _objectives(_obj("o1", 30), _obj("o2", 30))


def test_a_plan_that_exactly_fills_the_teaching_time_is_allowed():
    plan = _objectives(_obj("o1", 25), _obj("o2", 25))
    assert plan.total_minutes == TEACHING_MINUTES


def test_at_least_one_objective_is_required():
    with pytest.raises(ValidationError):
        _objectives()


def test_more_than_three_objectives_is_rejected():
    with pytest.raises(ValidationError):
        _objectives(_obj("o1", 10), _obj("o2", 10), _obj("o3", 10), _obj("o4", 10))


def test_objective_ids_must_be_unique():
    with pytest.raises(ValidationError, match="duplicate objective ids"):
        _objectives(_obj("o1", 10), _obj("o1", 10))


def test_an_objective_too_small_to_be_a_goal_is_rejected():
    with pytest.raises(ValidationError):
        _obj("o1", 2)


def test_a_single_objective_may_not_exceed_the_teaching_time():
    with pytest.raises(ValidationError):
        _obj("o1", TEACHING_MINUTES + 1)


def test_review_objectives_carry_no_source_objective():
    plan = _objectives(_obj("o1", 15, is_review=True), _obj("o2", 20))
    review = plan.objectives[0]
    assert review.is_review is True
    assert review.source_objective == ""


def test_deferred_objectives_are_kept_not_dropped():
    plan = LessonObjectives(
        student_id="s1",
        subject="german",
        level_id="a1-1",
        target_item_id="a1-1.classroom.l3",
        objectives=[_obj("o1", 25)],
        deferred=["I can write down a new noun with its article and its plural."],
        reason="Only one objective fits once the review is accounted for.",
    )
    assert plan.deferred


def test_the_agent_has_no_tools_by_design():
    # The diagram draws this agent without a tool box. Adding one would let it
    # go looking for a different answer than the two agents upstream agreed on.
    assert objective_agent.tools == []
    assert objective_agent.output_schema is not None
    assert objective_agent.output_key == "lesson_objectives"


def test_the_instruction_reads_both_upstream_outputs():
    instruction = objective_agent.instruction
    assert "{curriculum_placement}" in instruction
    assert "{diagnostic_report}" in instruction
