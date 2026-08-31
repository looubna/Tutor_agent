"""What the Objective agent produces: the goals for one paid hour.

The diagram states the contract precisely — *create 1-3 achievable learning
objectives for a single 1h lesson*, and they must be specific, measurable,
appropriate for the student's grade, appropriate for their actual level, and
achievable within the hour.

Four of those five are judgement the model makes. The two that can be checked
mechanically are checked here: **how many** objectives, and **whether they fit
the hour**. A model that is merely asked to be realistic about time will
sometimes not be; a validator is not optional about it.
"""

from __future__ import annotations

from pydantic import BaseModel, Field, model_validator

from .curriculum import LanguageFocus

# A booked lesson is 60 minutes, but objectives do not get all of it. A lesson
# opens with retrieval and closes with a recap, and neither is an objective —
# they are what makes the objectives stick. Ten minutes is the floor for both.
LESSON_MINUTES = 60
TEACHING_MINUTES = 50

# Below five minutes an objective is a step inside another objective, not a
# goal for the hour.
MIN_OBJECTIVE_MINUTES = 5


class LessonObjective(BaseModel):
    """One thing the student will be able to do by the end of the hour."""

    id: str = Field(description='Short local id: "o1", "o2", "o3".')
    statement: str = Field(
        description='A can-do statement in the student\'s voice, e.g. "I can name '
        'the three genders of German nouns."'
    )
    measurable_by: str = Field(
        description="How the tutor will know it was met, concretely. An objective "
        "nobody can check is not measurable."
    )
    covers_item_id: str = Field(
        description="The curriculum lesson or unit id this serves."
    )
    source_objective: str = Field(
        default="",
        description="The curriculum objective this narrows, copied verbatim. Empty "
        "for a review objective, which comes from diagnosed gaps instead.",
    )
    is_review: bool = Field(
        default=False,
        description="True when this closes a gap the Diagnostic agent found, "
        "rather than teaching the new lesson.",
    )
    estimated_minutes: int = Field(
        ge=MIN_OBJECTIVE_MINUTES,
        le=TEACHING_MINUTES,
        description="Teaching time this needs, honestly estimated.",
    )


class LessonObjectives(BaseModel):
    """The objectives for one lesson, with what was deliberately left out."""

    student_id: str
    subject: str
    level_id: str
    target_item_id: str
    focus: LanguageFocus | None = Field(
        default=None, description="Dominant skill for a language lesson."
    )

    objectives: list[LessonObjective] = Field(
        min_length=1,
        max_length=3,
        description="Between one and three. Three shallow objectives teach less "
        "than one that lands.",
    )

    deferred: list[str] = Field(
        default_factory=list,
        description="Curriculum objectives deliberately not attempted this hour. "
        "Evidence for planning the next lesson, not a failure.",
    )
    reason: str = Field(description="Two or three sentences on why these, and why now.")

    @property
    def total_minutes(self) -> int:
        return sum(x.estimated_minutes for x in self.objectives)

    @model_validator(mode="after")
    def _fits_the_hour(self) -> LessonObjectives:
        """The hour is fixed. Objectives that do not fit it are not achievable.

        A lesson ends when the paid hour ends, whether or not the plan was
        finished, so a plan that needs 70 minutes is a plan to leave the student
        mid-explanation.
        """
        if self.total_minutes > TEACHING_MINUTES:
            raise ValueError(
                f"objectives need {self.total_minutes} minutes of teaching but only "
                f"{TEACHING_MINUTES} are available in a {LESSON_MINUTES}-minute lesson "
                "(the rest is retrieval and recap)"
            )
        ids = [x.id for x in self.objectives]
        if len(set(ids)) != len(ids):
            raise ValueError(f"duplicate objective ids: {ids}")
        return self
