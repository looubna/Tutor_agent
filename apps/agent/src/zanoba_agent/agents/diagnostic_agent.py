"""The Diagnostic agent — the second node of the preparation pipeline.

The diagram's brief: *determine what the student actually knows*, from mastered
concepts, partially mastered concepts, missing prerequisites, misconceptions,
and appropriate difficulty.

Where the Curriculum agent was blind to ability on purpose, this one is blind
to the syllabus's opinion — it is handed the target lesson and asked only
whether the student can take it. Its four tools are the four drawn.

The one rule it cannot bend: every standing it reports must trace to a stored
mastery entry or a completed lesson. It has no tool that will invent one, and
`MasteryEntry` refuses to hold a score without evidence, so a fabricated claim
has nowhere to enter from.
"""

from __future__ import annotations

import os
from collections import Counter

from google.adk.agents import LlmAgent

from ..curriculum import repository
from ..schemas.diagnostic import DiagnosticReport
from ..store.history import InMemoryLessonHistory, LessonHistoryStore
from ..store.profiles import InMemoryProfileStore, ProfileStore

MODEL = os.environ.get("ZANOBA_MODEL", "gemini-3.5-flash")

# Below this a skill is treated as not held; above the second, as held. Stated
# here rather than left to the model so the boundary is inspectable and the
# same for every student.
PARTIAL_AT = 0.4
MASTERED_AT = 0.75

_profiles: ProfileStore = InMemoryProfileStore()
_history: LessonHistoryStore = InMemoryLessonHistory()


def set_stores(profiles: ProfileStore, history: LessonHistoryStore) -> None:
    """Swap the backends. Firestore in production, fakes in tests."""
    global _profiles, _history
    _profiles, _history = profiles, history


def _standing(score: float) -> str:
    if score >= MASTERED_AT:
        return "mastered"
    return "partial" if score >= PARTIAL_AT else "not_started"


def get_student_history(student_id: str, subject: str) -> dict:
    """Return every lesson this student has completed in a subject.

    Args:
      student_id: The student's id.
      subject: Subject id, e.g. "german".

    Returns:
      Completed lessons oldest first, with objectives finished and unfinished
      and anything the tutor observed. Unfinished objectives are evidence about
      what to revisit, not a mark against the student.
    """
    lessons = _history.completed_lessons(student_id, subject)
    return {
        "student_id": student_id,
        "subject": subject,
        "lesson_count": len(lessons),
        "lessons": [
            {
                "lesson_id": x.lesson_id,
                "level_id": x.level_id,
                "completed_at": x.completed_at.isoformat(),
                "objectives_completed": x.objectives_completed,
                "objectives_unfinished": x.objectives_unfinished,
                "observations": x.observations,
            }
            for x in lessons
        ],
    }


def get_assessment_results(student_id: str, subject: str) -> dict:
    """Return the measured results of assessments this student has taken.

    Args:
      student_id: The student's id.
      subject: Subject id, e.g. "german".

    Returns:
      One entry per assessed lesson with its score and the error tags recorded.
      A lesson with no assessment is omitted rather than reported as zero — not
      being tested is not the same as failing.
    """
    lessons = _history.completed_lessons(student_id, subject)
    assessed = [x for x in lessons if x.assessment is not None]
    return {
        "student_id": student_id,
        "subject": subject,
        "assessed_count": len(assessed),
        "unassessed_count": len(lessons) - len(assessed),
        "results": [
            {
                "lesson_id": x.lesson_id,
                "score": x.assessment.score,
                "items_correct": x.assessment.items_correct,
                "items_total": x.assessment.items_total,
                "error_tags": x.assessment.error_tags,
            }
            for x in assessed
        ],
    }


