"""The quality report — what is wrong, how wrong, and what to do about it.

The old report had a status and some issues. That was enough to say "this
failed" and not enough to say what to send back, so a single bad image
regenerated a whole lesson and threw away everything that was right.

Three things changed. There is a score per dimension, because "the material is
weak" is not actionable and "interaction_quality 40, everything else above 80"
is: it names which half of the lesson to redo. There are critical issues called
out separately, because a wrong answer key and a slightly long sentence are not
the same kind of problem. And every issue carries a SCOPE — image, exercise,
item, stage or lesson — which is what makes the repair targeted.

The rule that has not changed: the checker reports, and something else repairs.
A checker that fixes what it finds is a second author, and there is then nobody
checking that.
"""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field

Component = Literal["material", "lesson_plan", "objectives", "blueprint"]

# What to do about an issue. Only material regeneration loops in this build —
# the diagram draws the Quality checker looping back to the Material agent and
# nowhere else. The plan actions are still reported, for a human to act on.
Action = Literal["regenerate_material", "revise_plan", "revise_objectives",
                 "revise_blueprint", "none"]

# How much has to be redone. The narrowest one that fixes the problem is the
# right one: a picture that came back wrong should cost one picture.
Scope = Literal["image", "exercise", "item", "stage", "lesson"]

Category = Literal["linguistic", "pedagogical", "technical"]


class QualityIssue(BaseModel):
    """One thing wrong, and the smallest fix for it."""

    component: Component = "material"
    category: Category = Field(
        default="pedagogical",
        description="Linguistic problems are wrong or unnatural language; "
        "pedagogical ones are material that teaches badly while being correct; "
        "technical ones are missing fields and broken references.",
    )
    problem: str = Field(description="What is wrong, specifically. Not 'quality is low'.")
    action: Action = "regenerate_material"
    severity: Literal["low", "medium", "high", "critical"] = "medium"
    scope: Scope = Field(
        default="item",
        description="How much must be redone to fix this. Narrowest that works.",
    )
    item_id: str = Field(
        default="",
        description="The material item, exercise or image at fault, so revision is "
        "targeted. Without an id the whole package gets redone.",
    )
    fix: str = Field(
        default="",
        description="The instruction the generator needs to put it right.",
    )


class RegenerationTarget(BaseModel):
    """One thing to redo, and what to tell the generator about it."""

    target: str = Field(description="The item, exercise or image id.")
    scope: Scope
    reasons: list[str] = Field(default_factory=list)
    instructions: list[str] = Field(
        default_factory=list,
        description="What to do differently. A regeneration with no new "
        "instruction is the same request again, and gets the same answer.",
    )


class QualityReport(BaseModel):
    """The verdict on one lesson package."""

    status: Literal["PASS", "FAIL"]
    overall_score: int = Field(default=0, ge=0, le=100)
    focus: str = Field(default="", description="Which kind of lesson was graded.")

    # Per-dimension scores. Which ones are meaningful depends on the focus —
    # `evidence_alignment` means nothing for a vocabulary lesson — so they are
    # all optional and the report fills in the ones that apply.
    dimensions: dict[str, int] = Field(
        default_factory=dict,
        description="Score per dimension, 0-100. For a reading lesson: "
        "text_quality, question_quality, evidence_alignment and the rest. For "
        "communication: communication_alignment, authenticity, interaction_quality.",
    )

    issues: list[QualityIssue] = Field(default_factory=list)
    critical_issues: list[QualityIssue] = Field(
        default_factory=list,
        description="Issues that fail the lesson on their own: a wrong answer, a "
        "question the text does not support, English on a target-language slide, "
        "an image that was promised and never made.",
    )
    regeneration_required: bool = False
    regeneration_targets: list[RegenerationTarget] = Field(
        default_factory=list,
        description="What to redo, narrowest scope first. Empty on a pass.",
    )

    checks_run: list[str] = Field(
        default_factory=list, description="Which checks were actually performed."
    )
    calculations_verified: list[dict] = Field(
        default_factory=list,
        description="Results from verify_calculation. Independent of the model that "
        "wrote the answers, and the only calculation evidence that counts.",
    )
    evidence_verified: list[dict] = Field(
        default_factory=list,
        description="Results from verify_reading_evidence. A comprehension answer "
        "counts as supported only when its quote is found in the text.",
    )
    attempt: int = Field(default=1, ge=1)
    reason: str = Field(description="Two or three sentences on the verdict.")
