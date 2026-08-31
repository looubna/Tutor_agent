"""Student profile — what one learner currently understands.

The diagram draws two profile stores beside the two curricula:
`Student Profile` for the general case, and `Language learner Profile` for the
extra structure a language needs (four skills, grammar and vocabulary tracked
apart, a native language to explain in).

The rule that shapes every model here: **mastery is never fabricated.** A score
only exists because attempts produced it, so `MasteryEntry` carries the
evidence alongside the number and refuses to hold a score with nothing behind
it. An agent that wants to claim a student knows something has to point at when
they showed it.

The profile is the *current* picture and is updated in place. The lessons that
produced it are immutable history and live elsewhere.
"""

from __future__ import annotations

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field, model_validator

from .curriculum import CEFRBand, LanguageFocus

Severity = Literal["low", "medium", "high"]

# The four skills CEFR reports separately. Distinct from LanguageFocus: you can
# book a lesson focused on reading, but nobody books a "listening lesson" here
# — listening is assessed, not timetabled.
LanguageSkill = Literal["reading", "listening", "speaking", "writing"]


class MasteryEntry(BaseModel):
    """How well one skill or concept is held, and the evidence for saying so."""

    item_id: str = Field(description="Concept id, skill id or lesson id this scores.")
    score: float = Field(ge=0.0, le=1.0, description="0-1 confidence the student holds it.")
    attempts: int = Field(default=0, ge=0)
    correct: int = Field(default=0, ge=0)
    last_seen_at: datetime | None = None
    evidence_lesson_ids: list[str] = Field(
        default_factory=list,
        description="Lessons this score was derived from. Empty only when score is 0.",
    )

    @model_validator(mode="after")
    def _score_needs_evidence(self) -> MasteryEntry:
        """A non-zero score with no attempts behind it is a fabrication.

        This is the one invariant worth enforcing in the type rather than in a
        prompt: a model that is told not to invent mastery can still do it, but
        it cannot get an invented number past this.
        """
        if self.score > 0 and self.attempts == 0 and not self.evidence_lesson_ids:
            raise ValueError(
                f"mastery for {self.item_id!r} has score {self.score} but no attempts "
                "and no evidence lessons — mastery must come from evidence"
            )
        if self.correct > self.attempts:
            raise ValueError(
                f"mastery for {self.item_id!r} has {self.correct} correct out of "
                f"{self.attempts} attempts"
            )
        return self


class Misconception(BaseModel):
    """A specific wrong belief, not a general weakness."""

    concept: str = Field(description="What it is about, e.g. 'equivalent-fractions'.")
    description: str = Field(description="The wrong belief itself, stated plainly.")
    severity: Severity = "medium"
    first_seen_at: datetime | None = None
    evidence_lesson_ids: list[str] = Field(default_factory=list)


class RecurringError(BaseModel):
    """A mistake seen more than once, with a count that justifies 'recurring'."""

    tag: str = Field(description="Short stable id, e.g. 'der-vs-die'.")
    description: str = ""
    count: int = Field(default=1, ge=1)
    examples: list[str] = Field(default_factory=list, max_length=5)


class LearningPreferences(BaseModel):
    """How this student likes to be taught. Stated, not inferred."""

    preferred_explanation: str = ""
    correction_style: Literal["immediate", "delayed", "end-of-activity", ""] = ""
    likes_conversation: bool | None = None
    likes_visual_material: bool | None = None
    preferred_topics: list[str] = Field(default_factory=list)


class SubjectLearning(BaseModel):
    """Everything known about one student in one subject."""

    subject: str
    overall_level: str = Field(default="", description='Level id, e.g. "a1-1".')
    mastery: list[MasteryEntry] = Field(default_factory=list)
    misconceptions: list[Misconception] = Field(default_factory=list)
    recurring_errors: list[RecurringError] = Field(default_factory=list)
    strengths: list[str] = Field(default_factory=list)
    weaknesses: list[str] = Field(default_factory=list)


class Demographics(BaseModel):
    age: int | None = None
    grade: str = ""


class StudentProfile(BaseModel):
    """`Student Profile` from the diagram. One document per student."""

    student_id: str
    demographics: Demographics = Field(default_factory=Demographics)
    school_system: str = Field(default="", description='e.g. "FR", "US".')
    learning: list[SubjectLearning] = Field(default_factory=list)
    learning_preferences: LearningPreferences = Field(default_factory=LearningPreferences)
    updated_at: datetime | None = None

    def for_subject(self, subject: str) -> SubjectLearning | None:
        return next((x for x in self.learning if x.subject == subject), None)


class SkillLevel(BaseModel):
    """One CEFR skill and where the student sits in it."""

    skill: LanguageSkill
    band: CEFRBand
    evidence_lesson_ids: list[str] = Field(default_factory=list)


class LanguageKnowledge(BaseModel):
    """Grammar or vocabulary, tracked apart because they move independently."""

    area: LanguageFocus
    overall_mastery: float = Field(default=0.0, ge=0.0, le=1.0)
    topics: list[MasteryEntry] = Field(default_factory=list)


class LanguageGoals(BaseModel):
    short_term: list[str] = Field(default_factory=list)
    long_term: list[str] = Field(default_factory=list)


class LanguageLearnerProfile(BaseModel):
    """`Language learner Profile` from the diagram.

    Sits beside `StudentProfile` rather than inside it: the four CEFR skills, a
    native language to fall back on and per-area knowledge have no meaning for
    maths, and folding them in would leave most of the document empty.
    """

    student_id: str
    subject: str = Field(description='The language being learnt, e.g. "german".')
    native_language: str = ""
    target_language: str = ""
    overall_band: CEFRBand | None = None
    current_level_id: str = Field(default="", description='e.g. "a1-1".')
    skills: list[SkillLevel] = Field(default_factory=list)
    knowledge: list[LanguageKnowledge] = Field(default_factory=list)
    misconceptions: list[Misconception] = Field(default_factory=list)
    recurring_errors: list[RecurringError] = Field(default_factory=list)
    strengths: list[str] = Field(default_factory=list)
    weaknesses: list[str] = Field(default_factory=list)
    learning_preferences: LearningPreferences = Field(default_factory=LearningPreferences)
    goals: LanguageGoals = Field(default_factory=LanguageGoals)
    updated_at: datetime | None = None