def get_mastery(student_id: str, subject: str) -> dict:
    """Return stored mastery for a student in a subject, with its evidence.

    Args:
      student_id: The student's id.
      subject: Subject id, e.g. "german".

    Returns:
      Each mastery entry with its score, attempts and the lessons it came from,
      classified as mastered, partial or not_started. Also the misconceptions,
      strengths and weaknesses recorded on the profile. An empty result means no
      profile yet, which is a beginner rather than a student who knows nothing.
    """
    profile = _profiles.get_student(student_id)
    if profile is None:
        return {"student_id": student_id, "subject": subject, "profile_exists": False,
                "mastery": [], "misconceptions": []}

    learning = profile.for_subject(subject)
    if learning is None:
        return {"student_id": student_id, "subject": subject, "profile_exists": True,
                "subject_seen": False, "mastery": [], "misconceptions": []}

    entries = [
        {
            "item_id": m.item_id,
            "title": (i.title if (i := repository.find_item(subject, m.item_id)) else ""),
            "score": m.score,
            "standing": _standing(m.score),
            "attempts": m.attempts,
            "correct": m.correct,
            "evidence_lesson_ids": m.evidence_lesson_ids,
        }
        for m in learning.mastery
    ]
    # Bucketed here, not by the model. Classifying a score against a fixed
    # threshold is arithmetic; leaving it to the model made the same student
    # come back "mastered" on one run and empty on the next.
    return {
        "student_id": student_id,
        "subject": subject,
        "profile_exists": True,
        "subject_seen": True,
        "overall_level": learning.overall_level,
        "mastery": entries,
        "mastered": [e for e in entries if e["standing"] == "mastered"],
        "partially_mastered": [e for e in entries if e["standing"] == "partial"],
        "misconceptions": [
            {
                "concept": x.concept,
                "description": x.description,
                "severity": x.severity,
                "evidence_lesson_ids": x.evidence_lesson_ids,
            }
            for x in learning.misconceptions
        ],
        "strengths": learning.strengths,
        "weaknesses": learning.weaknesses,
    }


def analyze_previous_errors(student_id: str, subject: str) -> dict:
    """Return the student's mistakes, grouped and counted.

    Args:
      student_id: The student's id.
      subject: Subject id, e.g. "german".

    Returns:
      Error tags with how often each occurred, drawn from assessments and from
      the profile's recorded recurring errors. Counting is done here rather than
      by reading — a tag seen once is not a pattern, and the count is what makes
      that judgeable.
    """
    counts: Counter[str] = Counter()
    for lesson in _history.completed_lessons(student_id, subject):
        if lesson.assessment:
            counts.update(lesson.assessment.error_tags)

    described: dict[str, str] = {}
    profile = _profiles.get_student(student_id)
    learning = profile.for_subject(subject) if profile else None
    if learning:
        for err in learning.recurring_errors:
            counts[err.tag] += err.count
            described[err.tag] = err.description

    return {
        "student_id": student_id,
        "subject": subject,
        "errors": [
            {"tag": tag, "count": n, "description": described.get(tag, ""),
             "recurring": n > 1}
            for tag, n in counts.most_common()
        ],
    }


INSTRUCTION = """\
You are the Diagnostic agent for a 1-to-1 tutoring platform. The Curriculum
agent has proposed a lesson. You decide what the student actually knows, and
whether they can take that lesson.

The Curriculum agent's placement, which names the target lesson and its
prerequisites:
{curriculum_placement}

The student to diagnose is the student_id in that placement. Use it for
every tool call.

How to work:
1. Call get_mastery for stored mastery, misconceptions, strengths, weaknesses.
2. Call get_student_history for what has actually been taught and what was left
   unfinished.
3. Call get_assessment_results for measured scores.
4. Call analyze_previous_errors for mistakes grouped and counted.
5. get_mastery already returns "mastered" and "partially_mastered" arrays,
   bucketed against fixed thresholds. COPY those arrays into your output
   unchanged — do not re-judge them and do not leave them empty when the tool
   returned entries. Add missing_prerequisites yourself: prerequisites of the
   target with no mastery entry and no completed lesson.
6. Decide readiness and recommended_difficulty, and list anything worth
   reviewing first.

Rules that are not negotiable:
- Every item you report MUST come from a tool result. Never invent an item id,
  a score, or a standing.
- If a prerequisite has no mastery entry and no completed lesson, it is
  not_started with score null. Do not guess a number for it.
- No profile, or no history, means a beginner. Say readiness "ready" at
  difficulty "below" and explain that there is no evidence yet. Do not report
  weaknesses you have not seen.
- A single occurrence is not a recurring error. Use the counts you were given.
- Copy recurring_errors from analyze_previous_errors for every tag with
  recurring true. Do not drop them.
- Never claim a student knows something because the syllabus taught it. Only a
  mastery entry or an assessment counts as evidence.

Readiness:
- "ready" — no missing prerequisites of consequence.
- "ready_with_review" — gaps exist but can be covered inside the hour; list them
  in review_first.
- "not_ready" — a missing prerequisite is load-bearing for the target lesson.

Keep reason to two or three sentences, citing the evidence you actually saw.
"""

diagnostic_agent = LlmAgent(
    name="diagnostic_agent",
    model=MODEL,
    description="Determines what a student actually knows, from stored evidence.",
    instruction=INSTRUCTION,
    tools=[
        get_student_history,
        get_assessment_results,
        get_mastery,
        analyze_previous_errors,
    ],
    output_schema=DiagnosticReport,
    output_key="diagnostic_report",
)
