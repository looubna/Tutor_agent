"""The live lesson state machine, presence, and the scheduled end."""

from __future__ import annotations

import json
from datetime import datetime, timedelta, timezone

import pytest

from zanoba_agent.agents.live_tutor import (
    LIVE_TUTOR_TOOLS, bind_session, clear_board, evaluate_student_answer,
    live_tutor_agent, record_observation, session_surfaces, show_material,
    stop_showing_material, write_on_board)
from zanoba_agent.live import state_machine as sm
from zanoba_agent.schemas.lesson_state import (
    LessonState, ObjectiveProgress, Scheduled)

START = datetime(2026, 8, 30, 10, 0, tzinfo=timezone.utc)
AT = lambda m: START + timedelta(minutes=m)


def _state(**kw) -> LessonState:
    return LessonState(
        lesson_id="L1", student_id="s1", subject="german", level_id="a1-1",
        scheduled=Scheduled(start_time=START, duration_minutes=60),
        objectives=[ObjectiveProgress(objective_id="o1", statement="I can x."),
                    ObjectiveProgress(objective_id="o2", statement="I can y.")],
        **kw)


def _teaching(now=AT(2)) -> LessonState:
    st = _state()
    sm.observe_presence(st, True, False, now)
    return sm.start_lesson(st, now)


# ---- the happy path --------------------------------------------------------

def test_the_lesson_walks_the_states_in_the_brief_order():
    st = _teaching()
    assert [t.to_state for t in st.transitions] == [
        "STUDENT_DETECTED", "GREETING", "LESSON_STARTED", "TEACHING"]
    assert st.status == "in_progress"
    assert st.execution.started_at is not None


def test_question_answer_evaluate_continue():
    st = _teaching()
    for to in ("QUESTION", "STUDENT_RESPONDS", "EVALUATE", "CONTINUE", "TEACHING"):
        sm.transition(st, to, "t", AT(5))
    assert st.live_state == "TEACHING"


def test_evaluate_can_branch_to_explain_or_adapt():
    for branch in ("EXPLAIN", "ADAPT"):
        st = _teaching()
        for to in ("QUESTION", "STUDENT_RESPONDS", "EVALUATE", branch):
            sm.transition(st, to, "t", AT(5))
        assert st.live_state == branch


def test_an_illegal_transition_is_refused():
    st = _teaching()
    with pytest.raises(sm.IllegalTransition):
        sm.transition(st, "STUDENT_RESPONDS", "skipped the question", AT(5))


# ---- absence ---------------------------------------------------------------

def test_a_student_who_leaves_suspends_the_lesson():
    st = _teaching()
    sm.observe_presence(st, False, False, AT(10))
    assert st.live_state == "STUDENT_ABSENT"


def test_a_returning_student_resumes_teaching():
    st = _teaching()
    sm.observe_presence(st, False, False, AT(10))
    sm.observe_presence(st, True, False, AT(14))
    assert st.live_state == "TEACHING"
    assert [t.to_state for t in st.transitions[-2:]] == ["WAITING", "TEACHING"]


def test_absence_does_not_end_the_lesson():
    st = _teaching()
    sm.observe_presence(st, False, False, AT(10))
    assert st.status == "in_progress"
    assert st.live_state != "LESSON_END"


def test_a_second_person_is_detected_but_never_identified():
    st = _teaching()
    sm.observe_presence(st, True, True, AT(5))
    assert st.presence.additional_person_detected is True
    # The model has two booleans and no name field to fill in.
    assert set(st.presence.model_dump()) == {
        "student_present", "additional_person_detected", "checked_at"}


# ---- the clock wins --------------------------------------------------------

def test_the_lesson_ends_at_the_scheduled_time():
    st = _teaching()
    sm.enforce_schedule(st, AT(60))
    assert st.live_state == "LESSON_END"
    assert st.status == "completed"


def test_any_transition_after_the_hour_ends_the_lesson_instead():
    st = _teaching()
    sm.transition(st, "QUESTION", "asking anyway", AT(61))
    assert st.live_state == "LESSON_END"


def test_presence_after_the_hour_ends_the_lesson():
    st = _teaching()
    sm.observe_presence(st, True, False, AT(75))
    assert st.live_state == "LESSON_END"


def test_unfinished_objectives_are_marked_not_dropped():
    st = _teaching()
    st.objectives[0].status = "completed"
    sm.end_lesson(st, AT(60))
    assert [o.status for o in st.objectives] == ["completed", "unfinished"]
    assert len(st.unfinished_objectives()) == 1


