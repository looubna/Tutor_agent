"""The material blueprint: what material is needed, and why, before any exists.

The defect this exists to fix is architectural. The old pipeline went straight
from "the topic is definite articles" to "write exercises and generate images",
and everything wrong with the output followed from that one jump. With nothing
between the topic and the writing, the model reached for the exercise types it
knows best — three gap-fills and a quiz — asked for a picture beside each because
a picture was possible, and produced material that matched the topic without
teaching it.

A blueprint is a specification the generator writes *against*. It fixes the
stage, the pedagogical goal, the cognitive operation, the item count, the
vocabulary the items may use and what counts as success, before a single
sentence is authored. Two things follow that could not before: the plan can be
validated as a plan — progression, variety, image budget, objective coverage,
support fade and recycling are all checkable while it is still cheap to change —
and regeneration becomes targeted, because a failed item has a specification to
be rewritten against rather than a topic to be re-improvised from.

One blueprint, three shapes. A grammar lesson is organised around a form, a
communication lesson around a task the learner must be able to perform, and a
vocabulary lesson around a set of words the learner must be able to get back
without being shown them. They share the machinery and differ in what they are
validated for, which is why `focus` is read by almost every validator below.

The image half is the same argument. `VisualSpec` exists because "generate an
image for the word X" is not a brief, and what came back was a cartoon owl in
front of a blank chalkboard.
"""

from __future__ import annotations

import re
from collections import Counter
from typing import Literal

from pydantic import BaseModel, Field, model_validator

from ..material.rubric import (
    EXERCISE_TYPES,
    MAX_EXERCISE_ITEMS_PER_LESSON,
    MAX_IMAGES_PER_LESSON,
    MAX_NEW_ITEMS_BY_BAND,
    MAX_OPERATION_SHARE,
    MAX_SKILL_JUMP,
    MAX_SLOTS_PER_STAGE,
    MIN_DISTINCT_OPERATIONS,
    MIN_PRODUCTIVE_DIRECTIONS,
    MAX_QUESTIONS_BY_BAND,
    NO_IMAGE_STAGES,
    ONE_IMAGE_PER_ITEM_TYPES,
    MIN_DISTINCT_READING_SKILLS,
    MIN_EXERCISE_ITEMS_PER_LESSON,
    MIN_LESSON_MINUTES,
    MIN_RECYCLED_SHARE,
    MIN_SLOTS_PER_LESSON,
    NEW_WORD_BUDGET_BY_BAND,
    ONE_OF_REQUIRED_BY_FOCUS,
    READING_STAGES,
    TEXT_LENGTH_BY_BAND,
    TEXT_TYPES_BY_BAND,
    PRODUCTIVE_DIRECTIONS,
    REQUIRED_STAGES_BY_FOCUS,
    SKILL_LADDER,
    STAGES_BY_FOCUS,
    SUPPORT_LEVELS,
    UNDEPICTABLE,
    operation_variety_exempt,
    stage_order,
    stages_for,
)

Focus = Literal["grammar", "communication", "vocabulary", "reading"]

Stage = Literal[
    # grammar
    "warm-up", "context", "noticing", "explanation", "controlled-practice",
    "guided-practice", "communicative-practice", "review", "final-check",
    # communication
    "situation", "comprehension", "language-resource", "guided-interaction",
    "communicative-task", "independent-communication", "reflection",
    # vocabulary
    "encounter", "meaning", "pronunciation", "recognition", "retrieval",
    "contextual-use", "communicative-use", "recycling",
    # reading
    "pre-reading", "vocabulary-preparation", "gist", "detail", "inference",
    "strategy", "vocabulary-in-context", "post-reading",
]

ReadingSkill = Literal[
    "", "skimming", "scanning", "main_idea", "specific_detail", "sequencing",
    "reference", "context_inference", "inference", "prediction",
    "text_structure", "writer_purpose", "fact_opinion", "summarising",
]

VocabularySupport = Literal["essential", "useful", "inferable", "unnecessary"]

Skill = Literal[
    "recognition", "comprehension", "controlled_production",
    "guided_production", "communication",
]

Operation = Literal[
    "identify", "choose", "match", "classify", "complete",
    "transform", "reorder", "correct", "produce", "respond",
]

ExerciseType = Literal[
    "matching", "labelling", "multiple_choice", "true_false", "classification",
    "odd_one_out", "gap_fill", "transformation", "sentence_building",
    "error_correction", "dialogue_response", "role_play", "information_gap",
    "guessing_game", "open_production",
    "dialogue_completion", "phrase_function_match", "response_choice",
    "dialogue_ordering", "substitution", "interview", "problem_solving",
    "dictation", "picture_description", "find_differences",
    "picture_word_match", "picture_naming", "listen_repeat", "minimal_pair",
]

PresentationKind = Literal[
    "dialogue", "reading_text", "rule_table", "example_set", "vocabulary_list",
    "phrase_bank", "summary", "model_exchange", "pronunciation_table",
]

SupportLevel = Literal["high", "medium", "low", "independent"]

RetrievalDirection = Literal[
    "", "word_to_meaning", "picture_to_word", "meaning_to_word", "context_to_word",
    "situation_to_word", "word_to_sentence", "sentence_to_meaning",
    "function_to_phrase",
]

VisualType = Literal[
    "", "direct_concept", "context_scene", "contrast", "categorisation",
    "communicative_scene",
]

LexicalType = Literal["word", "collocation", "fixed_expression", "functional_phrase"]


# ------------------------------------------------------------- the parts ----

