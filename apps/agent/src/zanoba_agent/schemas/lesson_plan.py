"""The lesson plan — a 60-minute hour, broken into activities.

Both planners produce this. The diagram gives each its own phase list, and the
brief gives the language planner four different lists depending on focus, so
the shape below carries the phase as a label rather than fixing a set of fields
that only one domain would use.

Two things are checked mechanically, because a plan that fails either is not a
plan: the hour has to add up, and every objective has to be served by at least
one activity. An objective nothing teaches is the failure this catches — it
reads perfectly well and quietly does not happen.
"""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field, model_validator

from ..material.rubric import (
    ONE_OF_REQUIRED_BY_FOCUS, REQUIRED_STAGES_BY_FOCUS, STAGES_BY_FOCUS)
from .curriculum import LanguageFocus
from .objectives import LESSON_MINUTES, LessonObjective

# A plan must fill the paid hour without exceeding it. The floor stops a plan
# that quietly hands back ten minutes the student paid for.
MIN_PLAN_MINUTES = 50

# The phases each focus runs through. Read straight off the pedagogical rubric
# rather than written out again here, because the Lesson Planner and the
# Material Planner have to be naming the same stages — when they were two
# separate lists, the plan said "application" and the blueprint said
# "guided-practice", and nothing downstream could tell they meant the same thing.
#
# Which of these a given lesson actually runs is the planner's decision. The
# rubric marks the few whose absence means the lesson is not teaching its focus.
LANGUAGE_PHASES: dict[str, list[str]] = {
    focus: sorted(stages, key=lambda s: stages[s]["order"])
    for focus, stages in STAGES_BY_FOCUS.items()
}

STEM_PHASES: list[str] = [
    "warm-up", "prerequisite-review", "concept-explanation", "worked-examples",
    "guided-practice", "independent-practice", "assessment", "recap",
]


class LessonActivity(BaseModel):
    """One block of the hour."""

    id: str = Field(description='Short local id: "a1", "a2".')
    phase: str = Field(
        description="Which phase of the lesson structure this is, e.g. 'retrieval'."
    )
    title: str
    description: str = Field(
        description="What the tutor and student actually do. Concrete enough to run."
    )
    minutes: int = Field(ge=2, le=LESSON_MINUTES)
    serves_objective_ids: list[str] = Field(
        default_factory=list,
        description="Objective ids this advances. Empty is allowed only for "
        "warm-up and recap, which serve the hour rather than one objective.",
    )
    material_needed: str = Field(
        default="",
        description="What the Material agent must produce for this activity. "
        "Empty when the tutor needs nothing prepared.",
    )
    is_optional: bool = Field(
        default=False,
        description="True for activities to drop first if the hour runs short.",
    )


class LessonPlan(BaseModel):
    """An adaptive plan for one booked 60-minute lesson."""

    student_id: str
    subject: str
    domain: Literal["language", "stem"]
    level_id: str
    target_item_id: str
    focus: LanguageFocus | None = Field(
        default=None, description="Dominant skill for a language lesson; null for STEM."
    )

    objectives: list[LessonObjective] = Field(
        min_length=1,
        description="Carried forward unchanged from the Objective agent.",
    )
    activities: list[LessonActivity] = Field(min_length=2)

    adaptations: list[str] = Field(
        default_factory=list,
        description="What was changed for this student and why, citing the diagnosis.",
    )
    reason: str = Field(description="Two or three sentences on the shape of the hour.")

    @property
    def total_minutes(self) -> int:
        return sum(a.minutes for a in self.activities)

    @model_validator(mode="after")
    def _the_hour_adds_up(self) -> LessonPlan:
        total = self.total_minutes
        if total > LESSON_MINUTES:
            raise ValueError(
                f"plan runs {total} minutes; the lesson is {LESSON_MINUTES} and ends "
                "on time whether or not the plan is finished"
            )
        if total < MIN_PLAN_MINUTES:
            raise ValueError(
                f"plan fills only {total} of {LESSON_MINUTES} paid minutes"
            )
        return self

    @model_validator(mode="after")
    def _every_objective_is_taught(self) -> LessonPlan:
        """An objective no activity serves will not happen.

        This is the quiet failure worth catching: the plan lists the objective
        at the top, reads fine, and contains nothing that teaches it.
        """
        served = {oid for a in self.activities for oid in a.serves_objective_ids}
        missing = [o.id for o in self.objectives if o.id not in served]
        if missing:
            raise ValueError(
                f"objectives {missing} have no activity serving them"
            )
        return self

    @model_validator(mode="after")
    def _activity_ids_are_unique(self) -> LessonPlan:
        ids = [a.id for a in self.activities]
        if len(set(ids)) != len(ids):
            raise ValueError(f"duplicate activity ids: {ids}")
        return self
