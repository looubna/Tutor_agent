"""Lesson state — one paid hour, as it happens.

The `lesson_state` box in the diagram, field for field. It is the only state in
the system that is written *during* a lesson rather than before or after it, and
it is what the post-lesson stage reads to update a profile.

The rule that shapes it: **a lesson ends when the paid hour ends.** Not when the
objectives are met, not when the tutor is finished. Unfinished objectives are
recorded as evidence for planning the next lesson, never silently carried into
another hour the student has not bought.
"""

from __future__ import annotations

from datetime import datetime, timedelta
from typing import Literal

from pydantic import BaseModel, Field

LessonStatus = Literal["scheduled", "in_progress", "completed", "cancelled", "no_show"]

# The states the runtime moves through. Named exactly as the brief lists them so
# a transition log can be read against it.
LiveState = Literal[
    "WAITING",
    "STUDENT_DETECTED",
    "GREETING",
    "LESSON_STARTED",
    "TEACHING",
    "QUESTION",
    "STUDENT_RESPONDS",
    "EVALUATE",
    "CONTINUE",
    "EXPLAIN",
    "ADAPT",
    "STUDENT_ABSENT",
    "LESSON_END",
]

ObjectiveStatus = Literal["not_started", "in_progress", "completed", "partial", "unfinished"]


class Presence(BaseModel):
    """What the camera can support saying, and nothing more.

    Deliberately two booleans. The system may observe that a second person is
    visible; it may not conclude who they are. "The student's mother is here" is
    not something a camera knows, and a tutor acting on it would be acting on a
    guess about a real person.
    """

    student_present: bool = False
    additional_person_detected: bool = False
    checked_at: datetime | None = None


class Scheduled(BaseModel):
    start_time: datetime
    duration_minutes: int = 60

    @property
    def end_time(self) -> datetime:
        return self.start_time + timedelta(minutes=self.duration_minutes)


class ObjectiveProgress(BaseModel):
    objective_id: str
    statement: str = ""
    status: ObjectiveStatus = "not_started"
    evidence: list[str] = Field(
        default_factory=list, description="What the student did that shows it."
    )


class StudentInteraction(BaseModel):
    """What the student did. Raw evidence, not yet judged."""

    questions_asked: list[str] = Field(default_factory=list)
    mistakes: list[str] = Field(default_factory=list)
    successful_answers: list[str] = Field(default_factory=list)
    misconceptions_observed: list[str] = Field(default_factory=list)


class TutorActions(BaseModel):
    """What the tutor did, for working out afterwards what helped."""

    explanations_given: int = 0
    additional_examples: int = 0
    # Lines written on the shared whiteboard. This counter was removed while the
    # board was: nothing rendered it, so it measured how often the tutor wrote
    # into the void. The board reaches the student now, so the count means
    # something again.
    whiteboard_actions: int = 0
    # Marks made on the lesson paper. Counted apart from board lines because the
    # two are kept differently: the board is wiped at the end of the hour and
    # the paper is what the student takes away. A class that ends with an
    # unmarked sheet was a lecture.
    paper_marks: int = 0
    material_changes: list[str] = Field(default_factory=list)


class LessonExecution(BaseModel):
    """How the hour actually went, against how it was planned."""

    started_at: datetime | None = None
    ended_at: datetime | None = None
    actual_duration_minutes: int | None = None
    activities_completed: list[str] = Field(default_factory=list)
    topics_covered: list[str] = Field(default_factory=list)
    topics_not_covered: list[str] = Field(default_factory=list)


class Transition(BaseModel):
    """One state change, kept so a lesson can be replayed and argued with."""

    at: datetime
    from_state: LiveState
    to_state: LiveState
    trigger: str


class LessonState(BaseModel):
    """`lesson_state` from the diagram: one booked lesson, start to finish."""

    lesson_id: str
    student_id: str
    tutor_id: str = "zanoba-live-tutor"

    scheduled: Scheduled
    status: LessonStatus = "scheduled"
    live_state: LiveState = "WAITING"
    presence: Presence = Field(default_factory=Presence)

    subject: str = ""
    level_id: str = ""
    target_item_id: str = ""

    objectives: list[ObjectiveProgress] = Field(default_factory=list)
    current_activity_id: str = ""
    execution: LessonExecution = Field(default_factory=LessonExecution)
    interaction: StudentInteraction = Field(default_factory=StudentInteraction)
    tutor_actions: TutorActions = Field(default_factory=TutorActions)
    transitions: list[Transition] = Field(default_factory=list)

    def minutes_remaining(self, now: datetime) -> float:
        """Minutes of paid time left. Negative once the hour is over."""
        return (self.scheduled.end_time - now).total_seconds() / 60.0

    def is_over(self, now: datetime) -> bool:
        return now >= self.scheduled.end_time

    def unfinished_objectives(self) -> list[ObjectiveProgress]:
        """Objectives not completed. Evidence for the next lesson, not a debt."""
        return [o for o in self.objectives if o.status != "completed"]
