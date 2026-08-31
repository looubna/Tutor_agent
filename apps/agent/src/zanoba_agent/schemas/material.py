"""The material package — everything the tutor puts in front of the student.

One package per lesson. Two links matter and both are ids rather than prose: an
item's `activity_id` ties it to the hour, and its `blueprint_slot_id` ties it to
the specification it was written against. The second one is what makes targeted
regeneration possible — a failed item can be rewritten against the same brief,
instead of the whole lesson being re-improvised from the topic.

Exercises carry far more than a prompt and an answer, and the extra fields are
not bookkeeping. `pedagogical_purpose` is there because an exercise that cannot
say what it is for is an exercise generated because the type exists.
`acceptable_answers` is there because open items have more than one right
answer and marking the learner wrong for the second one is worse than not
asking. `constraints` is there so the checker can grade the item against what
was actually asked for.

Exercises also carry a machine-checkable `expression`, so arithmetic can be
verified independently of the model that wrote it — see `material.arithmetic`.
"""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field, model_validator

from .blueprint import (
    ExerciseType, Operation, ReadingSkill, Skill, Stage, VisualSpec)
from .slides import SlideComponent, layout_suits_stage

MaterialKind = Literal[
    "text", "dialogue", "vocabulary", "explanation", "worked_example",
    "exercise_set", "comprehension_questions", "role_play", "image", "diagram",
    "rule_table", "phrase_bank", "summary",
]


class ImageSpec(BaseModel):
    """A picture the lesson needs, and the brief it was made from.

    `spec` is the brief; `prompt` is what the generator was actually sent. They
    are kept apart so the checker can ask the question that matters — does the
    picture that came back satisfy the brief that was written — rather than only
    whether a file exists.
    """

    purpose: str = Field(description="What the picture is for, pedagogically.")
    prompt: str = Field(description="What was sent to the generator.")
    alt_text: str = Field(description="Description for a learner who cannot see it.")
    search_query: str = Field(
        default="",
        description="What to look for in a stock photo library, IN ENGLISH, e.g. "
        '"young woman waving hello in an office". Write THIS rather than copying '
        "the whole visual specification onto every picture — a vocabulary lesson "
        "has twenty of them, and the copying is what makes its output too large "
        "to finish. A picture with a search query and no spec is fine.",
    )
    spec: VisualSpec | None = Field(
        default=None,
        description="The visual specification this was generated from. Present for "
        "anything the Material Planner asked for; the checker grades against it.",
    )
    provider: Literal["pending", "generated", "searched", "failed"] = Field(
        default="pending",
        description="'pending' means specified but not yet produced. Never claim "
        "'generated' for an image that does not exist.",
    )
    url: str = ""
    attempts: int = Field(
        default=0, description="How many times this picture has been regenerated."
    )
    rejected_reasons: list[str] = Field(
        default_factory=list,
        description="Why previous attempts failed the image check. Fed back into "
        "the next prompt, so a regeneration is not the same request again.",
    )


class Exercise(BaseModel):
    """One item, with everything needed to run it, mark it and grade it."""

    id: str
    prompt: str = Field(description="What the learner sees. In the target language.")
    answer: str
    acceptable_answers: list[str] = Field(
        default_factory=list,
        description="Other answers that are also right. Required wherever the task "
        "is open enough to have more than one.",
    )
    instructions: str = Field(
        default="",
        description="What the learner must do, in the target language, as an "
        "imperative: 'Ordne zu.', 'Ergänze die Artikel.'",
    )
    options: list[str] = Field(
        default_factory=list,
        description="The choices, for a multiple-choice or classification item.",
    )
    explanation: str = Field(
        default="",
        description="Why the answer is what it is. For the tutor and the answer key.",
    )
    image: ImageSpec | None = Field(
        default=None,
        description="This item's own picture, for a task where the picture IS the "
        "item: picture-matching, picture-naming, labelling. One per item, never a "
        "shared composite.",
    )

    # ---- what this item is, so it can be validated rather than admired ----
    stage: Stage | None = None
    objective_id: str = ""
    target_grammar: str = ""
    skill: Skill | None = None
    exercise_type: ExerciseType | None = None
    operation: Operation | None = None
    difficulty: str = Field(default="", description='CEFR band, e.g. "A1".')
    pedagogical_purpose: str = Field(
        default="",
        description="What this item is for. Not 'practice' — what the learner "
        "demonstrates by getting it right.",
    )
    constraints: list[str] = Field(
        default_factory=list, description="What this item was required to obey."
    )

    # ---- reading: an answer is only an answer if the text supports it ----
    reading_skill: ReadingSkill = Field(
        default="",
        description="Which reading ability this question exercises.",
    )
    evidence_location: str = Field(
        default="",
        description='Where the answer lives: "paragraph_2", "turn_4", "whole_text".',
    )
    evidence_text: str = Field(
        default="",
        description="The words from the text that support the answer, quoted "
        "VERBATIM. Checked as a substring of the text, so a question whose answer "
        "is not actually in the passage is caught by counting rather than by "
        "reading. Empty for a gist question, whose evidence is the whole text.",
    )

    expression: str = Field(
        default="",
        description="The arithmetic in machine-checkable form, e.g. '3/4 + 1/6'. "
        "Empty when the question is not arithmetic.",
    )
    verification: dict | None = Field(
        default=None,
        description="Filled by verify_calculation. Never written by the model.",
    )


