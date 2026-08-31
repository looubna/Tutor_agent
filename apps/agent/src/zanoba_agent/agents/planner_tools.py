"""The five tools both Lesson Planners are drawn with.

The diagram gives the Language and STEM planners identical tool boxes, so they
live here once. What differs between the planners is the instruction and the
lesson structure they build, not what they can look up.

Every one of these is a read. A planner cannot write to a profile or record a
result — planning happens before the lesson, and nothing has happened yet to
record.
"""

from __future__ import annotations

from ..curriculum import repository
from ..store.history import InMemoryLessonHistory, LessonHistoryStore
from ..store.profiles import InMemoryProfileStore, ProfileStore

_profiles: ProfileStore = InMemoryProfileStore()
_history: LessonHistoryStore = InMemoryLessonHistory()


def set_stores(profiles: ProfileStore, history: LessonHistoryStore) -> None:
    """Swap the backends. Firestore in production, fakes in tests."""
    global _profiles, _history
    _profiles, _history = profiles, history


def get_curriculum_lesson(subject: str, item_id: str) -> dict:
    """Return one curriculum lesson or unit with its objectives.

    Args:
      subject: Subject id, e.g. "german".
      item_id: The lesson or unit id to fetch.

    Returns:
      The item's title, focus, objectives and the chapter or unit it sits in.
      Objectives here are the curriculum's own and are the only ones that may be
      quoted as such.
    """
    item = repository.find_item(subject, item_id)
    if item is None:
        return {"error": f"No item {item_id!r} in {subject!r}."}
    return {
        "subject": subject,
        "item_id": item.id,
        "title": item.title,
        "granularity": item.granularity,
        "focus": item.focus,
        "objectives": item.objectives,
        "parent_id": item.parent_id,
        "parent_title": item.parent_title,
        "order": item.order,
    }


def get_prerequisites(subject: str, item_id: str) -> dict:
    """Return what should have been taught before this lesson.

    Args:
      subject: Subject id, e.g. "german".
      item_id: The lesson or unit id to look up.

    Returns:
      Prerequisite item ids with their titles, most deliberate first.
    """
    item = repository.find_item(subject, item_id)
    if item is None:
        return {"error": f"No item {item_id!r} in {subject!r}."}
    ids = repository.prerequisites_of(subject, item_id)
    return {
        "subject": subject,
        "item_id": item_id,
        "prerequisites": [
            {"item_id": pid,
             "title": (p.title if (p := repository.find_item(subject, pid)) else "")}
            for pid in ids
        ],
    }


def get_student_profile(student_id: str, subject: str) -> dict:
    """Return how this student prefers to be taught, and what they struggle with.

    Args:
      student_id: The student's id.
      subject: Subject id, e.g. "german".

    Returns:
      Learning preferences, strengths, weaknesses and misconceptions. Preferences
      are what the student said, not what a model inferred, so they can be
      followed directly.
    """
    profile = _profiles.get_student(student_id)
    if profile is None:
        return {"student_id": student_id, "profile_exists": False}

    prefs = profile.learning_preferences
    learning = profile.for_subject(subject)
    return {
        "student_id": student_id,
        "profile_exists": True,
        "age": profile.demographics.age,
        "grade": profile.demographics.grade,
        "preferences": {
            "preferred_explanation": prefs.preferred_explanation,
            "correction_style": prefs.correction_style,
            "likes_conversation": prefs.likes_conversation,
            "likes_visual_material": prefs.likes_visual_material,
            "preferred_topics": prefs.preferred_topics,
        },
        "strengths": learning.strengths if learning else [],
        "weaknesses": learning.weaknesses if learning else [],
        "misconceptions": [
            {"concept": m.concept, "description": m.description, "severity": m.severity}
            for m in (learning.misconceptions if learning else [])
        ],
    }


def get_student_mastery(student_id: str, subject: str) -> dict:
    """Return what this student has and has not mastered, with evidence.

    Args:
      student_id: The student's id.
      subject: Subject id, e.g. "german".

    Returns:
      Mastery entries with scores and the lessons they came from. Absent means
      never attempted, which is different from attempted and failed.
    """
    profile = _profiles.get_student(student_id)
    learning = profile.for_subject(subject) if profile else None
    if learning is None:
        return {"student_id": student_id, "subject": subject, "mastery": []}
    return {
        "student_id": student_id,
        "subject": subject,
        "overall_level": learning.overall_level,
        "mastery": [
            {
                "item_id": m.item_id,
                "title": (i.title if (i := repository.find_item(subject, m.item_id)) else ""),
                "score": m.score,
                "attempts": m.attempts,
                "evidence_lesson_ids": m.evidence_lesson_ids,
            }
            for m in learning.mastery
        ],
    }


def get_previous_lesson(student_id: str, subject: str) -> dict:
    """Return the most recent lesson this student took in a subject.

    Args:
      student_id: The student's id.
      subject: Subject id, e.g. "german".

    Returns:
      The last lesson with what was finished, what was left unfinished, and what
      the tutor observed. Unfinished objectives are the strongest signal for what
      the opening retrieval of this lesson should cover.
    """
    lessons = _history.completed_lessons(student_id, subject)
    if not lessons:
        return {"student_id": student_id, "subject": subject, "previous_lesson": None}
    last = lessons[-1]
    return {
        "student_id": student_id,
        "subject": subject,
        "previous_lesson": {
            "lesson_id": last.lesson_id,
            "completed_at": last.completed_at.isoformat(),
            "objectives_completed": last.objectives_completed,
            "objectives_unfinished": last.objectives_unfinished,
            "observations": last.observations,
            "score": last.assessment.score if last.assessment else None,
        },
    }


PLANNER_TOOLS = [
    get_curriculum_lesson,
    get_prerequisites,
    get_student_profile,
    get_student_mastery,
    get_previous_lesson,
]
