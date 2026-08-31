"""The pedagogical rubric: what good language courseware is made of.

Extracted from professionally published A1 grammar lessons — the reference deck
in `German/A1-1/CH-1` is one — but deliberately not a copy of any of them. What
is reusable is not the content, it is the *shape*: concrete visual introduction,
then a situation, then the learner noticing the pattern before anyone states it,
then a short rule, then practice that changes its cognitive operation every few
minutes, then the grammar used to actually say something, then review.

A communication lesson has a different shape and a different centre of gravity.
It is not a grammar lesson with conversation bolted on: the target is what the
learner can DO in a real exchange, and grammar and vocabulary are resources
recruited to that end. The reference communication lesson teaches the alphabet,
but the alphabet is not the point — being able to say "Wie schreibt man das?"
and spell your own name back is. So the stages run situation → noticing →
controlled → guided interaction → communicative task → independent, with the
scaffolding deliberately falling away, and the lesson is judged on whether the
learner can perform the task at the end rather than on how many exercises it
contained.

That shape is encoded here as data rather than as prose in a prompt, for three
reasons. A prompt can be argued with and a table cannot. The Material Planner,
the generator and the checker must reason against the *same* rubric or the
checker is grading against a standard the generator never saw. And a stage list
in code can be validated — "this lesson explains a rule and then jumps straight
to free production" is a defect a model will not reliably notice in its own work.

Nothing here forces a stage. A 20-minute review lesson has no business running a
context-setting dialogue, and `required` below marks only the stages whose
absence means the lesson is not teaching its focus at all.
"""

from __future__ import annotations

from typing import Any

# --------------------------------------------------------------- stages ----

# The progression a grammar hour runs through. Order matters: the index is what
# the blueprint validator uses to catch a lesson that explains a rule and then
# asks for free production with nothing in between.
GRAMMAR_STAGES: dict[str, dict[str, Any]] = {
    "warm-up": {
        "order": 1,
        "purpose": "Activate what the learner already has — the vocabulary the "
                   "new grammar will attach to, or last lesson's unfinished work.",
        "cognitive_demand": "recall",
        "typical_operations": ["identify", "match"],
        "typical_exercise_types": ["matching", "labelling", "odd_one_out"],
        "typical_minutes": (5, 10),
        "image_value": "high",
        "required": False,
        "note": "Concrete nouns with pictures. The learner should succeed here; "
                "this stage buys attention for the stage that follows.",
    },
    "context": {
        "order": 2,
        "purpose": "Put the target grammar inside a situation the learner "
                   "recognises, before it is ever named.",
        "cognitive_demand": "comprehension",
        "typical_operations": ["identify", "respond"],
        "typical_exercise_types": ["dialogue_response", "gap_fill", "true_false"],
        "typical_minutes": (5, 10),
        "image_value": "high",
        "required": False,
        "note": "A short dialogue between two named people beats a paragraph of "
                "example sentences. The grammar should be visible but not the topic.",
    },
    "noticing": {
        "order": 3,
        "purpose": "The learner works out the pattern themselves from the data, "
                   "before the rule is stated.",
        "cognitive_demand": "analysis",
        "typical_operations": ["classify", "identify", "match"],
        "typical_exercise_types": ["classification", "matching", "odd_one_out"],
        "typical_minutes": (5, 8),
        "image_value": "conditional",
        "required": True,
        "note": "Present the forms; withhold the rule. A noticing task that "
                "states the answer above the exercise is an explanation slide.",
    },
    "explanation": {
        "order": 4,
        "purpose": "State the rule, once, as briefly as it can be stated correctly.",
        "cognitive_demand": "comprehension",
        "typical_operations": ["identify"],
        "typical_exercise_types": ["labelling", "gap_fill"],
        "typical_minutes": (5, 10),
        "image_value": "conditional",
        "required": True,
        "note": "A table, not paragraphs. At A1 the rule fits on one slide; if it "
                "does not, the lesson is teaching two rules and should teach one.",
    },
    "controlled-practice": {
        "order": 5,
        "purpose": "Recognition and single-form production, one unambiguous "
                   "answer per item, no other grammar in the way.",
        "cognitive_demand": "application",
        "typical_operations": ["choose", "classify", "complete", "match"],
        "typical_exercise_types": ["multiple_choice", "classification", "gap_fill",
                                   "matching", "true_false"],
        "typical_minutes": (8, 15),
        "image_value": "conditional",
        "required": True,
        "note": "Vary the operation between sets. Three gap-fills in a row is one "
                "exercise printed three times.",
    },
    "guided-practice": {
        "order": 6,
        "purpose": "The learner produces the form inside a supported frame — a "
                   "sentence to build, a form to transform, an error to fix.",
        "cognitive_demand": "application",
        "typical_operations": ["transform", "reorder", "correct", "complete"],
        "typical_exercise_types": ["transformation", "sentence_building",
                                   "error_correction", "gap_fill"],
        "typical_minutes": (8, 12),
        "image_value": "conditional",
        "required": False,
        "note": "The scaffold is what makes this different from free production: "
                "the words are given, the learner arranges or changes them.",
    },
    "communicative-practice": {
        "order": 7,
        "purpose": "Use the grammar to accomplish something. The learner should "
                   "not be able to complete the task without it.",
        "cognitive_demand": "synthesis",
        "typical_operations": ["produce", "respond"],
        "typical_exercise_types": ["role_play", "information_gap", "guessing_game",
                                   "open_production", "dialogue_response"],
        "typical_minutes": (8, 15),
        "image_value": "conditional",
        "required": False,
        "note": "The test of this stage: could the learner finish the task while "
                "avoiding the target grammar? If yes, the task is wrong.",
    },
    "review": {
        "order": 8,
        "purpose": "Restate the rule and the useful phrases, compactly, so the "
                   "learner leaves with something to take away.",
        "cognitive_demand": "recall",
        "typical_operations": ["identify", "complete"],
        "typical_exercise_types": ["gap_fill", "labelling"],
        "typical_minutes": (3, 6),
        "image_value": "none",
        "required": True,
        "note": "Summary and word list. The reference decks close on exactly this.",
    },
    "final-check": {
        "order": 9,
        "purpose": "The learner judges themselves against the stated objectives.",
        "cognitive_demand": "evaluation",
        "typical_operations": ["respond"],
        "typical_exercise_types": ["open_production", "true_false"],
        "typical_minutes": (3, 5),
        "image_value": "none",
        "required": False,
        "note": "Ask the objectives back as questions: 'Kannst du ...?'",
    },
}

STAGE_ORDER: list[str] = sorted(GRAMMAR_STAGES, key=lambda s: GRAMMAR_STAGES[s]["order"])

# The stages a grammar lesson is not a grammar lesson without.
REQUIRED_STAGES: set[str] = {s for s, v in GRAMMAR_STAGES.items() if v["required"]}