def test_a_closed_lesson_cannot_be_reopened():
    st = _teaching()
    sm.end_lesson(st, AT(60))
    with pytest.raises(sm.LessonClosed):
        sm.transition(st, "TEACHING", "one more thing", AT(61))


def test_a_student_who_never_arrives_is_a_no_show():
    st = _state()
    sm.enforce_schedule(st, AT(61))
    assert st.status == "no_show"
    assert st.execution.started_at is None


def test_actual_duration_is_recorded_not_assumed():
    st = _teaching(now=AT(3))
    sm.end_lesson(st, AT(58))
    assert st.execution.actual_duration_minutes == 55


# ---- the tutor's tools -----------------------------------------------------

def test_arithmetic_answers_are_checked_exactly_not_by_eye():
    st = _teaching()
    bind_session(st, {"activities": []}, {"items": []})
    good = evaluate_student_answer("3/4 + 1/6?", "11/12", "11/12")
    bad = evaluate_student_answer("3/4 + 1/6?", "11/12", "4/10")
    assert good["correct"] is True and good["checked_exactly"] is True
    assert bad["correct"] is False and bad["suggestion"] == "explain"
    assert st.interaction.mistakes and st.interaction.successful_answers


MATERIAL = {"items": [
    {"id": "s4_item", "kind": "rule_table", "title": "Die drei Artikel",
     "instruction": "Lies die Tabelle.", "content": "der · die · das",
     "answer_key": "der (masculine), die (feminine), das (neuter)"},
    {"id": "s5_item", "kind": "exercise_set", "title": "Setze den Artikel ein",
     "content": "", "exercises": [
         {"id": "s5_e1", "prompt": "Das ist ___ Tisch.", "answer": "der",
          "instructions": "Ergänze den Artikel.", "explanation": "masculine"}]},
]}


def test_material_the_tutor_shows_reaches_the_student():
    st = _teaching()
    bind_session(st, {}, MATERIAL)
    assert show_material("s4_item")["title"] == "Die drei Artikel"
    _, _, stage, _ = session_surfaces()
    assert stage.showing()["content"] == "der · die · das"


def test_showing_material_never_puts_the_answers_on_screen():
    st = _teaching()
    bind_session(st, {}, MATERIAL)
    show_material("s5_item")
    _, _, stage, _ = session_surfaces()
    on_screen = json.dumps(stage.showing(), ensure_ascii=False)
    assert "answer" not in on_screen.lower()
    assert "der" not in json.loads(on_screen)["exercises"][0].get("prompt", "der")


def test_only_one_thing_is_on_the_screen_at_a_time():
    st = _teaching()
    bind_session(st, {}, MATERIAL)
    show_material("s4_item")
    show_material("s5_item")
    _, _, stage, _ = session_surfaces()
    assert stage.showing()["id"] == "s5_item"
    stop_showing_material()
    assert stage.showing() is None


def test_material_that_does_not_exist_is_refused_not_invented():
    st = _teaching()
    bind_session(st, {}, MATERIAL)
    assert "error" in show_material("s99_item")


def test_every_surface_the_tutor_writes_on_reaches_the_student():
    """The board was removed once for failing this, and has earned its way back.

    Nothing rendered it then, so the tutor would say "look at the board" and
    the student saw nothing. It is drawn now — which is the condition for a
    tutor being allowed to write on something at all.
    """
    st = _teaching()
    bind_session(st, {}, {})
    write_on_board("17 + 5 = 22")

    # Everything written is reachable from the surfaces the runtime renders.
    audio, paper, stage, board = session_surfaces()
    assert [a.content for a in board.snapshot()] == ["17 + 5 = 22"]
    assert st.tutor_actions.whiteboard_actions == 1

    clear_board()
    assert board.snapshot() == []


def test_observations_are_filed_as_evidence():
    st = _teaching()
    bind_session(st, {}, {})
    record_observation("misconception", "Thinks der is for all masculine plurals.")
    record_observation("success", "Named all three genders unprompted.")
    assert st.interaction.misconceptions_observed
    assert st.interaction.successful_answers


def test_there_is_one_tutor_not_one_per_subject():
    assert live_tutor_agent.name == "live_tutor"
    assert len(LIVE_TUTOR_TOOLS) == 20


def test_the_tutor_cannot_end_its_own_lesson():
    # Ending is the clock's job. No tool exposes it.
    names = {t.__name__ for t in LIVE_TUTOR_TOOLS}
    assert not any("end" in n or "finish" in n for n in names)