class VisualSpec(BaseModel):
    """A brief for one picture, written before anything is generated.

    Optimised for pedagogical clarity, not artistic quality. For a vocabulary
    target the learner has to identify the concept in under a second and be
    unable to read the picture as anything else — a beautiful image of a garden
    that could also be a park has failed at the one job it had.

    A communicative scene is the exception, and the only one. There the picture
    is what the learner has to talk ABOUT, and withholding something is what
    creates the question worth asking. `ambiguity_tolerance: "intentional"` says
    that out loud so the checker grades it as a feature rather than a defect.
    """

    target_concept: str = Field(
        description='The single thing the picture must convey, e.g. "Garten", or '
        "the situation a communicative scene shows. Never a grammatical "
        "abstraction — no picture shows 'the definite article'."
    )
    visual_type: VisualType = Field(
        default="direct_concept",
        description="What job the picture does. Not every image is a labelled "
        "object; a context scene, a contrast pair and a scene to talk about are "
        "different requests.",
    )
    language_level: str = Field(description='CEFR band, e.g. "A1".')
    pedagogical_purpose: str = Field(
        description="What the learner does with it, e.g. 'vocabulary retrieval: "
        "the learner names this without being given the word'."
    )
    visual_goal: str = Field(
        default="make the target concept immediately identifiable",
        description="What the picture must achieve for the learner.",
    )
    main_subject: str = Field(description="What dominates the frame.")
    composition: str = Field(
        description="Framing, viewpoint, background. Plain background unless the "
        "setting is itself the target."
    )
    complexity: Literal["low", "medium"] = Field(
        default="low",
        description="A1-A2 material is 'low': one subject, plain ground, nothing "
        "else — unless it is a communicative scene, which needs enough in it to "
        "be worth asking about.",
    )
    must_show: list[str] = Field(
        default_factory=list, description="Elements without which the picture fails."
    )
    must_not_show: list[str] = Field(
        default_factory=list,
        description="Anything that would compete for the reading. For a picture of "
        "a Garten: a house, a park bench, people.",
    )
    text_allowed: bool = Field(
        default=False,
        description="Almost always false. Text in the picture does the learner's "
        "work for them and generators render foreign words wrongly.",
    )
    ambiguity_tolerance: Literal["very_low", "low", "medium", "intentional"] = Field(
        default="very_low",
        description="'very_low' for a vocabulary target the learner must name. "
        "'intentional' ONLY for a communicative scene, where what the picture "
        "withholds is what the learner has to ask about.",
    )

    # ---- what this picture is supposed to make happen -----------------------
    communication_goal: str = Field(
        default="",
        description="For a communicative scene: what the learner must accomplish "
        "by talking about it. Required when ambiguity is intentional.",
    )
    student_should_notice: list[str] = Field(
        default_factory=list,
        description="What the learner is meant to see in it.",
    )
    student_should_communicate: list[str] = Field(
        default_factory=list,
        description="What the learner must say because of it. The test of a "
        "communicative image: if this list is empty, the picture is decoration.",
    )
    style: str = Field(
        default="",
        description="Left empty to inherit the deck's one house style. Set it only "
        "when this picture genuinely needs to differ.",
    )

    # ---- where the picture comes from --------------------------------------
    source: Literal["auto", "photo_search", "generate"] = Field(
        default="auto",
        description="Where to get the picture. 'photo_search' looks for a real "
        "photograph in a stock library; 'generate' asks an image model for one; "
        "'auto' searches first and generates only if nothing usable comes back. "
        "Prefer a real photograph for anything that exists in the world — a "
        "table, a station, a flag, two people at a counter. Generation is for "
        "the staged situation with the exact props a lesson needs, and for a "
        "concept no photographer has bothered to shoot.",
    )
    search_query: str = Field(
        default="",
        description="What to type into a stock photo library, IN ENGLISH, "
        'e.g. "wooden dining table plain background" or "young woman greeting a '
        'man in an office". Photo libraries are indexed in English, so a German '
        "lesson still searches in English. Left empty, one is composed from "
        "main_subject and target_concept, which is usually worse.",
    )

    @model_validator(mode="after")
    def _a_direct_concept_shows_one_thing(self) -> VisualSpec:
        """One picture, one thing. "Buch" is a book and nothing else.

        The rule exists because a composite is so much easier to ask for than a
        set of separate pictures, and it fails in a way that is invisible until
        a learner is looking at it: a six-panel grid of classroom objects for a
        five-word matching task came back with two identical chairs in it and
        printed English on one of the books. Neither is fixable by prompting
        harder — the request itself was wrong.
        """
        if self.visual_type != "direct_concept":
            return self
        concept = self.target_concept.strip().lower()
        plural_hint = any(
            term in concept for term in
            ("objects", "items", "things", "words", "prompts", "set of",
             "collection", "various", "several", "different", "grid", "labeled",
             "labelled", "collage")
        )
        if plural_hint:
            raise ValueError(
                f"a direct_concept picture must show ONE thing, but "
                f"{self.target_concept!r} names a set. Give each item its own "
                "picture of its own single object — a book is a picture of a "
                "book, a chair is a picture of a chair — rather than one image "
                "of everything."
            )
        if self.complexity != "low":
            raise ValueError(
                f"a direct_concept picture of {self.target_concept!r} must be "
                "'low' complexity: one subject, plain ground, nothing competing."
            )
        return self

    @model_validator(mode="after")
    def _intentional_ambiguity_is_earned(self) -> VisualSpec:
        if self.ambiguity_tolerance == "intentional":
            if self.visual_type != "communicative_scene":
                raise ValueError(
                    f"ambiguity_tolerance 'intentional' on a {self.visual_type!r} "
                    "image. Only a communicative scene earns ambiguity; anywhere "
                    "else it is an unanswerable question for the learner."
                )
            if not self.communication_goal.strip():
                raise ValueError(
                    "an intentionally ambiguous picture with no communication_goal "
                    "is just an unclear picture"
                )
            if not self.student_should_communicate:
                raise ValueError(
                    "student_should_communicate is empty, so nothing says what the "
                    "learner has to say because of this image"
                )
        return self

    def to_prompt(self) -> str:
        """Render the specification as the prompt an image model receives.

        Built from the specification rather than written freehand, so what was
        asked for and what gets checked are the same document.
        """
        parts = [f"{self.main_subject}.", f"Composition: {self.composition}."]
        if self.must_show:
            parts.append("Must be visible: " + ", ".join(self.must_show) + ".")
        if self.must_not_show:
            parts.append("Must NOT appear: " + ", ".join(self.must_not_show) + ".")
        if self.visual_type == "communicative_scene":
            parts.append(
                "A scene with several distinguishable people or objects, so a "
                "viewer must ask a question to identify any one of them."
            )
        elif self.visual_type == "direct_concept":
            parts.append(
                f"A single {self.target_concept}, one only, alone in the frame "
                "and filling most of it, plain uncluttered background, nothing "
                "else visible. Not a set, not a collage, not a grid, not "
                "multiple examples."
            )
        elif self.complexity == "low":
            parts.append(
                "Exactly one subject, filling most of the frame, plain uncluttered "
                "background, no secondary objects competing for attention."
            )
        if not self.text_allowed:
            parts.append("No text, letters, words, numbers, labels or watermarks.")
        if self.style:
            parts.append(self.style)
        return " ".join(parts)

    @staticmethod
    def _terms(*parts: str) -> str:
        """Join phrases into search terms, dropping words already used.

        "a wooden table" plus a must_show of "wooden table" searched for the
        same thing twice, which ranks worse rather than better.
        """
        seen: set[str] = set()
        words: list[str] = []
        for word in " ".join(parts).replace(",", " ").split():
            key = word.strip(".").lower()
            if key and key not in seen:
                seen.add(key)
                words.append(word.strip("."))
        return " ".join(words[:12])

    def to_search_queries(self) -> list[str]:
        """The terms to try in a stock photo library, most specific first.

        A generator prompt and a search query are not the same sentence. The
        generator is told what to draw and what to leave out; a search engine
        given "Must NOT appear: chairs, people" returns pictures of chairs and
        people, because it matches words rather than obeying them. So the
        exclusions are dropped and what is left is the noun phrase a
        photographer would have filed the picture under.

        And it is a ladder rather than one string, because precision and recall
        pull opposite ways here. "wooden dining table plain background" is
        exactly the right description and returns nothing at all; "wooden dining
        table" returns a hundred, of which the first is fine. So the specific
        query is tried, and when it comes back empty the qualifiers are dropped
        one rung at a time until something is there — which is what a person
        does, and what the first version did not, so half the pictures fell
        through to being generated for no reason.
        """
        subject = self.main_subject.strip() or self.target_concept.strip()
        ladder = [
            self.search_query.strip(),
            self._terms(subject, *self.must_show[:2],
                        "plain background"
                        if self.visual_type == "direct_concept"
                        and self.complexity == "low" else ""),
            self._terms(subject, *self.must_show[:1]),
            self._terms(subject),
            self._terms(self.target_concept),
        ]
        rungs: list[str] = []
        for query in ladder:
            if query and query not in rungs:
                rungs.append(query)
        return rungs[:4]

    def to_search_query(self) -> str:
        """The single best search string — the top rung of the ladder."""
        rungs = self.to_search_queries()
        return rungs[0] if rungs else ""