# At least one of these must appear, or the learner never produces anything.
PRODUCTION_STAGES: set[str] = {"guided-practice", "communicative-practice"}

# ------------------------------------------------- communication stages ----

# A communication hour is organised around a task, not around a form. The
# learner meets a situation, notices the language the speakers actually use,
# understands what it is FOR, practises it under support, then performs the task
# with the support taken away. The reference lesson is exactly this: a
# misunderstood name, four phrases that repair it, the alphabet as the resource
# needed to repair it, and a guessing game where spelling is the only way to win.
COMMUNICATION_STAGES: dict[str, dict[str, Any]] = {
    "warm-up": {
        "order": 1,
        "purpose": "Activate what the learner already brings to this situation.",
        "cognitive_demand": "recall",
        "typical_operations": ["respond", "identify"],
        "typical_exercise_types": ["dialogue_response", "picture_description"],
        "typical_minutes": (3, 6),
        "image_value": "conditional",
        "support_level": "high",
        "required": False,
        "note": "A question the learner can answer from their own life, not from "
                "German. The reference opens by asking whether their own language "
                "has a spelling alphabet.",
    },
    "situation": {
        "order": 2,
        "purpose": "Establish the real situation and show the language working in "
                   "it — a short dialogue with a genuine reason to happen.",
        "cognitive_demand": "comprehension",
        "typical_operations": ["identify", "complete", "respond"],
        "typical_exercise_types": ["dialogue_completion", "gap_fill", "true_false"],
        "typical_minutes": (5, 10),
        "image_value": "conditional",
        "support_level": "high",
        "required": True,
        "note": "The interaction needs a reason. In the reference a name is "
                "misheard, and that is what makes 'Wie bitte?' and 'Tut mir leid.' "
                "mean something instead of being phrases on a list.",
    },
    "noticing": {
        "order": 3,
        "purpose": "The learner picks out the expressions the speakers used and "
                   "works out what each one DOES.",
        "cognitive_demand": "analysis",
        "typical_operations": ["identify", "match"],
        "typical_exercise_types": ["phrase_function_match", "matching", "dialogue_completion"],
        "typical_minutes": (4, 8),
        "image_value": "none",
        "support_level": "high",
        "required": True,
        "note": "Function, not translation. The learner should be able to say what "
                "'Wie bitte?' is for, not merely what it means.",
    },
    "comprehension": {
        "order": 4,
        "purpose": "Check the learner understood the exchange and the meaning of "
                   "the expressions before practising them.",
        "cognitive_demand": "comprehension",
        "typical_operations": ["match", "choose", "identify"],
        "typical_exercise_types": ["matching", "multiple_choice", "true_false",
                                   "response_choice"],
        "typical_minutes": (4, 8),
        "image_value": "conditional",
        "support_level": "high",
        "required": False,
    },
    "language-resource": {
        "order": 5,
        "purpose": "Supply the vocabulary, forms or system the task needs — "
                   "recruited for the task, never taught for its own sake.",
        "cognitive_demand": "comprehension",
        "typical_operations": ["identify", "match", "respond"],
        "typical_exercise_types": ["labelling", "matching", "phrase_function_match"],
        "typical_minutes": (5, 12),
        "image_value": "high",
        "support_level": "high",
        "required": False,
        "note": "The reference teaches the whole alphabet here — because you "
                "cannot spell your name without it, not because the syllabus "
                "reached the letter A.",
    },
    "controlled-practice": {
        "order": 6,
        "purpose": "Practise the expressions accurately, with the situation still "
                   "given and the language still on the page.",
        "cognitive_demand": "application",
        "typical_operations": ["complete", "choose", "reorder", "match"],
        "typical_exercise_types": ["dialogue_completion", "response_choice",
                                   "dialogue_ordering", "gap_fill", "substitution"],
        "typical_minutes": (6, 12),
        "image_value": "conditional",
        "support_level": "medium",
        "required": True,
        "note": "Every item here must earn its place by preparing the final task. "
                "A disconnected grammar gap-fill does not.",
    },
    "guided-interaction": {
        "order": 7,
        "purpose": "The learner speaks, with the turns and the phrases provided — "
                   "high support, real exchange.",
        "cognitive_demand": "application",
        "typical_operations": ["respond", "produce"],
        "typical_exercise_types": ["dialogue_response", "interview", "substitution",
                                   "role_play"],
        "typical_minutes": (6, 12),
        "image_value": "conditional",
        "support_level": "medium",
        "required": False,
        "note": "Role A asks these three questions; Role B answers with these "
                "frames. The words are given; the exchange is real.",
    },
    "communicative-task": {
        "order": 8,
        "purpose": "The learner performs the task. Something must be achieved, and "
                   "the target language must be the way to achieve it.",
        "cognitive_demand": "synthesis",
        "typical_operations": ["produce", "respond"],
        "typical_exercise_types": ["information_gap", "role_play", "guessing_game",
                                   "interview", "problem_solving", "dictation"],
        "typical_minutes": (8, 15),
        "image_value": "high",
        "support_level": "low",
        "required": True,
        "note": "The test: could the learner finish this while avoiding the target "
                "language? If yes, it is not the task. The reference has the tutor "
                "spell a word and the learner guess which photograph it names — "
                "you cannot win that without listening to the spelling.",
    },
    "independent-communication": {
        "order": 9,
        "purpose": "The same kind of exchange again with the scaffolding removed.",
        "cognitive_demand": "synthesis",
        "typical_operations": ["produce", "respond"],
        "typical_exercise_types": ["role_play", "interview", "problem_solving",
                                   "open_production", "guessing_game"],
        "typical_minutes": (5, 12),
        "image_value": "conditional",
        "support_level": "independent",
        "required": False,
        "note": "Optional in a 60-minute A1 hour, expected by A2. The phrases come "
                "off the page here.",
    },
    "reflection": {
        "order": 10,
        "purpose": "The learner judges themselves against the can-do objectives, "
                   "and the tutor gives feedback on whether communication SUCCEEDED.",
        "cognitive_demand": "evaluation",
        "typical_operations": ["respond"],
        "typical_exercise_types": ["open_production", "true_false"],
        "typical_minutes": (3, 6),
        "image_value": "none",
        "support_level": "independent",
        "required": True,
        "note": "Ask the objectives back: 'Kannst du deinen Namen buchstabieren?'",
    },
}

# ---------------------------------------------------- vocabulary stages ----

