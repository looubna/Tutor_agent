"""What the Curriculum agent hands to the Diagnostic agent.

The diagram gives this agent one job — *"what should normally be taught next"*
— and the word doing the work is **normally**. This answer is about the
syllabus, not the student: it is where an on-track learner would be. Whether
this particular student is ready is the Diagnostic agent's question, and
keeping the two apart is why the pipeline is sequential rather than one big
agent.
"""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field

from ..schemas.curriculum import LanguageFocus


class CurriculumPlacement(BaseModel):
    """Where the syllabus says this student should be."""

    student_id: str = Field(
        description=(
            "Who this placement is for. Carried explicitly because downstream "
            "agents receive this object and nothing else — without it the "
            "Diagnostic agent has no student to look up."
        )
    )
    subject: str
    domain: Literal["language", "stem"]
    level_id: str = Field(description='Level or program id, e.g. "a1-1".')

    next_item_id: str = Field(
        description="Id of the lesson or unit that comes next. Must exist in the curriculum."
    )
    next_item_title: str
    granularity: Literal["lesson", "unit"] = Field(
        description="'unit' means no lessons are authored beneath it yet."
    )
    focus: LanguageFocus | None = Field(
        default=None, description="Dominant skill for a language lesson; null for STEM."
    )
    objectives: list[str] = Field(
        default_factory=list,
        description="The curriculum's own objectives. Copied, never invented.",
    )

    prerequisites: list[str] = Field(
        default_factory=list, description="Item ids that should come first."
    )
    unmet_prerequisites: list[str] = Field(
        default_factory=list,
        description="Prerequisites with no completion on record. Evidence for the Diagnostic agent, not a verdict.",
    )

    completed_count: int = Field(
        default=0, description="How many items in this level the student has finished."
    )
    total_count: int = Field(default=0, description="How many items the level contains.")

    reason: str = Field(
        description="One or two sentences on why this item is next, citing the syllabus."
    )
