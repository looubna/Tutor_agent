"""Blueprint fixtures for the four language focuses.

Each is modelled on the corresponding published reference lesson, so a change
that makes a real lesson shape invalid fails here rather than in production.
"""

from __future__ import annotations

import pytest

from zanoba_agent.material.rubric import (
    NO_IMAGE_STAGES, ONE_IMAGE_PER_ITEM_TYPES)
from zanoba_agent.schemas.blueprint import (
    BlueprintSlot, CommunicativeTask, ExerciseSpec, FunctionalPhrase,
    GlossedWord, MaterialBlueprint, TextSpec, VisualSpec, VocabularyEntry,
    VocabularySelection)


def picture(concept="ein Klassenzimmer", visual_type="context_scene", **kw):
    """A plausible visual brief, so fixtures satisfy the every-slide rule."""
    base = dict(
        target_concept=concept, visual_type=visual_type, language_level="A1",
        pedagogical_purpose="show the situation this language belongs to",
        main_subject=f"a photograph of {concept}",
        composition="eye level, the subject filling most of the frame",
        must_not_show=["written text", "labels"],
    )
    base.update(kw)
    return VisualSpec(**base)


def slot(sid, stage, support="high", minutes=6, **kw):
    base = dict(
        slot_id=sid, stage=stage, objective_ids=["o1"],
        pedagogical_goal="controlled practice of the target language with items "
                         "the learner has already met in this lesson",
        difficulty="A1", support_level=support, estimated_minutes=minutes,
        visual_decision="a photograph of the situation these sentences belong to",
    )
    base.update(kw)
    # Every content slide carries a picture; only the closing summary, word list
    # and self-assessment go without. Fixtures follow the same rule the
    # blueprint enforces, so a fixture is always a lesson that could be taught.
    exercise = base.get("exercise")
    items_are_pictures = bool(exercise and exercise.item_visuals)
    if (base.get("visual") is None and stage not in NO_IMAGE_STAGES
            and not items_are_pictures):
        base["visual"] = picture()
    return BlueprintSlot(**base)


def ex(kind, op, skill, n, **kw):
    # Where the picture IS the item, the spec carries one per item rather than
    # one composite on the slot — a grid cannot be numbered and lets the same
    # object appear twice in a task whose answers must each be unique.
    if kind in ONE_IMAGE_PER_ITEM_TYPES and "item_visuals" not in kw:
        kw["item_visuals"] = [
            picture(f"Gegenstand {n_}", "direct_concept") for n_ in range(1, n + 1)]
    return ExerciseSpec(exercise_type=kind, operation=op, skill=skill,
                        number_of_items=n, **kw)


def _base(**kw):
    base = dict(student_id="s1", subject="german", target_language="german",
                level_id="a1-1", band="A1", target_item_id="a1-1.classroom.l3",
                context="Unterricht", rationale="mirrors the reference progression")
    base.update(kw)
    return base


# ------------------------------------------------------------------ grammar --

GRAMMAR_SLOTS = [
    # Six numbered photographs, one per word — the shape the reference deck's
    # matching slide uses. No separate header image: the pictures ARE the slide.
    slot("s1", "warm-up",
         exercise=ex("matching", "match", "recognition", 6,
                     item_visuals=[picture(c, "direct_concept") for c in
                                   ("Garten", "Telefon", "Ball", "Park",
                                    "Haus", "Katze")]),
         visual_decision="the pictures are the prompts; the learner supplies "
                         "each word, so each item carries its own"),
    slot("s2", "context", presentation="dialogue",
         presentation_brief="Sarah does not understand what der/die/das mean and "
                            "asks Lisa, who explains they are all 'the'"),
    slot("s3", "noticing", exercise=ex("classification", "classify", "recognition", 9)),
    slot("s4", "explanation", presentation="rule_table",
         presentation_brief="the three genders in one table with two nouns each"),
    slot("s5", "controlled-practice", support="medium",
         exercise=ex("multiple_choice", "choose", "recognition", 6)),
    slot("s6", "controlled-practice", support="medium",
         exercise=ex("gap_fill", "complete", "controlled_production", 6)),
    slot("s7", "guided-practice", support="low",
         exercise=ex("sentence_building", "reorder", "guided_production", 5)),
    slot("s8", "communicative-practice", support="low",
         exercise=ex("role_play", "respond", "communication", 1)),
    slot("s9", "review", support="independent", presentation="summary",
         presentation_brief="the rule plus the phrase bank from this lesson"),
]