# A vocabulary hour is not a word list with a quiz after it. The learner meets
# the words in use, works out what they mean, says them, and then has to GET
# THEM BACK without being shown them — retrieval is the stage everything else
# exists to make possible, and it is the one the old pipeline skipped entirely
# by testing recognition and calling it practice.
#
# The reference lesson recycles "Entschuldigung, ich habe eine Frage" through
# five separate stages. That is not repetition, it is the design.
VOCABULARY_STAGES: dict[str, dict[str, Any]] = {
    "warm-up": {
        "order": 1,
        "purpose": "Find what the learner already has. Cognates and borrowings "
                   "are free vocabulary and they buy confidence.",
        "cognitive_demand": "recall",
        "typical_operations": ["match", "identify"],
        "typical_exercise_types": ["matching", "labelling"],
        "typical_minutes": (3, 6),
        "image_value": "high",
        "support_level": "high",
        "retrieval_direction": "",
        "required": False,
        "note": "The reference opens with German words the learner already knows "
                "without knowing it: Hamburger, Hotel, Autobahn.",
    },
    "encounter": {
        "order": 2,
        "purpose": "Meet the words in a real utterance before meeting them as a "
                   "list — a short dialogue where somebody uses them for something.",
        "cognitive_demand": "comprehension",
        "typical_operations": ["complete", "identify"],
        "typical_exercise_types": ["dialogue_completion", "gap_fill"],
        "typical_minutes": (5, 8),
        "image_value": "conditional",
        "support_level": "high",
        "retrieval_direction": "context_to_word",
        "required": True,
        "note": "Context first. A word met in a sentence is learnt with its "
                "sentence attached; a word met in a glossary is learnt alone.",
    },
    "meaning": {
        "order": 3,
        "purpose": "Establish what each word means, unambiguously — picture, "
                   "situation or definition, not translation alone.",
        "cognitive_demand": "comprehension",
        "typical_operations": ["match", "identify"],
        "typical_exercise_types": ["matching", "labelling", "picture_word_match"],
        "typical_minutes": (5, 10),
        "image_value": "high",
        "support_level": "high",
        "retrieval_direction": "word_to_meaning",
        "required": True,
        "note": "For a gendered language the article is part of the word. 'die "
                "Frage, Pl. die Fragen' is the vocabulary item; 'Frage' is half of it.",
    },
    "pronunciation": {
        "order": 4,
        "purpose": "Hear it, say it, tell it apart from its neighbours.",
        "cognitive_demand": "application",
        "typical_operations": ["identify", "respond"],
        "typical_exercise_types": ["listen_repeat", "minimal_pair", "labelling"],
        "typical_minutes": (3, 6),
        "image_value": "none",
        "support_level": "high",
        "retrieval_direction": "",
        "required": False,
        "note": "Only where the sounds are actually a problem. Do not add a "
                "pronunciation stage to every lesson out of habit.",
    },
    "noticing": {
        "order": 5,
        "purpose": "See how the words group — by category, function, opposite or "
                   "situation. Grouping is what makes them retrievable later.",
        "cognitive_demand": "analysis",
        "typical_operations": ["classify", "match"],
        "typical_exercise_types": ["classification", "matching", "odd_one_out"],
        "typical_minutes": (4, 8),
        "image_value": "conditional",
        "support_level": "medium",
        "retrieval_direction": "",
        "required": False,
        "note": "The reference sorts every greeting and farewell into two columns, "
                "which is also how it recycles all ten words at once.",
    },
    "recognition": {
        "order": 6,
        "purpose": "Pick the right word when it is in front of you. The easiest "
                   "step, and not sufficient on its own.",
        "cognitive_demand": "application",
        "typical_operations": ["choose", "match", "identify"],
        "typical_exercise_types": ["multiple_choice", "matching", "true_false",
                                   "picture_word_match"],
        "typical_minutes": (4, 8),
        "image_value": "high",
        "support_level": "medium",
        "retrieval_direction": "picture_to_word",
        "required": True,
        "note": "A lesson that stops here has taught the learner to recognise a "
                "word they will not be able to produce.",
    },
    "retrieval": {
        "order": 7,
        "purpose": "Produce the word WITHOUT being shown it. This is the stage "
                   "that makes vocabulary stick.",
        "cognitive_demand": "application",
        "typical_operations": ["produce", "complete", "respond"],
        "typical_exercise_types": ["picture_naming", "gap_fill", "dialogue_response",
                                   "open_production"],
        "typical_minutes": (5, 10),
        "image_value": "high",
        "support_level": "low",
        "retrieval_direction": "picture_to_word",
        "required": True,
        "note": "The options must not be on the slide. If the answer is visible, "
                "this is recognition wearing retrieval's name.",
    },
    "contextual-use": {
        "order": 8,
        "purpose": "Put the word into a sentence the learner builds.",
        "cognitive_demand": "application",
        "typical_operations": ["complete", "reorder", "produce"],
        "typical_exercise_types": ["sentence_building", "gap_fill", "substitution",
                                   "open_production"],
        "typical_minutes": (5, 10),
        "image_value": "conditional",
        "support_level": "low",
        "retrieval_direction": "word_to_sentence",
        "required": False,
    },
    "communicative-use": {
        "order": 9,
        "purpose": "Need the words to get something done — ask for the objects, "
                   "greet the person, close the conversation.",
        "cognitive_demand": "synthesis",
        "typical_operations": ["produce", "respond"],
        "typical_exercise_types": ["role_play", "information_gap", "interview",
                                   "guessing_game", "picture_description"],
        "typical_minutes": (6, 12),
        "image_value": "high",
        "support_level": "low",
        "retrieval_direction": "situation_to_word",
        "required": False,
        "note": "'Ask your partner for three objects you need' beats 'use these "
                "five words in sentences'.",
    },
    "recycling": {
        "order": 10,
        "purpose": "Mixed retrieval across everything taught, in a different order "
                   "and a different task from where it was learnt.",
        "cognitive_demand": "recall",
        "typical_operations": ["produce", "classify", "match"],
        "typical_exercise_types": ["classification", "picture_naming", "matching",
                                   "guessing_game"],
        "typical_minutes": (4, 8),
        "image_value": "conditional",
        "support_level": "independent",
        "retrieval_direction": "meaning_to_word",
        "required": True,
        "note": "A word introduced once and never seen again was not taught.",
    },
    "reflection": {
        "order": 11,
        "purpose": "The learner checks themselves against the can-do objectives.",
        "cognitive_demand": "evaluation",
        "typical_operations": ["respond"],
        "typical_exercise_types": ["open_production", "true_false"],
        "typical_minutes": (3, 5),
        "image_value": "none",
        "support_level": "independent",
        "retrieval_direction": "",
        "required": True,
    },
}

# --------------------------------------------------- retrieval direction ----

