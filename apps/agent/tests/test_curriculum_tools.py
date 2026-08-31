"""The Curriculum agent's three tools.

Tested without a model. These are the agent's whole view of the world, so what
they refuse to return matters as much as what they do — an agent told never to
invent an id can only comply if the tools never hand it one.
"""

from __future__ import annotations

from datetime import datetime, timezone

from zanoba_agent.agents import curriculum_agent as ca
from zanoba_agent.store.history import CompletedLesson, InMemoryLessonHistory


def _completed(lesson_id: str, level_id: str = "a1-1", day: int = 1) -> CompletedLesson:
    return CompletedLesson(
        lesson_id=lesson_id,
        subject="german",
        level_id=level_id,
        completed_at=datetime(2026, 8, day, tzinfo=timezone.utc),
    )


def test_get_curriculum_without_a_level_lists_levels_only():
    result = ca.get_curriculum("german")
    assert result["domain"] == "language"
    assert result["levels"][0] == "a1-1"
    assert "items" not in result, "the cheap call must not load every lesson"


def test_get_curriculum_returns_ordered_items_for_a_level():
    items = ca.get_curriculum("german", "a1-1")["items"]
    assert items[0]["order"] == 1
    assert items[1]["id"] == "a1-1.classroom.l1"
    assert items[1]["focus"] == "vocabulary"


def test_get_curriculum_reports_unknown_subject_as_an_error():
    result = ca.get_curriculum("klingon")
    assert "error" in result and "klingon" in result["error"]


def test_get_curriculum_unknown_level_offers_the_real_ones():
    result = ca.get_curriculum("german", "z9-9")
    assert "error" in result
    assert "a1-1" in result["levels"], "an error should still help it recover"


def test_objectives_come_through_verbatim():
    items = {x["id"]: x for x in ca.get_curriculum("german", "a1-1")["items"]}
    objectives = items["a1-1.classroom.l1"]["objectives"]
    assert objectives, "the German curriculum authors objectives"
    assert any("greet" in o.lower() for o in objectives)


def test_history_is_empty_for_a_new_student():
    ca.set_history_store(InMemoryLessonHistory())
    assert ca.get_previous_lessons("s1", "german")["completed"] == []


def test_history_comes_back_oldest_first():
    ca.set_history_store(
        InMemoryLessonHistory(
            [_completed("a1-1.classroom.l2", day=5), _completed("a1-1.classroom.l1", day=2)]
        )
    )
    done = ca.get_previous_lessons("s1", "german")["completed"]
    assert [x["lesson_id"] for x in done] == ["a1-1.classroom.l1", "a1-1.classroom.l2"]


def test_history_is_scoped_to_the_subject():
    store = InMemoryLessonHistory([_completed("a1-1.classroom.l1")])
    ca.set_history_store(store)
    assert ca.get_previous_lessons("s1", "mathematics")["completed"] == []


def test_get_prerequisites_matches_the_repository():
    result = ca.get_prerequisites("german", "a1-1.classroom.l3")
    assert result["prerequisites"] == [
        "a1-1.get-started.l1",
        "a1-1.classroom.l1",
        "a1-1.classroom.l2",
    ]


def test_get_prerequisites_refuses_an_id_that_does_not_exist():
    result = ca.get_prerequisites("german", "a1-1.invented.l1")
    assert "error" in result
    assert "prerequisites" not in result, "a bad id must not yield a usable answer"


def test_stem_items_are_flagged_as_units_where_no_lessons_exist():
    items = ca.get_curriculum("mathematics", "6th-grade")["items"]
    assert all(x["granularity"] == "unit" for x in items)


def test_the_french_maths_programme_is_taught_by_lesson():
    items = ca.get_curriculum("mathematics", "fr.sixieme")["items"]
    assert all(x["granularity"] == "lesson" for x in items)
    assert len(items) >= 30, "6e should have a lesson for every chapter"


def test_agent_is_wired_to_its_three_drawn_tools():
    names = {t.__name__ for t in ca.curriculum_agent.tools}
    assert names == {"get_curriculum", "get_previous_lessons", "get_prerequisites"}
    assert ca.curriculum_agent.output_schema is not None