class FunctionalPhrase(BaseModel):
    """One expression, taught by what it DOES rather than by what it means.

    The learner who has memorised that "Wie bitte?" means "pardon?" has learnt a
    translation. The learner who knows it is what you say when you did not catch
    something has learnt a phrase they will use.
    """

    phrase: str = Field(description="The expression, in the target language.")
    function: str = Field(
        description="What it does, as an action: 'asking for repetition', "
        "'apologising', 'accepting an apology'. Not a translation."
    )
    meaning: str = Field(description="What it means, for the tutor's answer key.")
    situation: str = Field(description="When a speaker would actually say it.")
    formality: Literal["informal", "neutral", "formal"] = Field(
        default="neutral", description="The register the phrase belongs to."
    )
    level: str = Field(default="A1", description='CEFR band, e.g. "A1".')


class VocabularyEntry(BaseModel):
    """One lexical item, selected on purpose and taught whole.

    In a gendered language the article is part of the word: "die Frage, Pl. die
    Fragen" is the item, and "Frage" is half of it. The reference lesson prints
    the article and the plural on every noun card for exactly this reason — a
    learner who learns the bare noun has to learn it again later.
    """

    lemma: str = Field(description="The item as the learner should record it.")
    lexical_type: LexicalType = Field(
        default="word",
        description="A fixed expression is learnt whole, a word is learnt with its "
        "grammar. Treating them the same teaches one of them wrongly.",
    )
    article: str = Field(
        default="", description='The definite article, for a noun: "die". Empty otherwise.'
    )
    plural: str = Field(
        default="", description='The plural form: "die Fragen". Empty where there is none.'
    )
    meaning: str = Field(description="What it means, in the support language.")
    semantic_group: str = Field(
        description="The group it is learnt with: 'Begrüßungen', 'classroom "
        "objects', 'polite phrases'. Grouping is what makes it retrievable."
    )
    example: str = Field(
        description="One natural sentence using it, at this band. Not a sentence "
        "that exists only to contain the word — 'Der Computer ist ein Computer.' "
        "is not an example."
    )
    function: str = Field(
        default="",
        description="For a phrase: what it does. Empty for a plain noun.",
    )
    pronunciation_note: str = Field(
        default="",
        description="Only where the sounds are actually a difficulty worth a stage.",
    )
    is_known: bool = Field(
        default=False,
        description="True when the learner already has this and it is being "
        "recycled rather than introduced. Does not count against the new-item budget.",
    )
    image: VisualSpec | None = Field(
        default=None,
        description="The picture for this word. Required for every NEW item: the "
        "reference decks print a photograph beside each one, because a word met "
        "with a picture is learnt without translating and a word met in a "
        "glossary is learnt as a translation. A fixed expression whose meaning is "
        "a situation rather than an object gets a context scene of that situation.",
    )


class VocabularySelection(BaseModel):
    """The words this lesson teaches, and the ones it deliberately does not.

    Selection is a decision, and the old pipeline never made it — it asked for
    "vocabulary about X" and got whatever came back. Naming what was excluded
    and why is what turns a word list into a selection.
    """

    target_count: int = Field(
        ge=3, le=25, description="How many NEW items this hour introduces."
    )
    entries: list[VocabularyEntry] = Field(min_length=3)
    selection_criteria: list[str] = Field(
        default_factory=list,
        description="Why these: frequency, usefulness for this learner, "
        "depictability, relation to the objective.",
    )
    excluded: list[str] = Field(
        default_factory=list,
        description="Words considered and left out, with the reason. Evidence that "
        "a selection happened.",
    )

    @property
    def new_entries(self) -> list[VocabularyEntry]:
        return [e for e in self.entries if not e.is_known]

    @model_validator(mode="after")
    def _the_count_is_honest(self) -> VocabularySelection:
        new = len(self.new_entries)
        if new != self.target_count:
            raise ValueError(
                f"target_count says {self.target_count} new items but {new} entries "
                "are marked new"
            )
        lemmas = [e.lemma.strip().lower() for e in self.entries]
        if len(set(lemmas)) != len(lemmas):
            duplicated = [w for w, n in Counter(lemmas).items() if n > 1]
            raise ValueError(f"the same item appears twice: {duplicated}")
        return self


class GlossedWord(BaseModel):
    """One hard word in a reading text, and what to do about it.

    The decision this records is the one the old pipeline never made: it either
    ignored difficult vocabulary or turned all of it into a word list. Neither
    teaches the thing that matters, which is reading past words you do not know.
    """

    word: str
    meaning: str
    support: VocabularySupport = Field(
        description="'essential' gets pre-taught, 'inferable' is deliberately left "
        "in as a context-guessing task, 'unnecessary' is not taught at all."
    )
    context_clue: str = Field(
        default="",
        description="For an inferable word: what in the surrounding text gives it "
        "away. Required, or the learner is being asked to guess rather than infer.",
    )

    @model_validator(mode="after")
    def _inferable_words_are_actually_inferable(self) -> GlossedWord:
        if self.support == "inferable" and not self.context_clue.strip():
            raise ValueError(
                f"{self.word!r} is marked inferable but nothing in the text is "
                "named as the clue — that is guessing, not inference"
            )
        return self


