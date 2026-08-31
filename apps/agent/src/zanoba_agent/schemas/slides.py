"""What a slide IS, rather than what it says.

The material agent used to emit `content: str` — a paragraph of markdown — and
the deck renderer had to guess a layout from it. It could guess about five, so
everything else fell through to "text in a box". That is why a lesson came out
as three consecutive slides titled "Die drei Artikel" carrying fourteen, ten and
eight words, and why the CSS for vocabulary cards, sorting grids and speech
bubbles was written and never once used: the agent had no way to ask for them.

So the agent now chooses a LAYOUT instead of writing prose. Each component below
is one slide of a published lesson, taken from the reference decks:

    PictureSet      six numbered photographs, a blank under each
    Dialogue        turns, one per line, with the scene they happen in
    RuleTable       the three genders in headed columns, cells that are blanks
    VocabCard       das Mädchen · Nomen, Neutrum · Pl. die Mädchen · a photo
    SortingGrid     ten numbered word tiles above three named categories
    TileGrid        scrambled words to build a sentence from
    BubbleExchange  two speech bubbles and the question they model
    ChoiceCards     "Was ist richtig?" — two cards, one right
    QuestionList    numbered items with a rule to write on
    RolePlay        two roles, what each does, the phrases each needs
    Summary         the rule and the phrases, grouped
    WordList        the vocabulary, in two columns

This is the same move AutoPresent found worth 20 points of slide quality:
generating against a typed layout library rather than free-form, because a model
asked for a paragraph writes a paragraph, and a model asked to choose a layout
picks the one that fits.

Every component carries only what its layout needs. That is the point — a
`RuleTable` with no rows is a validation error, where a paragraph that should
have been a table is just a paragraph.
"""

from __future__ import annotations

from typing import Annotated, Literal, Union

from pydantic import BaseModel, Field, model_validator

from .blueprint import VisualSpec

# A cell the learner writes in. Rendered as a rule, never as an empty string,
# so a blank is visibly a blank on the printed page.
BLANK = "___"


class Cell(BaseModel):
    """One cell of a table or one label under a picture."""

    text: str = Field(
        default="",
        description="What is printed. Empty or '___' means the learner fills it in.",
    )
    answer: str = Field(
        default="",
        description="What belongs there, for the answer key. Never printed on "
        "the learner's copy.",
    )
    emphasis: bool = Field(
        default=False, description="Set the cell in the brand colour."
    )

    @property
    def is_blank(self) -> bool:
        return not self.text.strip() or self.text.strip() in {BLANK, "_", "__"}


class Picture(BaseModel):
    """One image on a slide, with what the learner does about it.

    Carries its own brief. The first version of this held only a `url` and the
    generator had nowhere to put the visual specification, so the images were
    made against the old item-level field, the components referenced none of
    them, and every slide rendered without a picture while the bill was paid
    all the same.
    """

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
        description="The brief this picture is made from. The image pipeline "
        "reads it; without one there is nothing to generate.",
    )
    prompt: str = Field(default="", description="What was sent to the generator.")
    purpose: str = Field(default="", description="What it teaches.")
    provider: Literal["pending", "generated", "searched", "failed"] = "pending"
    url: str = Field(default="", description="Filled in by the image pipeline.")
    alt_text: str = ""
    caption: str = Field(
        default="",
        description="Printed under it. Empty means a blank for the learner to "
        "write the word in — which is what a picture-naming task wants.",
    )
    answer: str = Field(default="", description="The word, for the answer key.")
    attempts: int = 0
    rejected_reasons: list[str] = Field(default_factory=list)


class Turn(BaseModel):
    """One line of a dialogue."""

    speaker: str
    line: str
    blanks: list[str] = Field(
        default_factory=list,
        description="Words removed from this line for the learner to supply. "
        "The line itself should contain '___' where each one was.",
    )


# --------------------------------------------------------------- layouts ----

class PictureSet(BaseModel):
    """Numbered photographs, a word or a blank under each.

    The reference decks' most-used slide: six pictures, the learner supplies the
    German. One picture per item and never a composite — a grid cannot be
    numbered and lets the same object appear twice.
    """

    kind: Literal["picture_set"] = "picture_set"
    title: str
    instruction: str = Field(description="Imperative, in the target language.")
    pictures: list[Picture] = Field(min_length=2, max_length=8)
    word_bank: list[str] = Field(
        default_factory=list,
        description="Words to choose from, when the task is matching rather "
        "than naming. Empty when the learner must produce the word unaided.",
    )

    @model_validator(mode="after")
    def _each_picture_is_a_different_thing(self) -> PictureSet:
        answers = [p.answer.strip().lower() for p in self.pictures if p.answer.strip()]
        if len(set(answers)) != len(answers):
            raise ValueError(
                f"two pictures have the same answer {answers}; each item must "
                "have exactly one right answer"
            )
        return self