# Which way the learner has to travel. The old pipeline only ever asked
# word -> meaning, which is the one direction that never produces a speaker.
RETRIEVAL_DIRECTIONS: dict[str, str] = {
    "word_to_meaning": "Given the word, supply the meaning. Recognition. Weakest.",
    "picture_to_word": "Given a picture, produce the word. Real retrieval.",
    "meaning_to_word": "Given the meaning or a definition, produce the word.",
    "context_to_word": "Given a sentence with a gap, produce the word that fits.",
    "situation_to_word": "Given a situation, produce what you would say.",
    "word_to_sentence": "Given the word, build a sentence that uses it.",
    "sentence_to_meaning": "Given a sentence, say what it means or does.",
    "function_to_phrase": "Given a communicative function, produce the phrase.",
}

# Directions that require the learner to GET THE WORD BACK rather than pick it
# out. A vocabulary lesson needs at least two of these or it has tested
# recognition and called it practice.
PRODUCTIVE_DIRECTIONS: set[str] = {
    "picture_to_word", "meaning_to_word", "context_to_word",
    "situation_to_word", "word_to_sentence", "function_to_phrase",
}
MIN_PRODUCTIVE_DIRECTIONS = 2

# ------------------------------------------------------ vocabulary load ----

# How many new items one hour can actually carry. Cognitive load, not ambition:
# a list of 25 A1 words produces a learner who half-knows 25 words.
MAX_NEW_ITEMS_BY_BAND: dict[str, int] = {
    "A1": 10, "A2": 14, "B1": 18, "B2": 22, "C1": 25, "C2": 25,
}

# A word introduced and never seen again was not taught. This is the share of
# the target vocabulary that must reappear after the stage that introduced it.
MIN_RECYCLED_SHARE = 0.6

# What kind of lexical item this is. They are learnt differently and a lesson
# that treats a fixed expression as a dictionary word teaches it wrongly.
LEXICAL_TYPES: dict[str, str] = {
    "word": "A single word, learnt with its article and plural where it has them.",
    "collocation": "Words that go together: 'einen Termin vereinbaren'.",
    "fixed_expression": "Learnt whole, not assembled: 'Guten Morgen!'.",
    "functional_phrase": "A whole utterance that does a job: 'Ich habe eine Frage.'",
}


# ------------------------------------------------------- reading stages ----

# A reading lesson has two targets, not one: what the text says, and HOW the
# learner got at it. The old pipeline only ever had the first, which is how it
# produced a text followed by ten questions that happened to be answerable.
#
# The order is the teaching. Gist before detail, always: a learner asked to
# understand every sentence on first contact has been taught that reading means
# decoding, which is the habit that makes them slow readers for years. The
# reference lesson also breaks its text into five parts, each with its own
# questions, rather than presenting one wall and interrogating it afterwards.
READING_STAGES: dict[str, dict[str, Any]] = {
    "pre-reading": {
        "order": 1,
        "purpose": "Activate what the learner knows about the topic and let them "
                   "predict. Build the mental context the text will land in.",
        "cognitive_demand": "recall",
        "typical_operations": ["respond", "identify", "produce"],
        "typical_exercise_types": ["picture_description", "open_production",
                                   "matching", "dialogue_response"],
        "typical_minutes": (4, 8),
        "image_value": "high",
        "support_level": "high",
        "reading_skill": "prediction",
        "required": True,
        "note": "Prepare, do not pre-answer. An image or a title to predict from; "
                "never a summary of what the text will say.",
    },
    "vocabulary-preparation": {
        "order": 2,
        "purpose": "Pre-teach ONLY the words without which the text is closed. "
                   "Everything else the learner should meet in it.",
        "cognitive_demand": "comprehension",
        "typical_operations": ["match", "complete", "classify"],
        "typical_exercise_types": ["matching", "gap_fill", "picture_word_match"],
        "typical_minutes": (4, 8),
        "image_value": "conditional",
        "support_level": "high",
        "reading_skill": "",
        "required": False,
        "note": "The goal is not to remove every hard word. It is to leave the "
                "learner able to read past the ones that remain.",
    },
    "gist": {
        "order": 3,
        "purpose": "One global question on a first fast read. What is this about, "
                   "who is it for, what is the best title.",
        "cognitive_demand": "comprehension",
        "typical_operations": ["choose", "identify", "respond"],
        "typical_exercise_types": ["multiple_choice", "true_false", "open_production",
                                   "dialogue_response"],
        "typical_minutes": (4, 8),
        "image_value": "none",
        "support_level": "medium",
        "reading_skill": "skimming",
        "required": True,
        "note": "Two or three questions at most. A detailed question here defeats "
                "the stage — the learner reads slowly and never learns to skim.",
    },
    "detail": {
        "order": 4,
        "purpose": "Locate specific information. Every answer sits somewhere "
                   "findable in the text.",
        "cognitive_demand": "application",
        "typical_operations": ["identify", "choose", "complete", "match"],
        "typical_exercise_types": ["multiple_choice", "true_false", "gap_fill",
                                   "matching", "dialogue_ordering"],
        "typical_minutes": (6, 12),
        "image_value": "none",
        "support_level": "medium",
        "reading_skill": "scanning",
        "required": True,
        "note": "The reference asks for true/false AND a correction when false, "
                "which forces the learner back into the text instead of guessing.",
    },
    "inference": {
        "order": 5,
        "purpose": "What the text means without saying — attitude, feeling, "
                   "purpose, what probably happened.",
        "cognitive_demand": "analysis",
        "typical_operations": ["choose", "produce", "respond"],
        "typical_exercise_types": ["multiple_choice", "open_production", "true_false"],
        "typical_minutes": (5, 10),
        "image_value": "none",
        "support_level": "medium",
        "reading_skill": "inference",
        "required": False,
        "note": "Only where the answer is NOT stated. An 'inference' question "
                "answerable by copying a sentence is a detail question mislabelled.",
    },
    "strategy": {
        "order": 6,
        "purpose": "Practise the reading strategy itself, explicitly — what 'she' "
                   "refers to, how the text is organised, how to guess a word.",
        "cognitive_demand": "analysis",
        "typical_operations": ["identify", "match", "reorder", "choose"],
        "typical_exercise_types": ["multiple_choice", "matching", "dialogue_ordering",
                                   "labelling"],
        "typical_minutes": (4, 8),
        "image_value": "none",
        "support_level": "medium",
        "reading_skill": "",
        "required": False,
        "note": "This is the stage that teaches reading rather than testing it. "
                "It should practise the skill the lesson declared.",
    },
    "vocabulary-in-context": {
        "order": 7,
        "purpose": "Work out an unknown word from what surrounds it, and say what "
                   "gave it away.",
        "cognitive_demand": "analysis",
        "typical_operations": ["choose", "identify", "produce"],
        "typical_exercise_types": ["multiple_choice", "matching", "open_production"],
        "typical_minutes": (4, 8),
        "image_value": "none",
        "support_level": "medium",
        "reading_skill": "context_inference",
        "required": False,
        "note": "'Which meaning fits here, and what told you?' The second half is "
                "the part that teaches the strategy.",
    },
    "post-reading": {
        "order": 8,
        "purpose": "Do something with what was read — react, compare, summarise, "
                   "decide, retell.",
        "cognitive_demand": "synthesis",
        "typical_operations": ["produce", "respond"],
        "typical_exercise_types": ["open_production", "role_play", "interview",
                                   "problem_solving", "dialogue_response"],
        "typical_minutes": (6, 12),
        "image_value": "conditional",
        "support_level": "low",
        "reading_skill": "",
        "required": False,
        "note": "A lesson that ends at 'here are the answers' has treated reading "
                "as a test. The reference ends on the learner's own city.",
    },
    "review": {
        "order": 9,
        "purpose": "The learner judges themselves against the reading objectives.",
        "cognitive_demand": "evaluation",
        "typical_operations": ["respond"],
        "typical_exercise_types": ["open_production", "true_false"],
        "typical_minutes": (3, 5),
        "image_value": "none",
        "support_level": "independent",
        "reading_skill": "",
        "required": True,
    },
}

