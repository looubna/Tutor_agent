"""The student profile, and the one rule that protects it.

"Never fabricate mastery" is the requirement these tests exist for. It is
stated in the prompt of every agent that touches a profile, but a prompt is a
request — the validator is the thing that actually stops it.
"""

from __future__ import annotations

from datetime import datetime, timezone

import pytest
from pydantic import ValidationError

from zanoba_agent.schemas.profile import (
    LanguageKnowledge,
    LanguageLearnerProfile,
    MasteryEntry,
    StudentProfile,
    SubjectLearning,
)
from zanoba_agent.store.profiles import InMemoryProfileStore


def test_mastery_needs_evidence():
    with pytest.raises(ValidationError, match="must come from evidence"):
        MasteryEntry(item_id="a1-1.classroom.l3", score=0.9)


def test_zero_mastery_needs_no_evidence():
    # "Not seen yet" is a legitimate, honest state.
    entry = MasteryEntry(item_id="a1-1.classroom.l3", score=0.0)
    assert entry.score == 0.0


def test_evidence_can_be_attempts_or_named_lessons():
    assert MasteryEntry(item_id="x", score=0.5, attempts=4, correct=2).score == 0.5
    assert MasteryEntry(item_id="x", score=0.5, evidence_lesson_ids=["a1-1.classroom.l1"])


def test_correct_cannot_exceed_attempts():
    with pytest.raises(ValidationError, match="correct out of"):
        MasteryEntry(item_id="x", score=0.5, attempts=2, correct=3)


def test_score_stays_within_range():
    with pytest.raises(ValidationError):
        MasteryEntry(item_id="x", score=1.4, attempts=2, correct=2)


def test_profile_finds_the_subject_it_was_asked_for():
    profile = StudentProfile(
        student_id="s1",
        learning=[
            SubjectLearning(subject="german", overall_level="a1-1"),
            SubjectLearning(subject="mathematics", overall_level="fr.sixieme"),
        ],
    )
    assert profile.for_subject("german").overall_level == "a1-1"
    assert profile.for_subject("physics") is None


def test_saving_stamps_updated_at():
    store = InMemoryProfileStore()
    store.save_student(StudentProfile(student_id="s1"))
    saved = store.get_student("s1")
    assert saved.updated_at is not None
    assert saved.updated_at.tzinfo is timezone.utc or saved.updated_at.utcoffset() is not None


def test_missing_profile_is_none_not_an_error():
    store = InMemoryProfileStore()
    assert store.get_student("nobody") is None
    assert store.get_language_learner("nobody", "german") is None


def test_language_profiles_are_scoped_per_subject():
    store = InMemoryProfileStore()
    store.save_language_learner(
        LanguageLearnerProfile(student_id="s1", subject="german", overall_band="A1")
    )
    store.save_language_learner(
        LanguageLearnerProfile(student_id="s1", subject="spanish", overall_band="A2")
    )
    assert store.get_language_learner("s1", "german").overall_band == "A1"
    assert store.get_language_learner("s1", "spanish").overall_band == "A2"


def test_untaught_area_holds_zero_rather_than_a_guess():
    knowledge = LanguageKnowledge(area="grammar", overall_mastery=0.0)
    assert knowledge.topics == []


def test_profile_round_trips_through_json():
    # Firestore stores plain JSON, so anything that survives model_dump(mode="json")
    # survives the database.
    original = LanguageLearnerProfile(
        student_id="s1",
        subject="german",
        overall_band="A1",
        knowledge=[
            LanguageKnowledge(
                area="vocabulary",
                overall_mastery=0.68,
                topics=[
                    MasteryEntry(
                        item_id="greetings",
                        score=0.82,
                        attempts=9,
                        correct=7,
                        last_seen_at=datetime(2026, 8, 3, tzinfo=timezone.utc),
                        evidence_lesson_ids=["a1-1.classroom.l1"],
                    )
                ],
            )
        ],
    )
    restored = LanguageLearnerProfile.model_validate(original.model_dump(mode="json"))
    assert restored == original