class Dialogue(BaseModel):
    """An exchange, one turn per line, in the situation it happens in.

    Never a paragraph. A model left to itself writes "Herr Müller: Hallo Tim! Wo
    ist das Buch? Tim: Hallo Herr Müller! ..." as one run of text, which a
    learner cannot follow and which does not look like a conversation.
    """

    kind: Literal["dialogue"] = "dialogue"
    title: str
    instruction: str = ""
    turns: list[Turn] = Field(min_length=2, max_length=8)
    scene: Picture | None = Field(
        default=None, description="Where this happens. Almost always worth having."
    )
    fill_ins: list[Cell] = Field(
        default_factory=list,
        description="The row of blanks under the dialogue, as the reference "
        "lessons print it.",
    )


class RuleTable(BaseModel):
    """A rule as a table. Not paragraphs.

    At A1 a grammar rule fits in one table; if it does not, the lesson is
    teaching two rules and should teach one.
    """

    kind: Literal["rule_table"] = "rule_table"
    title: str
    instruction: str = ""
    headers: list[str] = Field(min_length=2, max_length=4)
    rows: list[list[Cell]] = Field(min_length=1, max_length=6)
    note: str = Field(
        default="",
        description="The one memorable rule under the table, as the reference "
        "prints it: 'Alle deutschen Wörter auf –chen sind Neutrum!'",
    )
    illustration: Picture | None = None

    @model_validator(mode="after")
    def _rows_match_the_headers(self) -> RuleTable:
        wrong = [i for i, row in enumerate(self.rows) if len(row) != len(self.headers)]
        if wrong:
            raise ValueError(
                f"rows {wrong} do not have {len(self.headers)} cells; a table "
                "with ragged rows renders as a broken grid"
            )
        return self


class VocabCard(BaseModel):
    """One word, taught whole: article, plural, part of speech, picture, example.

    "die Frage, Pl. die Fragen" is the vocabulary item; "Frage" is half of it.
    """

    kind: Literal["vocab_card"] = "vocab_card"
    title: str = ""
    instruction: str = ""
    word: str = Field(description="With its article, where it has one.")
    part_of_speech: str = Field(
        default="", description="'Nomen, Femininum' — as the reference prints it."
    )
    plural: str = Field(default="", description="'Pl.: die Fragen'.")
    example: str = Field(default="", description="One natural sentence using it.")
    picture: Picture | None = None
    note: str = ""


class SortingGrid(BaseModel):
    """Numbered word tiles, and the categories they sort into.

    The reference's ten classroom nouns above three gender columns. It is the
    noticing slide and the recycling slide both.
    """

    kind: Literal["sorting_grid"] = "sorting_grid"
    title: str
    instruction: str
    tiles: list[str] = Field(min_length=4, max_length=12)
    categories: list[str] = Field(min_length=2, max_length=4)
    answers: dict[str, str] = Field(
        default_factory=dict,
        description="tile -> category, for the answer key only.",
    )


class TileGrid(BaseModel):
    """Scrambled words to build sentences from."""

    kind: Literal["tile_grid"] = "tile_grid"
    title: str
    instruction: str
    rows: list[list[str]] = Field(min_length=1, max_length=6)
    answers: list[str] = Field(
        default_factory=list, description="The sentence each row makes."
    )


class BubbleExchange(BaseModel):
    """Two speech bubbles: the model exchange the learner will imitate."""

    kind: Literal["bubble_exchange"] = "bubble_exchange"
    title: str = ""
    instruction: str = ""
    left: str = Field(description="What the first speaker says.")
    right: str = Field(description="What the second speaker says.")
    picture: Picture | None = None
    prompt: str = Field(
        default="",
        description="The line under it telling the learner to do the same, e.g. "
        "'Frage und antworte!'",
    )


class ChoiceCards(BaseModel):
    """"Was ist richtig?" — two to four cards, one of them correct."""

    kind: Literal["choice_cards"] = "choice_cards"
    title: str
    instruction: str
    question: str = ""
    options: list[Cell] = Field(min_length=2, max_length=4)
    answer: str = Field(description="The text of the correct option.")
    picture: Picture | None = None

    @model_validator(mode="after")
    def _the_answer_is_one_of_the_options(self) -> ChoiceCards:
        texts = [o.text.strip() for o in self.options]
        if self.answer.strip() not in texts:
            raise ValueError(
                f"the answer {self.answer!r} is not among the options {texts} — "
                "the item is unanswerable as printed"
            )
        return self