# The reading abilities a lesson can set out to build. One is primary, named on
# the blueprint, and at least one activity must actually practise it.
READING_SKILLS: dict[str, str] = {
    "skimming": "Read fast for the general idea.",
    "scanning": "Search for specific information without reading everything.",
    "main_idea": "Identify the central message of a text or paragraph.",
    "specific_detail": "Locate a stated fact.",
    "sequencing": "Work out the order events happened in.",
    "reference": "Work out what 'he', 'this', 'they' point back to.",
    "context_inference": "Work out an unknown word from what surrounds it.",
    "inference": "Understand what is meant but not stated.",
    "prediction": "Use title, image or context to anticipate content.",
    "text_structure": "Understand how the information is organised.",
    "writer_purpose": "Work out why the text was written.",
    "fact_opinion": "Tell a stated fact from a stated view.",
    "summarising": "Reduce the text to its essentials.",
}

# Genres by band. Chosen because the genre supports the objective, not because
# an article is the default shape of a reading text.
TEXT_TYPES_BY_BAND: dict[str, list[str]] = {
    "A1": ["short_message", "simple_email", "notice", "sign", "menu", "timetable",
           "advertisement", "short_dialogue", "personal_profile", "social_post"],
    "A2": ["email", "short_article", "message", "advertisement", "blog_post",
           "review", "instructions", "short_story", "description", "short_dialogue"],
    "B1": ["article", "blog_post", "interview", "opinion_text", "report", "review",
           "narrative", "informational_text"],
    "B2": ["article", "editorial", "essay_excerpt", "report", "interview",
           "argument", "analytical_text", "informational_text"],
    "C1": ["editorial", "essay_excerpt", "analytical_text", "report", "argument"],
    "C2": ["editorial", "essay_excerpt", "analytical_text", "report", "argument"],
}

# How long a text can be before the learner stops reading and starts decoding.
TEXT_LENGTH_BY_BAND: dict[str, tuple[int, int]] = {
    "A1": (25, 90), "A2": (80, 180), "B1": (150, 320),
    "B2": (250, 500), "C1": (350, 700), "C2": (400, 800),
}

# New words a text may carry before it stops being readable. Above this the
# learner is translating, not reading.
NEW_WORD_BUDGET_BY_BAND: dict[str, int] = {
    "A1": 5, "A2": 7, "B1": 10, "B2": 14, "C1": 18, "C2": 20,
}

# What to do about a hard word. The point is not to remove every one — it is to
# leave the learner able to read past the ones that stay.
VOCABULARY_SUPPORT: dict[str, str] = {
    "essential": "Comprehension fails without it. Pre-teach it.",
    "useful": "Helps but is not load-bearing. Gloss it if there is room.",
    "inferable": "Recoverable from context. Leave it, and make inferring it a task.",
    "unnecessary": "Not needed for any question. Do not teach it.",
}

# Do not write fifteen questions because the text contains fifteen facts.
MAX_QUESTIONS_BY_BAND: dict[str, int] = {
    "A1": 8, "A2": 10, "B1": 12, "B2": 14, "C1": 16, "C2": 16,
}

# A set of questions that all test one skill is a test, not a lesson.
MIN_DISTINCT_READING_SKILLS = 2


# Which stage set a lesson focus is built from.
STAGES_BY_FOCUS: dict[str, dict[str, dict[str, Any]]] = {
    "grammar": GRAMMAR_STAGES,
    "communication": COMMUNICATION_STAGES,
    # A speaking lesson is a communication lesson whose task ranges over the
    # whole chapter. Same stages; a second catalogue would drift from this one
    # the first time either was edited.
    "speaking": COMMUNICATION_STAGES,
    "vocabulary": VOCABULARY_STAGES,
    "reading": READING_STAGES,
}

COMMUNICATION_STAGE_ORDER: list[str] = sorted(
    COMMUNICATION_STAGES, key=lambda s: COMMUNICATION_STAGES[s]["order"]
)

REQUIRED_STAGES_BY_FOCUS: dict[str, set[str]] = {
    focus: {s for s, v in stages.items() if v["required"]}
    for focus, stages in STAGES_BY_FOCUS.items()
}

# At least one of each pair must appear, or the lesson stops short of its point.
ONE_OF_REQUIRED_BY_FOCUS: dict[str, set[str]] = {
    "grammar": {"guided-practice", "communicative-practice"},
    "communication": {"guided-interaction", "independent-communication"},
    "speaking": {"guided-interaction", "independent-communication"},
    "vocabulary": {"contextual-use", "communicative-use"},
    "reading": {"post-reading", "inference", "strategy", "vocabulary-in-context"},
}

# ------------------------------------------------------ support scaffold ----

# How much the learner is holding onto. A communication lesson is judged partly
# on this falling: the final task must be less supported than the practice that
# prepared it, or the learner never actually communicated, they read aloud.
SUPPORT_LEVELS: dict[str, int] = {
    "high": 3, "medium": 2, "low": 1, "independent": 0,
}


def stages_for(focus: str) -> dict[str, dict[str, Any]]:
    """The stage set for one lesson focus."""
    return STAGES_BY_FOCUS.get(focus, GRAMMAR_STAGES)


def stage_order(focus: str, stage: str) -> int:
    """Where a stage sits in its focus's progression. 0 if it does not belong."""
    return stages_for(focus).get(stage, {}).get("order", 0)


# ------------------------------------------------------------ operations ----