class TextSpec(BaseModel):
    """The brief for the reading text, written before a single question exists.

    Text first. The old pipeline generated a passage and then mined it for
    whatever could be asked, which is how a reading lesson becomes ten questions
    that happen to be answerable. Specifying the main idea and the key
    information up front means the questions have something to be *about*, and
    means the text can be rejected before any questions are written against it.
    """

    text_type: str = Field(
        description="The genre: 'short_email', 'notice', 'blog_post'. Chosen "
        "because it suits the objective, not because an article is the default."
    )
    topic: str
    purpose: str = Field(
        description="Why a real person would read this: to find opening hours, to "
        "learn what happened, to decide whether to go."
    )
    length_words: int = Field(ge=20, le=800)
    main_idea: str = Field(
        description="The one thing a learner who understood it could say. What the "
        "gist stage asks about."
    )
    key_information: list[str] = Field(
        min_length=2,
        description="The facts the text must contain, because the detail questions "
        "will be about exactly these.",
    )
    structure: str = Field(
        default="",
        description="How it is organised — paragraphs, turns, sections. The "
        "reference breaks one dialogue into five parts, each read separately.",
    )
    glossary: list[GlossedWord] = Field(
        default_factory=list,
        description="The hard words, each with a decision attached.",
    )
    vocabulary_constraints: list[str] = Field(default_factory=list)
    grammar_constraints: list[str] = Field(
        default_factory=list,
        description="What the text may use. A text can have easy words and still "
        "be too hard because of its sentences.",
    )

    @property
    def new_words(self) -> int:
        return sum(1 for g in self.glossary if g.support in {"essential", "useful"})


class CommunicativeTask(BaseModel):
    """What the learner must be able to DO by the end of a communication lesson.

    Written before any material, because everything generated afterwards has to
    prepare the learner for exactly this. The success criteria are the point:
    they are how the tutor judges whether communication succeeded, which is a
    different question from whether it was grammatically correct.
    """

    task: str = Field(description="The action: 'exchange personal information'.")
    situation: str = Field(description="Where and when: 'meeting a new classmate'.")
    learner_role: str = Field(description="Who the learner is in it.")
    interlocutor_role: str = Field(description="Who they are talking to.")
    goal: str = Field(
        description="What must be achieved: 'learn the other person's name and "
        "spell it correctly'. Something has to be accomplished, or it is a "
        "conversation exercise rather than a task."
    )
    required_language: list[str] = Field(
        min_length=2,
        description="The expressions the learner needs to do it, verbatim.",
    )
    success_criteria: list[str] = Field(
        min_length=2,
        description="Observable, in the order they happen: 'asks the person's "
        "name', 'asks for spelling when necessary', 'spells their own name'. "
        "Judged on whether communication succeeded, not on accuracy.",
    )
    information_gap: str = Field(
        default="",
        description="What each side knows that the other does not. The real reason "
        "to speak. Empty only when the task genuinely has no gap.",
    )


class ExerciseSpec(BaseModel):
    """What one exercise set must be, before its items are written."""

    exercise_type: ExerciseType
    operation: Operation = Field(
        description="The cognitive operation. This is the axis variety is measured "
        "on — six sets that all 'complete' are one exercise printed six times."
    )
    skill: Skill
    number_of_items: int = Field(ge=1, le=12)
    retrieval_direction: RetrievalDirection = Field(
        default="",
        description="Which way the learner travels. A vocabulary lesson that only "
        "ever asks word_to_meaning has tested recognition and called it practice.",
    )
    reading_skill: ReadingSkill = Field(
        default="",
        description="For a reading lesson: which reading ability these questions "
        "actually exercise. A set that is all 'specific_detail' is a test.",
    )
    requires_evidence: bool = Field(
        default=False,
        description="True for comprehension questions: every item must cite the "
        "part of the text that supports its answer, and the checker verifies it.",
    )
    constraints: list[str] = Field(
        default_factory=list,
        description="What every item must obey, e.g. 'exactly one defensible "
        "answer', 'no grammar beyond the target', 'no vocabulary not yet met'.",
    )
    vocabulary_constraints: list[str] = Field(
        default_factory=list,
        description="The words items may draw on. Naming them is what stops an "
        "A1 article drill from arriving full of B1 nouns.",
    )
    success_criteria: list[str] = Field(
        default_factory=list,
        description="What the learner getting this right demonstrates.",
    )
    item_visuals: list[VisualSpec] = Field(
        default_factory=list,
        description="One picture per item, for the exercise types where the "
        "picture IS the item — picture-matching, picture-naming, labelling. "
        "Must be exactly number_of_items long. A single composite grid is not a "
        "substitute: it cannot be numbered, and it lets the same object appear "
        "twice in a task whose answers must be unique.",
    )

    @model_validator(mode="after")
    def _picture_tasks_have_a_picture_per_item(self) -> ExerciseSpec:
        if self.exercise_type not in ONE_IMAGE_PER_ITEM_TYPES:
            return self
        if not self.item_visuals:
            return self  # the slot-level validator reports the absence
        if len(self.item_visuals) != self.number_of_items:
            raise ValueError(
                f"{self.exercise_type!r} has {self.number_of_items} items but "
                f"{len(self.item_visuals)} pictures; the picture is the item, so "
                "there must be exactly one each"
            )
        concepts = [v.target_concept.strip().lower() for v in self.item_visuals]
        if len(set(concepts)) != len(concepts):
            from collections import Counter as _C
            repeated = [c for c, n in _C(concepts).items() if n > 1]
            raise ValueError(
                f"two items would show the same thing ({repeated}); the answer to "
                "each item must be unique or the task has more than one right "
                "answer"
            )
        return self

    @model_validator(mode="after")
    def _type_and_operation_agree(self) -> ExerciseSpec:
        expected = EXERCISE_TYPES[self.exercise_type]["operation"]
        if self.operation != expected:
            raise ValueError(
                f"exercise type {self.exercise_type!r} exercises {expected!r}, not "
                f"{self.operation!r} — the type and the operation must describe the "
                "same task or variety cannot be measured"
            )
        low, high = EXERCISE_TYPES[self.exercise_type]["items"]
        if not low <= self.number_of_items <= high:
            raise ValueError(
                f"{self.exercise_type!r} works with {low}-{high} items, not "
                f"{self.number_of_items}"
            )
        return self