@pytest.fixture
def grammar_blueprint():
    return MaterialBlueprint(**_base(focus="grammar", grammar_point="der/die/das"),
                             slots=GRAMMAR_SLOTS)


# ------------------------------------------------------------ communication --

COMMUNICATION_SLOTS = [
    slot("s1", "warm-up", exercise=ex("dialogue_response", "respond", "comprehension", 3),
         visual=picture("two students meeting for the first time")),
    slot("s2", "situation", presentation="dialogue",
         presentation_brief="Lisa mishears Safia's name as Sofia; Safia corrects "
                            "her and Lisa apologises. The mishearing is what makes "
                            "the repair phrases necessary"),
    slot("s3", "noticing",
         exercise=ex("phrase_function_match", "match", "comprehension", 4)),
    slot("s4", "language-resource", presentation="pronunciation_table",
         presentation_brief="the alphabet, as the resource needed to spell a name"),
    slot("s5", "controlled-practice", support="medium",
         exercise=ex("dialogue_completion", "complete", "comprehension", 4)),
    slot("s6", "guided-interaction", support="medium",
         exercise=ex("substitution", "produce", "guided_production", 4)),
    slot("s7", "communicative-task", support="low",
         exercise=ex("information_gap", "produce", "communication", 1),
         visual=VisualSpec(
             target_concept="a classroom of several different students",
             visual_type="communicative_scene", language_level="A1",
             pedagogical_purpose="information gap: the learner must ask to identify",
             main_subject="four students sitting at desks in a bright classroom",
             composition="wide shot, all four faces visible",
             ambiguity_tolerance="intentional",
             communication_goal="the learner must ask questions to work out which "
                                "student the partner has chosen",
             student_should_communicate=["Wie heißt du?", "Wie schreibt man das?"]),
         visual_decision="the scene is what the learner asks about; withholding "
                         "which student is meant is what creates the question"),
    slot("s8", "reflection", support="independent",
         exercise=ex("open_production", "produce", "communication", 2),
         visual_decision="none: this is the closing self-assessment"),
]


@pytest.fixture
def communication_blueprint():
    return MaterialBlueprint(
        **_base(focus="communication", target_item_id="a1-1.classroom.l2"),
        slots=COMMUNICATION_SLOTS,
        communicative_task=CommunicativeTask(
            task="exchange names and spell them",
            situation="meeting a new classmate in the first online lesson",
            learner_role="new student", interlocutor_role="classmate",
            goal="learn the other person's name and write it down correctly",
            required_language=["Wie heißt du?", "Wie schreibt man das?",
                               "Ich buchstabiere: ...", "Wie bitte?"],
            success_criteria=["asks the partner's name",
                              "asks for the spelling when unsure",
                              "spells their own name back correctly"],
            information_gap="each partner knows only their own name and must ask "
                            "for the other's letter by letter"),
        functional_language=[
            FunctionalPhrase(phrase="Wie bitte?", function="asking for repetition",
                             meaning="pardon?", situation="you did not catch what "
                             "was said"),
            FunctionalPhrase(phrase="Tut mir leid.", function="apologising",
                             meaning="I'm sorry", situation="you got something wrong"),
        ])


# ------------------------------------------------------------- vocabulary --

VOCABULARY_SLOTS = [
    slot("s1", "warm-up", exercise=ex("matching", "match", "recognition", 6),
         visual=picture("everyday objects with international names")),
    slot("s2", "encounter", presentation="dialogue",
         presentation_brief="Lisa greets Amir at the start of the first lesson and "
                            "he greets her back",
         exercise=None),
    slot("s3", "meaning", exercise=ex("picture_word_match", "match", "recognition", 6,
                                      retrieval_direction="word_to_meaning"),
         visual=VisualSpec(target_concept="Guten Morgen", language_level="A1",
                           pedagogical_purpose="establish meaning by time of day",
                           main_subject="a bright kitchen early in the morning",
                           composition="window with morning light",
                           must_not_show=["clock showing evening", "darkness"]),
         visual_decision="time of day is what distinguishes these greetings and a "
                         "picture shows it faster than a gloss"),
    slot("s4", "recognition", support="medium",
         exercise=ex("multiple_choice", "choose", "recognition", 5,
                     retrieval_direction="context_to_word"),
         recycles=["Guten Morgen", "Guten Tag"]),
    slot("s5", "retrieval", support="low",
         exercise=ex("picture_naming", "produce", "controlled_production", 6,
                     retrieval_direction="picture_to_word"),
         recycles=["Guten Morgen", "Guten Tag", "Guten Abend", "Hallo"],
         visual=picture("a person waving hello", "direct_concept")),
    slot("s6", "contextual-use", support="low",
         exercise=ex("sentence_building", "reorder", "guided_production", 5,
                     retrieval_direction="word_to_sentence"),
         recycles=["Vielen Dank", "Auf Wiedersehen"]),
    slot("s7", "recycling", support="independent",
         exercise=ex("classification", "classify", "recognition", 10,
                     retrieval_direction="meaning_to_word"),
         recycles=["Guten Morgen", "Guten Tag", "Guten Abend", "Hallo",
                   "Auf Wiedersehen", "Tschüss", "Gute Nacht", "Vielen Dank"]),
    slot("s8", "reflection", support="independent",
         exercise=ex("open_production", "produce", "communication", 2,
                     retrieval_direction="situation_to_word")),
]