# The cognitive operation an exercise asks for. This is the axis that variety is
# measured on: ten items are ten exercises only if they are not all "complete".
COGNITIVE_OPERATIONS: dict[str, str] = {
    "identify": "Point at the instance. 'Which word is feminine?'",
    "choose": "Pick from given alternatives. 'der or die?'",
    "match": "Pair items across two sets. Word to picture, question to answer.",
    "classify": "Sort items into categories. Nouns into three gender columns.",
    "complete": "Supply a missing element in a given frame. Gap-fill.",
    "transform": "Change a given form into another. Singular to plural.",
    "reorder": "Arrange given pieces into a well-formed whole. Scrambled sentence.",
    "correct": "Find and repair a deliberate error.",
    "produce": "Generate language from meaning, not from a frame.",
    "respond": "Answer, react or take a turn in an exchange.",
}

# ---------------------------------------------------------- exercise types ----

# What each exercise type is for, what operation it exercises, and what it must
# structurally contain. The generator writes against `requires`; the checker
# validates against it. One table, two readers.
EXERCISE_TYPES: dict[str, dict[str, Any]] = {
    "matching": {
        "operation": "match", "skill": "recognition",
        "requires": ["two sets of the same length", "exactly one correct pairing per item"],
        "good_for": ["warm-up", "noticing", "controlled-practice", "meaning",
                     "recognition", "comprehension", "language-resource",
                     "vocabulary-preparation", "strategy", "recycling"],
        "items": (4, 8),
    },
    "labelling": {
        "operation": "identify", "skill": "recognition",
        "requires": ["a picture or a form to label", "one label per target"],
        "good_for": ["warm-up", "explanation", "review"],
        "items": (3, 8),
    },
    "multiple_choice": {
        "operation": "choose", "skill": "recognition",
        "requires": ["2-4 options per item", "exactly one defensible answer",
                     "distractors that are plausible, not absurd"],
        "good_for": ["controlled-practice", "context", "gist", "detail",
                     "inference", "vocabulary-in-context", "strategy",
                     "recognition", "comprehension"],
        "items": (2, 8),
    },
    "true_false": {
        "operation": "choose", "skill": "comprehension",
        "requires": ["a statement decidable from the material shown"],
        "good_for": ["context", "controlled-practice", "final-check", "gist",
                     "detail", "inference", "comprehension", "reflection",
                     "review"],
        "items": (2, 6),
    },
    "classification": {
        "operation": "classify", "skill": "recognition",
        "requires": ["2-4 named categories", "every item belongs to exactly one"],
        "good_for": ["noticing", "controlled-practice", "recycling",
                     "recognition", "meaning"],
        "items": (6, 12),
    },
    "odd_one_out": {
        "operation": "identify", "skill": "recognition",
        "requires": ["one item differing on the taught dimension and no other"],
        "good_for": ["warm-up", "noticing"],
        "items": (3, 5),
    },
    "gap_fill": {
        "operation": "complete", "skill": "controlled_production",
        "requires": ["one gap per item", "a sentence that constrains the answer to one form"],
        "good_for": ["context", "explanation", "controlled-practice",
                     "guided-practice", "review", "encounter", "situation",
                     "vocabulary-preparation", "retrieval", "contextual-use"],
        "items": (4, 8),
    },
    "transformation": {
        "operation": "transform", "skill": "controlled_production",
        "requires": ["a given form", "a named direction of change", "a worked first item"],
        "good_for": ["guided-practice"],
        "items": (4, 8),
    },
    "sentence_building": {
        "operation": "reorder", "skill": "guided_production",
        "requires": ["scrambled pieces that make exactly one natural sentence",
                     "a worked first item"],
        "good_for": ["guided-practice", "contextual-use"],
        "items": (4, 6),
    },
    "error_correction": {
        "operation": "correct", "skill": "guided_production",
        "requires": ["exactly one error per item", "an error a learner at this level "
                     "actually makes, not an invented one"],
        "good_for": ["guided-practice"],
        "items": (4, 6),
    },
    "dialogue_response": {
        "operation": "respond", "skill": "guided_production",
        "requires": ["a prompt turn", "a response the target grammar is needed for"],
        "good_for": ["context", "communicative-practice", "warm-up",
                     "guided-interaction", "retrieval", "post-reading"],
        "items": (3, 6),
    },
    "role_play": {
        "operation": "respond", "skill": "communication",
        "requires": ["two named roles", "what each role must do",
                     "the phrases each role may need"],
        "good_for": ["communicative-practice"],
        "items": (1, 2),
    },
    "information_gap": {
        "operation": "produce", "skill": "communication",
        "requires": ["each partner holds what the other lacks",
                     "the target grammar is the only way to ask for it"],
        "good_for": ["communicative-practice"],
        "items": (1, 2),
    },
    "guessing_game": {
        "operation": "respond", "skill": "communication",
        "requires": ["a hidden item", "a question form the learner must use to guess"],
        "good_for": ["communicative-practice"],
        "items": (1, 2),
    },
    # ---- communication ----
    "dialogue_completion": {
        "operation": "complete", "skill": "comprehension",
        "requires": ["a dialogue with a real reason to happen",
                     "gaps on the target expressions, not on random words"],
        "good_for": ["situation", "encounter", "controlled-practice", "noticing"],
        "items": (3, 6),
    },
    "phrase_function_match": {
        "operation": "match", "skill": "comprehension",
        "requires": ["the phrase on one side, what it DOES on the other",
                     "functions named as actions: 'asking for repetition'"],
        "good_for": ["noticing", "comprehension", "language-resource"],
        "items": (4, 8),
    },
    "response_choice": {
        "operation": "choose", "skill": "comprehension",
        "requires": ["a turn to respond to", "2-4 responses, one appropriate",
                     "distractors wrong in register or function, not in grammar"],
        "good_for": ["comprehension", "controlled-practice"],
        "items": (4, 6),
    },
    "dialogue_ordering": {
        "operation": "reorder", "skill": "comprehension",
        "requires": ["turns that make exactly one coherent exchange"],
        "good_for": ["controlled-practice", "comprehension"],
        "items": (4, 8),
    },
    "substitution": {
        "operation": "produce", "skill": "guided_production",
        "requires": ["a frame held constant", "the pieces that vary supplied"],
        "good_for": ["controlled-practice", "guided-interaction", "contextual-use"],
        "items": (3, 6),
    },
    "interview": {
        "operation": "respond", "skill": "communication",
        "requires": ["questions the learner asks a real person",
                     "answers that are not predictable in advance"],
        "good_for": ["guided-interaction", "communicative-task",
                     "independent-communication", "communicative-use"],
        "items": (1, 2),
    },
    "problem_solving": {
        "operation": "produce", "skill": "communication",
        "requires": ["a problem with more than one solution",
                     "the target language needed to agree on one"],
        "good_for": ["communicative-task", "independent-communication"],
        "items": (1, 2),
    },
    "dictation": {
        "operation": "respond", "skill": "communication",
        "requires": ["something said that must be written or acted on",
                     "the learner cannot see what was said"],
        "good_for": ["communicative-task", "retrieval"],
        "items": (1, 2),
    },
    "picture_description": {
        "operation": "produce", "skill": "communication",
        "requires": ["a scene with enough in it to describe",
                     "what the learner must communicate about it"],
        "good_for": ["warm-up", "communicative-task", "communicative-use"],
        "items": (1, 3),
    },
    "find_differences": {
        "operation": "produce", "skill": "communication",
        "requires": ["two pictures, each partner seeing only one",
                     "differences nameable with the target language"],
        "good_for": ["communicative-task", "communicative-use"],
        "items": (1, 2),
    },
    # ---- vocabulary ----
    "picture_word_match": {
        "operation": "match", "skill": "recognition",
        "requires": ["one unambiguous picture per word",
                     "no two pictures that could take the same word"],
        "good_for": ["meaning", "recognition", "warm-up"],
        "items": (4, 8),
    },
    "picture_naming": {
        "operation": "produce", "skill": "controlled_production",
        "requires": ["a picture and NO word list on the slide",
                     "a concept with exactly one natural name at this level"],
        "good_for": ["retrieval", "recycling"],
        "items": (4, 8),
    },
    "listen_repeat": {
        "operation": "respond", "skill": "recognition",
        "requires": ["the sound written as well as spoken",
                     "a phonological feature worth attending to"],
        "good_for": ["pronunciation"],
        "items": (3, 6),
    },
    "minimal_pair": {
        "operation": "identify", "skill": "recognition",
        "requires": ["two forms differing in exactly one sound"],
        "good_for": ["pronunciation"],
        "items": (3, 6),
    },
    "open_production": {
        "operation": "produce", "skill": "communication",
        "requires": ["a meaning to express, not a form to fill",
                     "acceptable answers described, since there is more than one"],
        "good_for": ["communicative-practice", "final-check", "reflection",
                     "review", "pre-reading", "post-reading", "retrieval",
                     "contextual-use", "communicative-use", "inference",
                     "vocabulary-in-context", "independent-communication"],
        "items": (1, 4),
    },
}

