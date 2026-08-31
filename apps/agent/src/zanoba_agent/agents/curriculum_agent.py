"""The Curriculum agent — the first node of the preparation pipeline.

It answers one question from the diagram: *what should normally be taught
next*. Normally, meaning according to the syllabus. It has no opinion about
whether the student is ready; that is the Diagnostic agent's job downstream,
and this agent deliberately cannot see mastery scores to reach for.

Its three tools are the three drawn in the diagram, and nothing else. The
lookups behind them are deterministic — `curriculum.repository` does the index
work — so the model's job is to pick the right item and say why, not to
compute ordering it would only get wrong.
"""

from __future__ import annotations

import os

from google.adk.agents import LlmAgent

from ..curriculum import repository
from ..store.history import InMemoryLessonHistory, LessonHistoryStore
from ..schemas.placement import CurriculumPlacement

# Gemini 3.5+ is required by the platform we target. Overridable so a run can
# be pointed at a stronger model without a code change.
MODEL = os.environ.get("ZANOBA_MODEL", "gemini-3.5-flash")

_history: LessonHistoryStore = InMemoryLessonHistory()


def set_history_store(store: LessonHistoryStore) -> None:
    """Swap the history backend. Firestore in production, a fake in tests."""
    global _history
    _history = store


def get_curriculum(subject: str, level_id: str = "") -> dict:
    """Return the teachable items of a subject, in teaching order.

    Args:
      subject: Subject id, e.g. "german" or "mathematics".
      level_id: Level or program id, e.g. "a1-1". Empty returns the level list
        only, which is the cheaper call when you do not yet know the level.

    Returns:
      For an empty level_id, the subject's domain and its level ids. Otherwise
      the ordered items of that level, each with its id, title, focus and
      objectives.
    """
    try:
        domain = repository.domain_of(subject)
    except repository.CurriculumNotFound as exc:
        return {"error": str(exc)}

    if not level_id:
        return {
            "subject": subject,
            "domain": domain,
            "levels": repository.level_ids(subject),
        }

    items = repository.items_in_order(subject, level_id)
    if not items:
        return {
            "error": f"No level {level_id!r} in {subject!r}.",
            "levels": repository.level_ids(subject),
        }
    return {
        "subject": subject,
        "domain": domain,
        "level_id": level_id,
        "items": [x.model_dump(exclude={"prerequisites"}) for x in items],
    }


def get_previous_lessons(student_id: str, subject: str) -> dict:
    """Return the lessons this student has already completed in a subject.

    Args:
      student_id: The student's id.
      subject: Subject id, e.g. "german".

    Returns:
      Completed lessons oldest first, with the objectives that were and were
      not finished. An empty list means a student with no history in this
      subject — a beginner, not an error.
    """
    lessons = _history.completed_lessons(student_id, subject)
    return {
        "student_id": student_id,
        "subject": subject,
        "completed": [
            {
                "lesson_id": x.lesson_id,
                "level_id": x.level_id,
                "completed_at": x.completed_at.isoformat(),
                "objectives_completed": x.objectives_completed,
                "objectives_unfinished": x.objectives_unfinished,
            }
            for x in lessons
        ],
    }


def get_prerequisites(subject: str, item_id: str) -> dict:
    """Return what should be taught before a given lesson or unit.

    Args:
      subject: Subject id, e.g. "german".
      item_id: The lesson or unit id to look up.

    Returns:
      The prerequisite item ids, most deliberate first. Explicitly declared
      prerequisites come before those implied by syllabus order.
    """
    item = repository.find_item(subject, item_id)
    if item is None:
        return {"error": f"No item {item_id!r} in {subject!r}."}
    return {
        "subject": subject,
        "item_id": item_id,
        "prerequisites": repository.prerequisites_of(subject, item_id),
    }


INSTRUCTION = """\
You are the Curriculum agent for a 1-to-1 tutoring platform. You decide what the
syllabus says should be taught next for one student in one subject.

You are answering about the CURRICULUM, not about the student's ability. You do
not judge whether they are ready — a later agent does that. Report what the
syllabus orders next, and report unmet prerequisites as evidence for it.

How to work:
1. Call get_curriculum with the subject and, when you know it, the level, to see
   the ordered items.
2. Call get_previous_lessons to see what the student has already completed.
3. The next item is the first one in order with no completion on record. If
   everything at the level is complete, say so and name the first item of the
   next level.
4. Call get_prerequisites on your chosen item. Any prerequisite the student has
   not completed goes in unmet_prerequisites.

Rules:
- Always set student_id to the student you were asked about. Downstream
  agents get this object and nothing else.
- Only ever name ids that a tool returned. Never invent a lesson, unit or id.
- Copy objectives verbatim from the curriculum. Never write your own.
- Never infer or state a mastery level, score or ability. You cannot see any.
- If granularity is "unit", no lessons are authored beneath it yet — say so in
  your reason rather than pretending it is a single lesson.
- Keep reason to one or two sentences, and cite the syllabus position.
"""

curriculum_agent = LlmAgent(
    name="curriculum_agent",
    model=MODEL,
    description="Decides what the syllabus says a student should be taught next.",
    instruction=INSTRUCTION,
    tools=[get_curriculum, get_previous_lessons, get_prerequisites],
    output_schema=CurriculumPlacement,
    output_key="curriculum_placement",
)
