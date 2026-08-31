"""Lesson history — the immutable record of what actually happened.

History is append-only. A lesson that has been taught is evidence, and evidence
does not get edited later because a newer lesson went differently. The current
picture of a student lives in their profile, which *is* updated in place; the
two are kept apart deliberately.

Same shape as `store.profiles`: a Protocol, a Firestore implementation for real
runs, an in-memory one for tests.
"""

from __future__ import annotations

from datetime import datetime
from typing import Protocol

from pydantic import BaseModel, Field

COLLECTION = "lesson_history"


class ObjectiveResult(BaseModel):
    """How one objective of a lesson went."""

    objective: str
    status: str = Field(description='"completed", "partial" or "unfinished".')


class LessonAssessment(BaseModel):
    """The measured outcome of a lesson, when one was taken."""

    score: float | None = Field(default=None, ge=0.0, le=1.0)
    items_correct: int = Field(default=0, ge=0)
    items_total: int = Field(default=0, ge=0)
    error_tags: list[str] = Field(
        default_factory=list,
        description='Short stable tags for what went wrong, e.g. "der-vs-die".',
    )


class CompletedLesson(BaseModel):
    """One lesson a student has finished. Immutable historical evidence."""

    lesson_id: str
    subject: str
    level_id: str
    completed_at: datetime
    objectives_completed: list[str] = Field(default_factory=list)
    objectives_unfinished: list[str] = Field(default_factory=list)
    objective_results: list[ObjectiveResult] = Field(default_factory=list)
    assessment: LessonAssessment | None = None
    observations: list[str] = Field(
        default_factory=list, description="What the tutor noticed, in their words."
    )


class LessonHistoryStore(Protocol):
    """The read and append sides of lesson history."""

    def completed_lessons(self, student_id: str, subject: str) -> list[CompletedLesson]:
        """Every completed lesson for one student in one subject, oldest first."""
        ...

    def record(self, student_id: str, lesson: CompletedLesson) -> None:
        """Append one lesson. Never updates an existing record."""
        ...


class InMemoryLessonHistory:
    """A list-backed store. For tests and offline runs."""

    def __init__(self, lessons: list[CompletedLesson] | None = None) -> None:
        self._by_student: dict[str, list[CompletedLesson]] = {}
        # Lessons passed in without a student are visible to every student, which
        # keeps single-student test setups to one line.
        self._shared = list(lessons or [])

    def add(self, lesson: CompletedLesson) -> None:
        self._shared.append(lesson)

    def record(self, student_id: str, lesson: CompletedLesson) -> None:
        self._by_student.setdefault(student_id, []).append(lesson)

    def completed_lessons(self, student_id: str, subject: str) -> list[CompletedLesson]:
        pool = self._shared + self._by_student.get(student_id, [])
        return sorted(
            (x for x in pool if x.subject == subject), key=lambda x: x.completed_at
        )


class FirestoreLessonHistory:
    """The real store.

    One document per completed lesson, keyed `{student}__{lesson}` so recording
    the same lesson twice overwrites rather than duplicating — a retried write
    must not look like a second attempt at the lesson.
    """

    def __init__(self, project: str | None = None, database: str = "(default)") -> None:
        self._project = project
        self._database = database
        self._client = None

    @property
    def client(self):
        if self._client is None:
            from google.cloud import firestore

            self._client = firestore.Client(
                project=self._project, database=self._database
            )
        return self._client

    def completed_lessons(self, student_id: str, subject: str) -> list[CompletedLesson]:
        from google.cloud.firestore_v1.base_query import FieldFilter

        docs = (
            self.client.collection(COLLECTION)
            .where(filter=FieldFilter("student_id", "==", student_id))
            .where(filter=FieldFilter("subject", "==", subject))
            .stream()
        )
        lessons = []
        for doc in docs:
            data = doc.to_dict() or {}
            data.pop("student_id", None)
            lessons.append(CompletedLesson.model_validate(data))
        return sorted(lessons, key=lambda x: x.completed_at)

    def record(self, student_id: str, lesson: CompletedLesson) -> None:
        payload = lesson.model_dump(mode="json") | {"student_id": student_id}
        self.client.collection(COLLECTION).document(
            f"{student_id}__{lesson.lesson_id}"
        ).set(payload)