# --------------------------------------------------------- the progression ----

# recognition -> comprehension -> controlled production -> guided production ->
# communication. The rank is what catches a lesson that explains a rule and then
# asks for free speech: a jump of more than one rank with nothing between.
SKILL_LADDER: dict[str, int] = {
    "recognition": 1,
    "comprehension": 2,
    "controlled_production": 3,
    "guided_production": 4,
    "communication": 5,
}

MAX_SKILL_JUMP = 2

# ---------------------------------------------------------------- images ----

# Whether a picture materially improves the activity, decided by what the
# activity is rather than by whether a picture is possible. The rule the old
# pipeline lacked: an image on a rule table teaches nothing and costs attention.
#
# "high"        - the activity is about concrete meaning; a picture carries it.
# "conditional" - only if the item is a concrete, depictable noun or situation.
# "none"        - a picture here is decoration.
IMAGE_VALUE_BY_TYPE: dict[str, str] = {
    "matching": "high", "labelling": "high", "odd_one_out": "high",
    "picture_word_match": "high", "picture_naming": "high",
    "picture_description": "high", "find_differences": "high",
    "dialogue_completion": "conditional", "phrase_function_match": "none",
    "response_choice": "conditional", "dialogue_ordering": "none",
    "substitution": "conditional", "interview": "conditional",
    "problem_solving": "conditional", "dictation": "conditional",
    "listen_repeat": "none", "minimal_pair": "none",
    "dialogue_response": "conditional", "role_play": "conditional",
    "guessing_game": "conditional", "information_gap": "conditional",
    "multiple_choice": "conditional", "true_false": "conditional",
    "classification": "conditional", "gap_fill": "conditional",
    "open_production": "conditional",
    "transformation": "none", "sentence_building": "none", "error_correction": "none",
}

# Exercise types where the picture IS the item: the learner is asked about one
# specific image, so each item needs its own. A single composite grid cannot be
# counted, cannot be numbered reliably, and lets the same object appear twice —
# which is how a five-word matching task got a six-panel image containing two
# identical chairs. The reference decks always use N separate numbered
# photographs for these.
ONE_IMAGE_PER_ITEM_TYPES = {
    "picture_word_match", "picture_naming", "matching", "labelling",
    "odd_one_out", "find_differences",
}

# Abstractions no photograph can show. The rule they carry is NOT "use no
# image" — it is "photograph a concrete instance instead". The reference deck
# illustrates the three genders with a picture of a man, a woman and a child,
# because that is what der/die/das look like when something has to be pointed
# at. Asking for a picture of "the definite article" is how the old pipeline got
# a cartoon owl in front of a blank chalkboard.
UNDEPICTABLE = {
    "article", "artikel", "gender", "genus", "grammar", "grammatik", "rule", "regel",
    "plural", "singular", "case", "kasus", "tense", "conjugation", "declension",
    "ending", "endung", "word order", "syntax", "meaning", "understanding",
}


# The five jobs a picture can do in a language lesson. Naming the type is what
# stops every image being the same request with a different noun in it.
VISUAL_TYPES: dict[str, str] = {
    "direct_concept": "One thing, unmistakable. The learner names it. 'Apfel'.",
    "context_scene": "The word in use — someone ordering a coffee, for 'bestellen'.",
    "contrast": "Two things side by side differing on the taught dimension.",
    "categorisation": "A set that sorts into the groups being taught.",
    "communicative_scene": "A scene the learner must ask questions about. The one "
                           "type where ambiguity is the point rather than a defect.",
}

# Where a picture's ambiguity is a feature. A communicative scene that gives
# everything away leaves nothing to ask about; a vocabulary picture that gives
# nothing away is an unanswerable question.
AMBIGUITY_MAY_BE_INTENTIONAL: set[str] = {"communicative_scene"}


# The handful of slides a published deck genuinely leaves unillustrated: the
# closing summary, the word list, the self-assessment. Everything else in the
# reference decks carries a picture, and so should everything here.
NO_IMAGE_STAGES = {"review", "reflection", "final-check"}