class MaterialItem(BaseModel):
    """One piece of material, tied to the activity and the brief it serves."""

    id: str
    activity_id: str = Field(description="The plan activity this serves.")
    blueprint_slot_id: str = Field(
        default="",
        description="The blueprint slot this was written against. What makes "
        "regeneration targeted rather than a fresh guess at the topic.",
    )
    kind: MaterialKind
    stage: Stage | None = Field(
        default=None, description="The pedagogical stage this belongs to."
    )
    title: str = Field(description="In the target language, as the learner reads it.")
    instruction: str = Field(
        default="",
        description="The imperative line telling the learner what to do, in the "
        "target language: 'Lies den Text.', 'Ordne zu.', 'Sprich nach.'",
    )
    slide: SlideComponent | None = Field(
        default=None,
        description="THE SLIDE. A typed layout — a picture set, a dialogue, a "
        "rule table, a sorting grid — chosen to suit the stage. This is what the "
        "learner sees, and it is what makes the difference between courseware "
        "and a document with photographs in it. Prefer it to `content` always.",
    )
    content: str = Field(
        default="",
        description="Free prose, for the rare item no layout fits. A fallback, "
        "not the default: an item with prose instead of a slide renders as text "
        "in a box, which is what the layouts exist to stop.",
    )
    objective_ids: list[str] = Field(
        default_factory=list, description="The objectives this advances."
    )
    pedagogical_purpose: str = Field(
        default="",
        description="What this achieves, carried through from the blueprint slot.",
    )
    exercises: list[Exercise] = Field(default_factory=list)
    images: list[ImageSpec] = Field(default_factory=list)
    answer_key: str = Field(default="", description="Answers, kept apart from content.")


    @model_validator(mode="after")
    def _an_item_is_a_slide_or_at_least_something(self) -> MaterialItem:
        if self.slide is None and not self.content.strip() and not self.exercises:
            raise ValueError(
                f"item {self.id!r} has no slide, no content and no exercises — "
                "there is nothing to put in front of the learner"
            )
        return self

    @model_validator(mode="after")
    def _the_layout_suits_the_stage(self) -> MaterialItem:
        """A rule table in the warm-up, or a word list in the practice, is a
        layout chosen because it was easy rather than because it teaches."""
        if self.slide is None or self.stage is None:
            return self
        if not layout_suits_stage(self.slide.kind, self.stage):
            from .slides import LAYOUTS_FOR_STAGE

            raise ValueError(
                f"item {self.id!r} is a {self.slide.kind!r} at the "
                f"{self.stage!r} stage. That stage wants one of "
                f"{sorted(LAYOUTS_FOR_STAGE.get(self.stage, []))}"
            )
        return self


class MaterialPackage(BaseModel):
    """Everything produced for one lesson."""

    student_id: str
    subject: str
    domain: Literal["language", "stem"]
    target_language: str = Field(
        default="",
        description='The language the learner-facing text is in, e.g. "german". '
        "Set for language lessons; the purity check reads it.",
    )
    target_item_id: str
    target_item_title: str = Field(
        default="", description="The lesson's own title, for the deck cover."
    )
    items: list[MaterialItem] = Field(min_length=1)
    notes: str = ""

    @model_validator(mode="after")
    def _item_ids_are_unique(self) -> MaterialPackage:
        ids = [i.id for i in self.items]
        if len(set(ids)) != len(ids):
            raise ValueError(f"duplicate material ids: {ids}")
        return self

    @model_validator(mode="after")
    def _exercise_ids_are_unique(self) -> MaterialPackage:
        """Two items with the same exercise id cannot be regenerated separately."""
        ids = [f"{i.id}/{e.id}" for i in self.items for e in i.exercises]
        if len(set(ids)) != len(ids):
            raise ValueError(f"duplicate exercise ids: {sorted(ids)}")
        return self

    def covers(self) -> set[str]:
        return {i.activity_id for i in self.items}

    def slots_filled(self) -> set[str]:
        return {i.blueprint_slot_id for i in self.items if i.blueprint_slot_id}

    def item(self, item_id: str) -> MaterialItem | None:
        return next((i for i in self.items if i.id == item_id), None)
