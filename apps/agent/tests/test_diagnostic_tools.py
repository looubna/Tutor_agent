"""The Diagnostic agent's four tools.

The theme running through these: what the tools refuse to say. A student with
no record must come back as "no evidence", never as "knows nothing" — those
look similar in a dict and mean opposite things to a lesson planner.
"""

from __future__ import annotations

from datetime import datetime, timezone

import pytest

from zanoba_agent.agents import diagnostic_agent as da
from zanoba_agent.schemas.profile import (
    MasteryEntry,
    Misconception,
    RecurringError,
    StudentProfile,
    SubjectLearning,
)
from zanoba_agent.store.history import (
    CompletedLesson,
    InMemoryLessonHistory,
    LessonAssessment,
)
from zanoba_agent.store.profiles import InMemoryProfileStore

D = lambda d: datetime(2026, 8, d, tzinfo=timezone.utc)


@pytest.fixture
def stores():
    profiles = InMemoryProfileStore()
    profiles.save_student(
        StudentProfile(
            student_id="s1",
            learning=[
                SubjectLearning(
                    subject="german",
                    overall_level="a1-1",
                    mastery=[
                        MasteryEntry(item_id="a1-1.classroom.l1", score=0.82, attempts=9,
                                     correct=7, evidence_lesson_ids=["a1-1.classroom.l1"]),
                        MasteryEntry(item_id="a1-1.classroom.l2", score=0.55, attempts=6,
                                     correct=3, evidence_lesson_ids=["a1-1.classroom.l2"]),
                    ],
                    misconceptions=[
                        Misconception(concept="du-vs-sie", description="Uses du with strangers.",
                                      severity="medium", evidence_lesson_ids=["a1-1.classroom.l1"]),
                    ],
                    recurring_errors=[
                        RecurringError(tag="umlaut-dropped", description="Writes schon for schön.",
                                       count=3),
                    ],
                    strengths=["Recalls greetings quickly."],
                )
            ],
        )
    )
    history = InMemoryLessonHistory(
        [
            CompletedLesson(lesson_id="a1-1.classroom.l1", subject="german", level_id="a1-1",
                            completed_at=D(3), objectives_completed=["I can greet someone."],
                            assessment=LessonAssessment(score=0.78, items_correct=7, items_total=9,
                                                        error_tags=["umlaut-dropped"])),
            CompletedLesson(lesson_id="a1-1.classroom.l2", subject="german", level_id="a1-1",
                            completed_at=D(5), objectives_unfinished=["I can spell my name."],
                            observations=["Slowed down after the first few letters."]),
        ]
    )
    da.set_stores(profiles, history)
    return profiles, history


def test_mastery_is_classified_against_stated_thresholds(stores):
    by_id = {m["item_id"]: m for m in da.get_mastery("s1", "german")["mastery"]}
    assert by_id["a1-1.classroom.l1"]["standing"] == "mastered"   # 0.82
    assert by_id["a1-1.classroom.l2"]["standing"] == "partial"    # 0.55


def test_mastery_carries_the_curriculum_title(stores):
    by_id = {m["item_id"]: m for m in da.get_mastery("s1", "german")["mastery"]}
    assert by_id["a1-1.classroom.l1"]["title"] == "Hello and goodbye"


def test_mastery_always_carries_its_evidence(stores):
    for entry in da.get_mastery("s1", "german")["mastery"]:
        assert entry["evidence_lesson_ids"], f"{entry['item_id']} has a score with no evidence"


def test_no_profile_is_reported_as_absent_not_as_zero(stores):
    result = da.get_mastery("ghost", "german")
    assert result["profile_exists"] is False
    assert result["mastery"] == []
    assert "overall_level" not in result, "an absent profile must not imply a level"


def test_a_subject_never_studied_is_distinguished_from_a_missing_profile(stores):
    result = da.get_mastery("s1", "physics")
    assert result["profile_exists"] is True
    assert result["subject_seen"] is False


def test_unassessed_lessons_are_counted_not_scored_as_zero(stores):
    result = da.get_assessment_results("s1", "german")
    assert result["assessed_count"] == 1
    assert result["unassessed_count"] == 1
    assert [r["lesson_id"] for r in result["results"]] == ["a1-1.classroom.l1"]


def test_history_keeps_unfinished_objectives_and_observations(stores):
    lessons = {x["lesson_id"]: x for x in da.get_student_history("s1", "german")["lessons"]}
    assert lessons["a1-1.classroom.l2"]["objectives_unfinished"] == ["I can spell my name."]
    assert lessons["a1-1.classroom.l2"]["observations"]


def test_errors_are_aggregated_across_assessments_and_profile(stores):
    errors = {e["tag"]: e for e in da.analyze_previous_errors("s1", "german")["errors"]}
    # 1 from the assessment + 3 recorded on the profile.
    assert errors["umlaut-dropped"]["count"] == 4
    assert errors["umlaut-dropped"]["recurring"] is True
    assert errors["umlaut-dropped"]["description"]


def test_a_single_occurrence_is_not_marked_recurring():
    profiles, history = InMemoryProfileStore(), InMemoryLessonHistory(
        [CompletedLesson(lesson_id="l1", subject="german", level_id="a1-1", completed_at=D(1),
                         assessment=LessonAssessment(score=0.9, error_tags=["one-off"]))]
    )
    da.set_stores(profiles, history)
    errors = {e["tag"]: e for e in da.analyze_previous_errors("s1", "german")["errors"]}
    assert errors["one-off"]["count"] == 1
    assert errors["one-off"]["recurring"] is False


def test_a_brand_new_student_yields_empty_evidence_everywhere():
    da.set_stores(InMemoryProfileStore(), InMemoryLessonHistory())
    assert da.get_student_history("new", "german")["lesson_count"] == 0
    assert da.get_assessment_results("new", "german")["results"] == []
    assert da.get_mastery("new", "german")["mastery"] == []
    assert da.analyze_previous_errors("new", "german")["errors"] == []


def test_agent_is_wired_to_its_four_drawn_tools():
    names = {t.__name__ for t in da.diagnostic_agent.tools}
    assert names == {
        "get_student_history",
        "get_assessment_results",
        "get_mastery",
        "analyze_previous_errors",
    }
    assert da.diagnostic_agent.output_schema is not None


def test_mastery_buckets_are_computed_by_the_tool_not_the_model(stores):
    # Classifying a score against a fixed threshold is arithmetic. Leaving it to
    # the model made the same student come back "mastered" on one run and empty
    # on the next, against identical Firestore data.
    result = da.get_mastery("s1", "german")
    assert [x["item_id"] for x in result["mastered"]] == ["a1-1.classroom.l1"]
    assert [x["item_id"] for x in result["partially_mastered"]] == ["a1-1.classroom.l2"]


def test_buckets_are_absent_rather_than_empty_when_there_is_no_profile(stores):
    result = da.get_mastery("ghost", "german")
    assert "mastered" not in result, "no profile must not look like 'nothing mastered'"