def image_earns_its_place(stage: str, exercise_type: str, target_concept: str,
                          focus: str = "grammar") -> dict:
    """Decide what picture this activity needs, and say why.

    The default is YES. Every content slide of a published lesson carries an
    image — the reference decks illustrate the vocabulary, the dialogues, the
    rule tables and the practice, and only the closing summary and the word list
    go without. A wall of text is not the product, however good the text is.

    What varies is not whether to use a picture but WHAT KIND:

      direct_concept       one thing, unmistakable, the learner names it
      context_scene        the language in use, for a dialogue or a situation
      contrast             two things differing on the taught dimension
      categorisation       a set that sorts into the groups being taught
      communicative_scene  something to talk about, where ambiguity is the point

    And for a grammatical abstraction the answer is never "no picture". It is
    "photograph a concrete instance": the reference deck illustrates der / die /
    das with a man, a woman and a child, because that is what the three genders
    look like when something has to be pointed at.
    """
    concept = (target_concept or "").strip().lower()
    stages = stages_for(focus)
    stage_value = stages.get(stage, {}).get("image_value", "conditional")
    type_value = IMAGE_VALUE_BY_TYPE.get(exercise_type, "conditional")

    if stage in NO_IMAGE_STAGES:
        return {"use_image": False, "confidence": "high", "visual_type": "",
                "reason": f"{stage!r} is a closing summary or self-assessment — "
                          "the reference decks leave exactly these unillustrated."}

    if any(term in concept for term in UNDEPICTABLE):
        return {
            "use_image": True, "confidence": "high",
            "visual_type": "direct_concept", "ambiguity": "very_low",
            "requires_concrete_instance": True,
            "reason": f"{target_concept!r} cannot be photographed, but it can be "
                      "SHOWN. Set target_concept to a concrete example that "
                      "instantiates it — the three genders become a man, a woman "
                      "and a child — never the abstraction itself.",
        }

    # What kind of picture this would have to be, which is also the answer to
    # "how much ambiguity is acceptable here".
    if exercise_type in {"picture_description", "find_differences", "information_gap",
                         "guessing_game", "role_play", "interview", "problem_solving"}:
        visual_type = "communicative_scene"
    elif exercise_type in {"classification", "odd_one_out"}:
        visual_type = "categorisation"
    elif stage in {"encounter", "situation", "context"}:
        visual_type = "context_scene"
    else:
        visual_type = "direct_concept"

    intentional = visual_type in AMBIGUITY_MAY_BE_INTENTIONAL

    if "none" in (stage_value, type_value):
        # The learner is manipulating given forms rather than identifying a
        # thing, so the picture is not the prompt. It still belongs on the
        # slide: a concrete scene of the situation the language is used in.
        return {"use_image": True, "confidence": "medium",
                "visual_type": "context_scene", "ambiguity": "low",
                "reason": f"{stage!r} with a {exercise_type!r} task works on "
                          "language on the page, so the picture is not the "
                          "prompt — give it a context scene showing the "
                          "situation these sentences belong to."}

    if stage_value == "high" or type_value == "high":
        if intentional:
            return {"use_image": True, "confidence": "high",
                    "visual_type": visual_type, "ambiguity": "intentional",
                    "reason": "the picture is what the learner has to talk about; "
                              "it should withhold enough that a question is needed "
                              "to resolve it."}
        return {"use_image": True, "confidence": "high",
                "visual_type": visual_type, "ambiguity": "very_low",
                "reason": f"{stage!r} turns on concrete meaning — the picture IS "
                          "the prompt, and the word is what the learner supplies, "
                          "so it must have exactly one natural reading."}

    if not concept:
        return {"use_image": True, "confidence": "low",
                "visual_type": "context_scene", "ambiguity": "low",
                "reason": "no target concept named. Name one — the situation this "
                          "activity happens in will do — rather than leaving the "
                          "slide bare."}

    return {"use_image": True, "confidence": "medium", "visual_type": visual_type,
            "ambiguity": "intentional" if intentional else "low",
            "reason": f"{target_concept!r} is concrete and depictable, and a "
                      "picture removes the need to translate it."}


# ----------------------------------------------------------- the ceilings ----

# More material is not better material. These are the ceilings the blueprint is
# validated against — six excellent exercises over twenty repetitive ones.
MAX_SLOTS_PER_STAGE = 3

# The floor. "Do not overgenerate" was read as licence to produce eight thin
# slides, which is the opposite failure and just as bad: the reference decks run
# 38-41 slides of real content for the same hour. Six EXCELLENT exercises still
# means six, and a 60-minute lesson that fits on one page is not a lesson.
MIN_SLOTS_PER_LESSON = 7
MIN_EXERCISE_ITEMS_PER_LESSON = 18
MIN_LESSON_MINUTES = 45
MAX_EXERCISE_ITEMS_PER_LESSON = 45
MAX_IMAGES_PER_LESSON = 34
MIN_DISTINCT_OPERATIONS = 4
# No single cognitive operation may be more than this share of the exercise sets.
#
# Measured over the PRACTICE stages only. The rule exists to catch six exercises
# that all ask the learner to do the same thing, which is a defect. It is not a
# defect when the last three activities of a communication lesson all ask the
# learner to produce language — producing is what those stages are for, and
# penalising them would push a lesson towards ending on a matching exercise.
MAX_OPERATION_SHARE = 0.4

# The stages where repeating the operation is the point rather than a failure:
# the learner is finally doing the thing the hour was building towards.
PAYOFF_DEMANDS = {"synthesis", "evaluation"}


def is_payoff_stage(focus: str, stage: str) -> bool:
    """Is this a stage where the learner performs rather than practises?"""
    return stages_for(focus).get(stage, {}).get("cognitive_demand") in PAYOFF_DEMANDS


# Reading comprehension stages measure their variety on a different axis. A
# question set is naturally "choose" — multiple choice and true/false are what
# comprehension questions look like — and what must vary is the READING SKILL:
# skimming, scanning, inference. Applying the operation rule here would push a
# reading lesson towards sentence-reordering tasks to satisfy a counter.
READING_COMPREHENSION_STAGES = {"gist", "detail", "inference",
                                "vocabulary-in-context", "strategy"}


def operation_variety_exempt(focus: str, stage: str) -> bool:
    """Is this stage exempt from the cognitive-operation variety rule?

    Two cases, both of them design rather than defect: the payoff stages, where
    repeating "produce" is the whole point, and reading's comprehension stages,
    which vary on reading skill instead.
    """
    if is_payoff_stage(focus, stage):
        return True
    return focus == "reading" and stage in READING_COMPREHENSION_STAGES


def stage_catalogue(focus: str = "grammar") -> dict:
    """The stage list for one lesson focus, with what each stage is for."""
    stages = STAGES_BY_FOCUS.get(focus)
    if stages is None:
        return {"focus": focus, "stages": {},
                "note": f"No staged blueprint for focus {focus!r}. Defined for "
                        f"{sorted(STAGES_BY_FOCUS)}.",
                "available": sorted(STAGES_BY_FOCUS)}
    return {
        "focus": focus,
        "order": sorted(stages, key=lambda x: stages[x]["order"]),
        "required": sorted(REQUIRED_STAGES_BY_FOCUS.get(focus, set())),
        "one_of_required": sorted(ONE_OF_REQUIRED_BY_FOCUS.get(focus, set())),
        "stages": stages,
    }