class BlueprintSlot(BaseModel):
    """One planned piece of material: what it is, and what it is for."""

    slot_id: str = Field(description='Short id: "s1", "s2".')
    stage: Stage
    objective_ids: list[str] = Field(
        min_length=1,
        description="The lesson objectives this serves. Never empty: material that "
        "advances no objective is material generated because the exercise type "
        "exists, which is the habit this whole schema is against.",
    )
    activity_id: str = Field(
        default="",
        description="The plan activity this slot belongs to, so the generated "
        "material can be tied back to the hour.",
    )
    pedagogical_goal: str = Field(
        min_length=20,
        description="What this achieves, specifically. 'Fill in the blanks' is not "
        "a goal; 'controlled recognition practice: the learner selects the correct "
        "definite article for nouns already met in this lesson' is.",
    )
    target_grammar: str = Field(
        default="",
        description="The form being practised, for a grammar lesson. Empty when the "
        "lesson is not about a form.",
    )
    difficulty: str = Field(description='CEFR band, e.g. "A1".')
    support_level: SupportLevel = Field(
        default="high",
        description="How much the learner is holding onto. Must fall across the "
        "lesson: the final task has to be less supported than the practice that "
        "prepared it, or the learner read aloud rather than communicated.",
    )
    recycles: list[str] = Field(
        default_factory=list,
        description="Vocabulary or phrases from earlier in this lesson that appear "
        "again here. How spaced recycling is planned rather than hoped for.",
    )

    exercise: ExerciseSpec | None = Field(
        default=None, description="Set for a practice slot; null for a presentation."
    )
    presentation: PresentationKind | None = Field(
        default=None, description="Set for a presentation slot; null for practice."
    )
    presentation_brief: str = Field(
        default="",
        description="For a presentation: what it must contain and what situation it "
        "happens in. A dialogue brief names the two speakers, what each of them "
        "WANTS, and why the exchange has to happen at all.",
    )

    visual: VisualSpec | None = Field(
        default=None,
        description="A picture, only where one materially improves the activity. "
        "Null is the right answer for a rule table or a scrambled-sentence task.",
    )
    visual_decision: str = Field(
        default="",
        description="Why there is or is not a picture here. Required either way, so "
        "that 'no image' is a decision on the record rather than an omission.",
    )
    estimated_minutes: int = Field(ge=1, le=20)

    @model_validator(mode="after")
    def _is_exactly_one_thing(self) -> BlueprintSlot:
        if bool(self.exercise) == bool(self.presentation):
            raise ValueError(
                f"slot {self.slot_id!r} must be either an exercise or a presentation, "
                "not both and not neither"
            )
        if self.presentation and not self.presentation_brief.strip():
            raise ValueError(
                f"slot {self.slot_id!r} is a {self.presentation} with no brief — a "
                "presentation with no brief is the topic-to-prose jump again"
            )
        if not self.visual_decision.strip():
            raise ValueError(
                f"slot {self.slot_id!r} does not say why it has or has not got a "
                "picture. Decorative images are what happens when nobody had to say."
            )
        return self

    @property
    def skill(self) -> str:
        if self.exercise:
            return self.exercise.skill
        return "comprehension"

    @property
    def support_rank(self) -> int:
        return SUPPORT_LEVELS[self.support_level]