_GREETINGS = [
    ("Hallo!", "hello"), ("Guten Morgen!", "good morning"),
    ("Guten Tag!", "good afternoon"), ("Guten Abend!", "good evening"),
    ("Auf Wiedersehen!", "goodbye"), ("Tschüss!", "bye"),
    ("Gute Nacht!", "good night"), ("Vielen Dank!", "thank you very much"),
]


@pytest.fixture
def vocabulary_blueprint():
    return MaterialBlueprint(
        **_base(focus="vocabulary", target_item_id="a1-1.classroom.l1"),
        slots=VOCABULARY_SLOTS,
        vocabulary=VocabularySelection(
            target_count=len(_GREETINGS),
            selection_criteria=["highest-frequency greetings", "usable from lesson one"],
            excluded=["Grüezi — regional, not needed at A1",
                      "Servus — regional, ambiguous between hello and goodbye"],
            entries=[
                VocabularyEntry(
                    lemma=lemma, lexical_type="fixed_expression", meaning=meaning,
                    semantic_group="Begrüßungen und Verabschiedungen",
                    example=f"{lemma} Ich bin Amir.",
                    function="greeting or farewell",
                    image=picture(meaning, "context_scene"))
                for lemma, meaning in _GREETINGS
            ]))


# ---------------------------------------------------------------- reading --

READING_SLOTS = [
    slot("s1", "pre-reading", minutes=6,
         exercise=ex("open_production", "produce", "communication", 2),
         visual=VisualSpec(target_concept="a large Canadian city street",
                           visual_type="context_scene", language_level="A2",
                           pedagogical_purpose="pre-reading prediction",
                           main_subject="a busy city street with historic and "
                                        "modern buildings",
                           composition="wide street-level view",
                           must_not_show=["signs naming the city", "text"]),
         visual_decision="the learner predicts what the text is about from the "
                         "scene, which the picture supports without naming the city"),
    slot("s2", "vocabulary-preparation", minutes=6, exercise=ex("gap_fill", "complete",
                                                     "controlled_production", 5)),
    slot("s3", "gist", minutes=6, support="medium",
         exercise=ex("multiple_choice", "choose", "comprehension", 2,
                     reading_skill="skimming", requires_evidence=True)),
    slot("s4", "detail", minutes=10, support="medium",
         exercise=ex("true_false", "choose", "comprehension", 5,
                     reading_skill="scanning", requires_evidence=True)),
    slot("s5", "inference", minutes=8, support="medium",
         exercise=ex("multiple_choice", "choose", "comprehension", 3,
                     reading_skill="inference", requires_evidence=True)),
    slot("s6", "post-reading", minutes=10, support="low",
         exercise=ex("interview", "respond", "communication", 1)),
    slot("s7", "review", minutes=4, support="independent",
         exercise=ex("open_production", "produce", "communication", 2)),
]


@pytest.fixture
def reading_blueprint():
    return MaterialBlueprint(
        **{**_base(focus="reading", target_item_id="a2-1.city.l1"),
           "band": "A2", "level_id": "a2-1", "target_language": "french",
           "context": "une ville"},
        reading_skill="scanning",
        slots=READING_SLOTS,
        text=TextSpec(
            text_type="short_dialogue", topic="a wedding trip to Montreal",
            purpose="find out who is going, when and how they will get there",
            length_words=140,
            main_idea="two friends are planning a trip to a wedding in Montreal",
            key_information=["the wedding is in Montreal",
                             "they arrive in the morning",
                             "they take a taxi from the airport"],
            structure="a telephone dialogue in five short parts",
            glossary=[
                GlossedWord(word="le beau-frère", meaning="brother-in-law",
                            support="essential"),
                GlossedWord(word="célibataire", meaning="single",
                            support="inferable",
                            context_clue="the previous line says 'il a divorcé'"),
            ]))
