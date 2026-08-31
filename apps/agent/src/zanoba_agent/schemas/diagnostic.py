"""What the Diagnostic agent hands to the Objective agent.

The diagram gives this agent its brief in full: *determine what the student
actually knows, based on mastered concepts, partially mastered concepts,
missing prerequisites, misconceptions, appropriate difficulty.* Those five are
the fields below.

Where the Curriculum agent answered "what comes next in the syllabus", this
answers "and can they do it". Neither one alone decides the lesson; the
Objective agent takes both.
"""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field

Standing = Literal["mastered", "partial", "not_started"]

# What to do with the lesson the syllabus proposed. Not a score — a decision
# the Objective agent can act on.
Readiness = Literal["ready", "ready_with_review", "not_ready"]

# Where to pitch the material relative to the curriculum's own default.
Difficulty = Literal["below", "at", "above"]


class ItemStanding(BaseModel):
    """Where the student stands on one lesson, concept or skill."""

    item_id: str
    title: str = ""
    standing: Standing
    score: float | None = Field(
        default=None, ge=0.0, le=1.0, description="Null when never attempted."
    )
    evidence_lesson_ids: list[str] = Field(
        default_factory=list,
        description="Lessons this standing rests on. Empty means not_started.",
    )


class ObservedMisconception(BaseModel):
    """A wrong belief carried forward from the profile, not newly guessed."""

    concept: str
    description: str
    severity: Literal["low", "medium", "high"]
    evidence_lesson_ids: list[str] = Field(default_factory=list)


class ObservedError(BaseModel):
    """A mistake seen more than once."""

    tag: str
    description: str = ""
    count: int = Field(ge=1)


class DiagnosticReport(BaseModel):
    """What the student actually knows, going into this lesson."""

    student_id: str
    subject: str
    level_id: str
    target_item_id: str = Field(description="The lesson the Curriculum agent proposed.")

    mastered: list[ItemStanding] = Field(default_factory=list)
    partially_mastered: list[ItemStanding] = Field(default_factory=list)
    missing_prerequisites: list[ItemStanding] = Field(
        default_factory=list,
        description="Prerequisites of the target with no evidence of mastery.",
    )
    misconceptions: list[ObservedMisconception] = Field(default_factory=list)
    recurring_errors: list[ObservedError] = Field(default_factory=list)

    readiness: Readiness
    recommended_difficulty: Difficulty = Field(
        description="Where to pitch material relative to the curriculum default."
    )
    review_first: list[str] = Field(
        default_factory=list,
        description="Item ids worth revisiting before the new material. Ids only.",
    )

    evidence_lesson_count: int = Field(
        default=0, ge=0, description="How many completed lessons this rests on."
    )
    reason: str = Field(description="Two or three sentences citing the evidence.")