class QuestionList(BaseModel):
    """Numbered items with a rule to write the answer on."""

    kind: Literal["question_list"] = "question_list"
    title: str
    instruction: str
    items: list[Cell] = Field(min_length=2, max_length=8)
    worked_first: str = Field(
        default="",
        description="The first item done, as an example. The reference prints one "
        "on every transformation task.",
    )
    word_bank: list[str] = Field(default_factory=list)


class RolePlay(BaseModel):
    """Two roles, what each has to do, and the phrases each needs."""

    kind: Literal["role_play"] = "role_play"
    title: str
    instruction: str
    role_a: str = Field(description="Who they are, e.g. 'Die Lehrerin'.")
    role_a_task: str = Field(description="What they do.")
    role_a_phrases: list[str] = Field(default_factory=list)
    role_b: str
    role_b_task: str
    role_b_phrases: list[str] = Field(default_factory=list)
    picture: Picture | None = None


class Summary(BaseModel):
    """The rule and the phrases, grouped under headings."""

    kind: Literal["summary"] = "summary"
    title: str
    instruction: str = ""
    groups: list[dict] = Field(
        min_length=1,
        description="[{heading, points: [...]}] — the shape of the reference's "
        "Zusammenfassung slide.",
    )


class WordList(BaseModel):
    """The lesson's vocabulary, in two columns, as the reference closes on."""

    kind: Literal["word_list"] = "word_list"
    title: str
    instruction: str = ""
    words: list[str] = Field(min_length=4, max_length=30)


SlideComponent = Annotated[
    Union[PictureSet, Dialogue, RuleTable, VocabCard, SortingGrid, TileGrid,
          BubbleExchange, ChoiceCards, QuestionList, RolePlay, Summary, WordList],
    Field(discriminator="kind"),
]

# Which layouts suit which blueprint stage. The checker uses it to catch a
# noticing stage rendered as a wall of text, which is the failure that made a
# lesson look like a document with pictures instead of courseware.
LAYOUTS_FOR_STAGE: dict[str, set[str]] = {
    "warm-up": {"picture_set", "sorting_grid", "bubble_exchange", "question_list"},
    "context": {"dialogue", "bubble_exchange", "picture_set"},
    "situation": {"dialogue", "bubble_exchange"},
    "encounter": {"dialogue", "bubble_exchange", "picture_set"},
    "noticing": {"sorting_grid", "picture_set", "rule_table", "question_list"},
    "meaning": {"picture_set", "vocab_card", "question_list"},
    "comprehension": {"question_list", "choice_cards", "picture_set"},
    "language-resource": {"vocab_card", "word_list", "rule_table", "picture_set"},
    "pronunciation": {"tile_grid", "word_list", "vocab_card"},
    "explanation": {"rule_table", "vocab_card", "bubble_exchange"},
    "recognition": {"choice_cards", "picture_set", "sorting_grid"},
    "controlled-practice": {"question_list", "choice_cards", "sorting_grid",
                            "dialogue", "tile_grid"},
    "retrieval": {"picture_set", "question_list", "tile_grid"},
    "guided-practice": {"tile_grid", "question_list", "bubble_exchange"},
    "guided-interaction": {"bubble_exchange", "role_play", "question_list"},
    "contextual-use": {"tile_grid", "question_list", "bubble_exchange"},
    "communicative-practice": {"role_play", "bubble_exchange", "picture_set"},
    "communicative-task": {"role_play", "picture_set", "bubble_exchange"},
    "communicative-use": {"role_play", "bubble_exchange", "picture_set"},
    "independent-communication": {"role_play", "question_list"},
    "recycling": {"sorting_grid", "picture_set", "question_list"},
    "pre-reading": {"picture_set", "bubble_exchange", "question_list"},
    "vocabulary-preparation": {"question_list", "picture_set", "vocab_card"},
    "gist": {"choice_cards", "question_list"},
    "detail": {"question_list", "choice_cards", "sorting_grid"},
    "inference": {"choice_cards", "question_list"},
    "strategy": {"question_list", "sorting_grid", "tile_grid"},
    "vocabulary-in-context": {"choice_cards", "question_list", "vocab_card"},
    "post-reading": {"role_play", "question_list", "bubble_exchange"},
    "review": {"summary", "word_list", "rule_table"},
    "reflection": {"summary", "question_list"},
    "final-check": {"question_list", "choice_cards", "summary"},
}


def layout_suits_stage(layout: str, stage: str) -> bool:
    """Is this a sensible layout for this stage? Unknown stages allow anything."""
    allowed = LAYOUTS_FOR_STAGE.get(stage)
    return True if allowed is None else layout in allowed