class MaterialBlueprint(BaseModel):
    """The specification for one lesson's material, before any is written."""

    student_id: str
    subject: str
    target_language: str = Field(
        description='The language the material is written in, e.g. "german". '
        "Read from get_target_language, never inferred. Everything the learner "
        "reads is in it — a German lesson is German from the cover to the last "
        "page, a French lesson is French."
    )
    level_id: str
    band: str = Field(description='CEFR band, e.g. "A1".')
    target_item_id: str
    target_item_title: str = ""
    focus: Focus = "grammar"

    grammar_point: str = Field(
        default="",
        description="The one form a grammar lesson teaches. Empty for other focuses.",
    )
    context: str = Field(
        description="The realistic situation the language is met in: classroom, "
        "home, shopping, travel. Chosen for the content and the learner."
    )
    communicative_task: CommunicativeTask | None = Field(
        default=None,
        description="Required for a communication lesson: the task the whole hour "
        "prepares the learner to perform.",
    )
    vocabulary: VocabularySelection | None = Field(
        default=None,
        description="Required for a vocabulary lesson: the items chosen, and the "
        "ones deliberately left out.",
    )
    text: TextSpec | None = Field(
        default=None,
        description="Required for a reading lesson: the brief for the text itself, "
        "settled before any question is written against it.",
    )
    reading_skill: ReadingSkill = Field(
        default="",
        description="The primary reading ability a reading lesson builds. At least "
        "one activity must explicitly practise it.",
    )
    functional_language: list[FunctionalPhrase] = Field(
        default_factory=list,
        description="The expressions this lesson teaches by function. Required for "
        "a communication lesson.",
    )

    slots: list[BlueprintSlot] = Field(min_length=3)
    rationale: str = Field(
        description="Why these stages, in this order, for this student. Cites the "
        "diagnosis."
    )

    # ---- what is checkable about a plan while it is still cheap to change ----

    @model_validator(mode="after")
    def _slot_ids_are_unique(self) -> MaterialBlueprint:
        ids = [s.slot_id for s in self.slots]
        if len(set(ids)) != len(ids):
            raise ValueError(f"duplicate slot ids: {ids}")
        return self

    @model_validator(mode="after")
    def _stages_belong_to_this_focus(self) -> MaterialBlueprint:
        known = stages_for(self.focus)
        stray = sorted({s.stage for s in self.slots} - set(known))
        if stray:
            raise ValueError(
                f"stages {stray} are not part of a {self.focus} lesson; its stages "
                f"are {sorted(known, key=lambda x: known[x]['order'])}"
            )
        return self

    @model_validator(mode="after")
    def _stages_run_forwards(self) -> MaterialBlueprint:
        """A lesson that practises before it presents is out of order.

        Not every stage has to appear — a review lesson skips half of them — but
        the ones that do appear have to run in the order they teach in.
        """
        seen = [stage_order(self.focus, s.stage) for s in self.slots]
        if seen != sorted(seen):
            raise ValueError(
                f"stages are out of pedagogical order: {[s.stage for s in self.slots]}"
            )
        return self

    @model_validator(mode="after")
    def _the_lesson_teaches_its_focus(self) -> MaterialBlueprint:
        stages = {s.stage for s in self.slots}
        missing = REQUIRED_STAGES_BY_FOCUS.get(self.focus, set()) - stages
        if missing:
            raise ValueError(
                f"a {self.focus} lesson needs {sorted(missing)}; without them it "
                "does not teach what it claims to"
            )
        one_of = ONE_OF_REQUIRED_BY_FOCUS.get(self.focus, set())
        if one_of and not stages & one_of:
            raise ValueError(
                f"a {self.focus} lesson needs at least one of {sorted(one_of)}: "
                "otherwise the learner recognises the language but never uses it"
            )
        return self

    @model_validator(mode="after")
    def _progression_has_no_cliff(self) -> MaterialBlueprint:
        """Presentation straight to free production is the jump to catch.

        recognition -> comprehension -> controlled -> guided -> communication.
        Skipping one rung is a design choice; skipping two is asking the learner
        to do unaided what they have not yet done with help.

        Measured against the HIGHEST rung reached so far, not against the
        previous exercise. A lesson is allowed to drop back — a vocabulary
        recycling stage deliberately returns to recognition after guided
        production, and the reference lesson does exactly that — and what
        matters is whether the learner has ever been supported at this level,
        not what the immediately preceding activity happened to be.
        """
        reached = 0
        for slot in self.slots:
            if not slot.exercise:
                continue
            rank = SKILL_LADDER[slot.skill]
            if reached and rank - reached > MAX_SKILL_JUMP:
                raise ValueError(
                    f"{slot.slot_id} jumps {rank - reached} rungs past anything "
                    "the lesson has practised; the learner is being asked to do "
                    "unaided what they have not yet done with help"
                )
            reached = max(reached, rank)
        return self

    @model_validator(mode="after")
    def _support_falls_away(self) -> MaterialBlueprint:
        """The final task must be less supported than the practice before it.

        This is the communication lesson's central claim. A "role-play" where
        both speakers read predetermined sentences at the same level of support
        as the drill before it is not communication, it is a reading exercise
        with two voices.
        """
        if self.focus not in {"communication", "vocabulary", "reading"}:
            return self
        ranked = [(s.slot_id, s.support_rank) for s in self.slots]
        for (prev_id, prev), (this_id, rank) in zip(ranked, ranked[1:]):
            if rank > prev:
                raise ValueError(
                    f"support goes back UP at {this_id} (after {prev_id}); "
                    "scaffolding must fall away across the lesson, not return"
                )
        if ranked and ranked[-1][1] > SUPPORT_LEVELS["low"]:
            raise ValueError(
                f"the lesson never gets below '{self.slots[-1].support_level}' "
                "support; the learner is helped all the way to the end and never "
                "performs anything independently"
            )
        return self

    @model_validator(mode="after")
    def _a_communication_lesson_has_a_task(self) -> MaterialBlueprint:
        if self.focus != "communication":
            return self
        if self.communicative_task is None:
            raise ValueError(
                "a communication lesson with no communicative_task is a grammar "
                "lesson with conversation added; state what the learner must be "
                "able to DO and build backwards from it"
            )
        if not self.functional_language:
            raise ValueError(
                "no functional_language: the learner would memorise sentences "
                "without learning what any of them is FOR"
            )
        return self

    @model_validator(mode="after")
    def _a_vocabulary_lesson_selects_its_words(self) -> MaterialBlueprint:
        if self.focus != "vocabulary":
            return self
        if self.vocabulary is None:
            raise ValueError(
                "a vocabulary lesson with no vocabulary selection is a request for "
                "'words about X', which is how the word lists happened"
            )
        ceiling = MAX_NEW_ITEMS_BY_BAND.get(self.band.upper(), 12)
        count = len(self.vocabulary.new_entries)
        if count > ceiling:
            raise ValueError(
                f"{count} new items at {self.band} exceeds {ceiling}; a learner "
                "given 25 words half-learns 25 words. Cut the list and teach it."
            )
        return self

    @model_validator(mode="after")
    def _every_new_word_has_a_picture(self) -> MaterialBlueprint:
        """A word introduced without a picture is introduced as a translation."""
        if self.focus != "vocabulary" or self.vocabulary is None:
            return self
        bare = [e.lemma for e in self.vocabulary.new_entries if e.image is None]
        if bare:
            raise ValueError(
                f"these new vocabulary items have no picture: {bare[:8]}. Every "
                "new item needs one — a concrete object gets a direct_concept "
                "image, a phrase like 'Guten Morgen!' gets a context scene of the "
                "situation it belongs to."
            )
        return self

    @model_validator(mode="after")
    def _vocabulary_is_actually_retrieved(self) -> MaterialBlueprint:
        """Recognition is not retrieval, and only one of them makes a speaker."""
        if self.focus != "vocabulary":
            return self
        directions = {s.exercise.retrieval_direction for s in self.slots
                      if s.exercise and s.exercise.retrieval_direction}
        productive = directions & PRODUCTIVE_DIRECTIONS
        if len(productive) < MIN_PRODUCTIVE_DIRECTIONS:
            raise ValueError(
                f"only {sorted(productive)} require the learner to produce the "
                f"word; a vocabulary lesson needs at least "
                f"{MIN_PRODUCTIVE_DIRECTIONS} productive retrieval directions from "
                f"{sorted(PRODUCTIVE_DIRECTIONS)}, or it has tested recognition and "
                "called it practice"
            )
        return self

    @model_validator(mode="after")
    def _vocabulary_comes_back(self) -> MaterialBlueprint:
        """A word introduced once and never used again was not taught."""
        if self.focus != "vocabulary" or self.vocabulary is None:
            return self
        # Compared on letters alone. "Guten Morgen" and "Guten Morgen!" are the
        # same item, and failing a lesson over an exclamation mark would teach
        # the planner to distrust the check rather than to plan recycling.
        def key(text: str) -> str:
            return re.sub(r"[^\w]+", "", (text or "").lower(), flags=re.UNICODE)

        targets = {key(e.lemma): e.lemma for e in self.vocabulary.new_entries}
        targets.pop("", None)
        if not targets:
            return self
        recycled = {key(r) for s in self.slots for r in s.recycles}
        covered = set(targets) & recycled
        share = len(covered) / len(targets)
        if share < MIN_RECYCLED_SHARE:
            missing = sorted(targets[k] for k in set(targets) - recycled)
            raise ValueError(
                f"only {share:.0%} of the new vocabulary is planned to reappear "
                f"after the stage that introduced it (needs {MIN_RECYCLED_SHARE:.0%}). "
                f"Never seen again: {missing[:8]}. Name them in the recycles field "
                "of a later slot, or cut them."
            )
        return self


    @model_validator(mode="after")
    def _a_reading_lesson_specifies_its_text(self) -> MaterialBlueprint:
        """Text first, and a named skill. Questions come after both."""
        if self.focus != "reading":
            return self
        if self.text is None:
            raise ValueError(
                "a reading lesson with no text specification is a request for "
                "questions about a passage nobody has designed yet"
            )
        if not self.reading_skill:
            raise ValueError(
                "no primary reading_skill named. A reading lesson has two targets "
                "— what the text says and how the learner got at it — and this is "
                "the second one"
            )
        band = self.band.upper()
        low, high = TEXT_LENGTH_BY_BAND.get(band, (20, 800))
        if not low <= self.text.length_words <= high:
            raise ValueError(
                f"a {self.text.length_words}-word text at {band} is outside "
                f"{low}-{high}; too long and the learner decodes instead of reading"
            )
        genres = TEXT_TYPES_BY_BAND.get(band, [])
        if genres and self.text.text_type not in genres:
            raise ValueError(
                f"text type {self.text.text_type!r} is not one a {band} learner "
                f"reads. Choose from {genres}"
            )
        budget = NEW_WORD_BUDGET_BY_BAND.get(band, 10)
        if self.text.new_words > budget:
            raise ValueError(
                f"{self.text.new_words} words need teaching at {band}, over the "
                f"budget of {budget}. Mark more of them 'inferable' and let the "
                "learner read past them, or simplify the text."
            )
        return self

    @model_validator(mode="after")
    def _gist_comes_before_detail(self) -> MaterialBlueprint:
        """A learner asked to understand every sentence on first contact learns
        that reading means decoding, and reads slowly for years after."""
        if self.focus != "reading":
            return self
        stages = [s.stage for s in self.slots]
        if "gist" in stages and "detail" in stages:
            if stages.index("gist") > stages.index("detail"):
                raise ValueError(
                    "the detail stage runs before the gist stage; the first read "
                    "must have a global purpose"
                )
        return self

    @model_validator(mode="after")
    def _the_declared_reading_skill_is_practised(self) -> MaterialBlueprint:
        if self.focus != "reading" or not self.reading_skill:
            return self
        practised = {s.exercise.reading_skill for s in self.slots
                     if s.exercise and s.exercise.reading_skill}
        if self.reading_skill not in practised:
            raise ValueError(
                f"the lesson declares {self.reading_skill!r} as its reading skill "
                f"but no activity practises it (found {sorted(practised)}). A "
                "declared skill nothing exercises is a label."
            )
        if len(practised) < MIN_DISTINCT_READING_SKILLS:
            raise ValueError(
                f"every question tests {sorted(practised)}; a reading lesson needs "
                f"at least {MIN_DISTINCT_READING_SKILLS} different reading skills, "
                "or it is a test rather than a lesson"
            )
        return self

    @model_validator(mode="after")
    def _does_not_overtest(self) -> MaterialBlueprint:
        """Fifteen facts in the text is not a reason for fifteen questions."""
        if self.focus != "reading":
            return self
        questions = sum(s.exercise.number_of_items for s in self.slots
                        if s.exercise and s.stage in
                        {"gist", "detail", "inference", "vocabulary-in-context"})
        ceiling = MAX_QUESTIONS_BY_BAND.get(self.band.upper(), 12)
        if questions > ceiling:
            raise ValueError(
                f"{questions} comprehension questions at {self.band} exceeds "
                f"{ceiling}; balance the set across skills instead of mining the "
                "text for everything askable"
            )
        return self

    @model_validator(mode="after")
    def _comprehension_questions_must_cite_the_text(self) -> MaterialBlueprint:
        if self.focus != "reading":
            return self
        for slot in self.slots:
            if slot.exercise and slot.stage in {"gist", "detail", "inference"}:
                if not slot.exercise.requires_evidence:
                    raise ValueError(
                        f"slot {slot.slot_id!r} asks comprehension questions without "
                        "requires_evidence; an answer nothing in the text supports "
                        "cannot be marked, and is the defect this catches"
                    )
        return self

    @model_validator(mode="after")
    def _every_slot_serves_a_real_objective(self) -> MaterialBlueprint:
        for slot in self.slots:
            if not [o for o in slot.objective_ids if o.strip()]:
                raise ValueError(f"slot {slot.slot_id!r} serves no objective")
        return self

    @model_validator(mode="after")
    def _practice_is_varied(self) -> MaterialBlueprint:
        """Six exercises that all ask the same thing are one exercise.

        Measured on the cognitive operation, not on the exercise type: a
        gap-fill and a cloze differ in name and not in what the learner does.
        """
        operations = [s.exercise.operation for s in self.slots if s.exercise]
        if len(operations) < 3:
            return self
        distinct = len(set(operations))
        # Variety is measured over the practice, not over the payoff. The last
        # activities of a communication lesson all ask the learner to produce,
        # and that is what they are for.
        practice = [s.exercise.operation for s in self.slots
                    if s.exercise
                    and not operation_variety_exempt(self.focus, s.stage)]
        if distinct < MIN_DISTINCT_OPERATIONS:
            raise ValueError(
                f"{len(operations)} exercise sets using only {distinct} cognitive "
                f"operations {sorted(set(operations))}; a lesson needs at least "
                f"{MIN_DISTINCT_OPERATIONS}. Vary what the learner does, not the label."
            )
        if len(practice) >= 3:
            commonest, count = Counter(practice).most_common(1)[0]
            if count / len(practice) > MAX_OPERATION_SHARE:
                raise ValueError(
                    f"{count} of {len(practice)} practice sets are {commonest!r}; "
                    f"no operation may exceed {MAX_OPERATION_SHARE:.0%} of the "
                    "practice. (The production stages are exempt — repeating "
                    "'produce' there is the point.)"
                )
        return self

    @model_validator(mode="after")
    def _fills_the_hour(self) -> MaterialBlueprint:
        """A thin lesson is as much a failure as a bloated one.

        "Prefer six excellent exercises to twenty repetitive ones" is right and
        was read as licence to produce eight sparse slides. The reference decks
        run 38-41 slides of real content for the same sixty minutes. Both
        ceilings and floors, or the rule only ever pushes one way.
        """
        if len(self.slots) < MIN_SLOTS_PER_LESSON:
            raise ValueError(
                f"{len(self.slots)} slots is not an hour of teaching; a lesson "
                f"needs at least {MIN_SLOTS_PER_LESSON}. Add the stages this "
                "grammar point, level and learner actually call for."
            )
        items = sum(s.exercise.number_of_items for s in self.slots if s.exercise)
        if items < MIN_EXERCISE_ITEMS_PER_LESSON:
            raise ValueError(
                f"{items} exercise items across the whole lesson is too thin "
                f"(needs {MIN_EXERCISE_ITEMS_PER_LESSON}); the learner runs out "
                "of things to do long before the hour ends"
            )
        if self.total_minutes < MIN_LESSON_MINUTES:
            raise ValueError(
                f"the slots total {self.total_minutes} minutes of a 60-minute "
                f"lesson; at least {MIN_LESSON_MINUTES} should be planned or the "
                "tutor is handing back time the student paid for"
            )
        return self

    @model_validator(mode="after")
    def _does_not_overgenerate(self) -> MaterialBlueprint:
        """Six excellent exercises beat twenty repetitive ones, and cost less."""
        per_stage = Counter(s.stage for s in self.slots)
        heavy = {st: n for st, n in per_stage.items() if n > MAX_SLOTS_PER_STAGE}
        if heavy:
            raise ValueError(
                f"too much material in one stage: {heavy}; the ceiling is "
                f"{MAX_SLOTS_PER_STAGE} per stage"
            )
        items = sum(s.exercise.number_of_items for s in self.slots if s.exercise)
        if items > MAX_EXERCISE_ITEMS_PER_LESSON:
            raise ValueError(
                f"{items} exercise items in one hour exceeds "
                f"{MAX_EXERCISE_ITEMS_PER_LESSON}; the learner will not reach them"
            )
        pictures = sum(1 for s in self.slots if s.visual)
        pictures += sum(len(s.exercise.item_visuals)
                        for s in self.slots if s.exercise)
        if self.vocabulary:
            pictures += sum(1 for e in self.vocabulary.entries if e.image)
        if pictures > MAX_IMAGES_PER_LESSON:
            raise ValueError(
                f"{pictures} images exceeds {MAX_IMAGES_PER_LESSON}; one useful "
                "picture beats five decorative ones"
            )
        return self

    @model_validator(mode="after")
    def _every_content_slot_is_illustrated(self) -> MaterialBlueprint:
        """A wall of text is not the product, however good the text is.

        The reference decks carry a picture on every content slide and leave
        only the closing summary, the word list and the self-assessment bare.
        The old pipeline's rule — "an image only where it earns its place" —
        was right about decoration and wrong about how much of a published
        lesson is visual, and it produced eight slides of prose.

        A dialogue is called out separately because it is the slide where a
        picture does the most work: the situation is what makes the language
        make sense, and showing it costs the learner nothing to read.
        """
        def illustrated(slot: BlueprintSlot) -> bool:
            if slot.visual is not None:
                return True
            # A picture-matching task is illustrated by its items, not by a
            # single picture on the slot.
            return bool(slot.exercise and slot.exercise.item_visuals)

        bare = [s.slot_id for s in self.slots
                if not illustrated(s) and s.stage not in NO_IMAGE_STAGES]
        if bare:
            raise ValueError(
                f"slots {bare} have no picture. Every slide carries one except "
                f"{sorted(NO_IMAGE_STAGES)}. If the target is abstract, "
                "photograph a concrete instance of it rather than leaving the "
                "slide bare."
            )
        dialogues = [s.slot_id for s in self.slots
                     if s.presentation == "dialogue" and s.visual is None]
        if dialogues:
            raise ValueError(
                f"dialogue slots {dialogues} have no picture. A dialogue needs "
                "the scene it happens in; that is what makes the language mean "
                "something rather than sit on the page."
            )
        return self

    @model_validator(mode="after")
    def _picture_tasks_get_one_image_per_item(self) -> MaterialBlueprint:
        """A picture-matching task needs N pictures, not one grid of N things.

        The first rebuilt lesson asked for a single composite image for a
        five-word matching exercise and got a six-panel grid with two identical
        chairs in it and printed English on a book. None of that is fixable by
        prompting harder: a composite cannot be counted, cannot be numbered, and
        gives the model licence to fill space. The reference decks use separate
        numbered photographs for exactly this reason.
        """
        for slot in self.slots:
            if not slot.exercise:
                continue
            if slot.exercise.exercise_type not in ONE_IMAGE_PER_ITEM_TYPES:
                continue
            if slot.exercise.item_visuals:
                continue
            if slot.visual and slot.visual.visual_type != "categorisation":
                raise ValueError(
                    f"slot {slot.slot_id!r} is a "
                    f"{slot.exercise.exercise_type!r} task over "
                    f"{slot.exercise.number_of_items} items but carries ONE "
                    "image. The picture is the item here, so each item needs its "
                    "own: put a VisualSpec on every exercise item rather than a "
                    "single composite on the slot, or the learner is asked about "
                    "a grid nobody can number."
                )
        return self

    @model_validator(mode="after")
    def _images_are_not_asked_of_abstractions(self) -> MaterialBlueprint:
        for slot in self.slots:
            if not slot.visual:
                continue
            concept = slot.visual.target_concept.lower()
            if any(term in concept for term in UNDEPICTABLE):
                raise ValueError(
                    f"slot {slot.slot_id!r} asks for a picture of "
                    f"{slot.visual.target_concept!r}, which is a grammatical "
                    "abstraction. No photograph shows it, so what comes back is "
                    "decoration next to a rule the learner is trying to read."
                )
        return self

    # ---------------------------------------------------------- reading it ----

    @property
    def stages(self) -> list[str]:
        return [s.stage for s in self.slots]

    @property
    def total_minutes(self) -> int:
        return sum(s.estimated_minutes for s in self.slots)

    @property
    def image_count(self) -> int:
        total = sum(1 for s in self.slots if s.visual)
        total += sum(len(s.exercise.item_visuals) for s in self.slots if s.exercise)
        if self.vocabulary:
            total += sum(1 for e in self.vocabulary.entries if e.image)
        return total

    def slot(self, slot_id: str) -> BlueprintSlot | None:
        return next((s for s in self.slots if s.slot_id == slot_id), None)

    def operations(self) -> dict[str, int]:
        return dict(Counter(s.exercise.operation for s in self.slots if s.exercise))

    def retrieval_directions(self) -> dict[str, int]:
        return dict(Counter(
            s.exercise.retrieval_direction for s in self.slots
            if s.exercise and s.exercise.retrieval_direction))
