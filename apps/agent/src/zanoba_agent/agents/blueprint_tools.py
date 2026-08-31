"""Tools for the Material Planner.

Every one of these reads the rubric or measures a draft. None of them writes
material — the planner's job is to specify, and a planner that could also
generate would stop specifying and start writing, which is the jump this whole
stage exists to prevent.

`check_blueprint` is the important one. It runs the same validators the schema
runs, but returns them as a report instead of raising, so the planner can fix
its own draft before committing it rather than failing the run.
"""

from __future__ import annotations

import json
from typing import Any

from pydantic import ValidationError

from ..material.rubric import (
    COGNITIVE_OPERATIONS,
    EXERCISE_TYPES,
    LEXICAL_TYPES,
    MAX_EXERCISE_ITEMS_PER_LESSON,
    MAX_IMAGES_PER_LESSON,
    MAX_NEW_ITEMS_BY_BAND,
    MAX_QUESTIONS_BY_BAND,
    NEW_WORD_BUDGET_BY_BAND,
    PRODUCTIVE_DIRECTIONS,
    READING_SKILLS,
    RETRIEVAL_DIRECTIONS,
    SKILL_LADDER,
    STAGES_BY_FOCUS,
    SUPPORT_LEVELS,
    TEXT_LENGTH_BY_BAND,
    TEXT_TYPES_BY_BAND,
    VISUAL_TYPES,
    VOCABULARY_SUPPORT,
    image_earns_its_place,
    stage_catalogue,
)


def _load(raw: Any) -> dict:
    if isinstance(raw, dict):
        return raw
    try:
        return json.loads(raw)
    except (TypeError, ValueError):
        return {}


def get_stage_catalogue(focus: str = "grammar") -> dict:
    """Return the stages a lesson of this focus can be built from.

    Args:
      focus: The lesson's dominant skill, e.g. "grammar".

    Returns:
      Every stage with what it is for, what the learner does in it, which
      exercise types suit it, how long it usually takes and whether a picture
      helps. Also which stages are required and which pair is one-of-required.

      Not every stage belongs in every lesson. Pick the ones this grammar point,
      this level and this student's diagnosis actually call for.
    """
    return stage_catalogue(focus)


def get_exercise_types(stage: str = "") -> dict:
    """Return the exercise types available, and what each one is structurally.

    Args:
      stage: Optional stage to filter by, e.g. "controlled-practice". Empty
        returns every type.

    Returns:
      Each type with the cognitive operation it exercises, the skill level it
      sits at, what it must structurally contain, and its sensible item range.
      Choose by the operation you want the learner to perform, not by which type
      is most familiar — that is how a lesson ends up as six gap-fills.
    """
    types = EXERCISE_TYPES
    if stage:
        types = {k: v for k, v in EXERCISE_TYPES.items() if stage in v["good_for"]}
        if not types:
            known = sorted({s for stages in STAGES_BY_FOCUS.values() for s in stages})
            return {"error": f"No exercise types listed for stage {stage!r}.",
                    "known_stages": known}
    return {
        "stage": stage or "all",
        "exercise_types": types,
        "cognitive_operations": COGNITIVE_OPERATIONS,
        "skill_ladder": SKILL_LADDER,
        "rule": "Vary the cognitive operation between consecutive practice slots. "
                "Two sets that ask the learner to do the same thing are one set.",
    }


def should_this_have_an_image(stage: str, exercise_type: str,
                              target_concept: str, focus: str = "grammar") -> dict:
    """Decide whether a picture materially improves one activity.

    Args:
      stage: The blueprint stage, e.g. "controlled-practice".
      exercise_type: The exercise type, e.g. "matching".
      target_concept: What the picture would be of, e.g. "Garten".
      focus: The lesson focus — "grammar", "communication", "vocabulary" or
        "reading". The four want different things from a picture.

    Returns:
      Whether to use an image and the reason, either way. The question is never
      whether an image can be generated — it always can. It is whether the
      learner understands something faster because one is there.

      A concrete noun the learner must name: yes, the picture is the prompt. A
      table of article forms, or a scrambled-sentence task: no. A picture of a
      grammatical abstraction is refused outright, because no photograph shows
      "the definite article" and what comes back is decoration.

      The answer also names the VISUAL TYPE the picture would have to be, and
      how much ambiguity it may carry. For a vocabulary target: none, the learner
      has to name it. For a communicative scene: ambiguity is the point, because
      what the picture withholds is what the learner has to ask about.
    """
    return image_earns_its_place(stage, exercise_type, target_concept, focus)


def get_visual_types() -> dict:
    """Return the kinds of job a picture can do, so the right one is requested.

    Returns:
      The five visual types with what each is for. Naming the type is what stops
      every image request being the same sentence with a different noun in it —
      a direct concept image, a context scene and a scene to talk about are three
      different briefs, and only one of them may be ambiguous.
    """
    return {"visual_types": VISUAL_TYPES,
            "rule": "Ambiguity is a defect everywhere except a communicative "
                    "scene, where it is what creates the question."}


def get_retrieval_directions() -> dict:
    """Return the ways a vocabulary item can be asked for.

    Returns:
      Every direction, and which of them require the learner to PRODUCE the word
      rather than pick it out. A vocabulary lesson needs at least two productive
      directions; one that only ever asks word_to_meaning has tested recognition
      and called it practice.
    """
    return {"directions": RETRIEVAL_DIRECTIONS,
            "productive": sorted(PRODUCTIVE_DIRECTIONS),
            "rule": "Recognition is not retrieval. The learner must get the word "
                    "back without it being on the slide."}


def get_vocabulary_budget(band: str) -> dict:
    """Return how many new lexical items one hour at this band can carry.

    Args:
      band: CEFR band, e.g. "A1".

    Returns:
      The ceiling on new items, and the lexical types to choose between. A
      learner given 25 words half-learns 25 words; prefer eight they can use.
    """
    key = (band or "").strip().upper()
    return {
        "band": key,
        "max_new_items": MAX_NEW_ITEMS_BY_BAND.get(key, 12),
        "lexical_types": LEXICAL_TYPES,
        "rule": "Teach nouns with their article and plural. 'die Frage, Pl. die "
                "Fragen' is the item; 'Frage' is half of it.",
    }


def get_reading_skills() -> dict:
    """Return the reading abilities a lesson can set out to build.

    Returns:
      Every reading skill with what it means. A reading lesson has two targets —
      what the text says, and how the learner got at it — and this is the second
      one. Name a primary skill and make sure an activity actually practises it.
    """
    return {"reading_skills": READING_SKILLS,
            "rule": "Gist before detail, always. And a question set that is all "
                    "specific_detail is a test, not a lesson."}


def get_text_constraints(band: str) -> dict:
    """Return what a reading text at this band may be.

    Args:
      band: CEFR band, e.g. "A2".

    Returns:
      The genres a learner at this band actually reads, the word-count range, how
      many new words the text may carry, and how to classify the hard ones.
      Difficulty is not only vocabulary: a text of easy words can still be too
      hard because of its sentences.
    """
    key = (band or "").strip().upper()
    low, high = TEXT_LENGTH_BY_BAND.get(key, (20, 800))
    return {
        "band": key,
        "text_types": TEXT_TYPES_BY_BAND.get(key, []),
        "length_words": {"min": low, "max": high},
        "new_word_budget": NEW_WORD_BUDGET_BY_BAND.get(key, 10),
        "max_comprehension_questions": MAX_QUESTIONS_BY_BAND.get(key, 12),
        "vocabulary_support": VOCABULARY_SUPPORT,
        "rule": "The goal is not to remove every hard word. It is to leave the "
                "learner able to read past the ones that stay.",
    }


def get_support_levels() -> dict:
    """Return the scaffolding ladder a lesson must descend.

    Returns:
      The four support levels. Support must fall across the lesson: the final
      task has to be less supported than the practice that prepared it, or the
      learner read aloud rather than communicated.
    """
    return {"support_levels": SUPPORT_LEVELS,
            "rule": "high -> medium -> low -> independent. It never goes back up."}


def check_blueprint(blueprint: str) -> dict:
    """Validate a draft blueprint before any material is written against it.

    Args:
      blueprint: The draft blueprint, as JSON.

    Returns:
      Whether it is valid, and every problem found. Checks progression order,
      required stages, the skill ladder, cognitive-operation variety, objective
      coverage, image budget and overgeneration.

      Fix what this reports and call it again. A blueprint corrected here costs
      nothing; the same defect found after generation costs a whole lesson of
      exercises and images.
    """
    from ..schemas.blueprint import MaterialBlueprint

    draft = _load(blueprint)
    if not draft:
        return {"valid": False, "problems": [
            {"field": "", "problem": "blueprint is not readable JSON"}]}

    try:
        parsed = MaterialBlueprint(**draft)
    except ValidationError as exc:
        return {
            "valid": False,
            "problems": [
                {"field": ".".join(str(p) for p in e["loc"]), "problem": e["msg"]}
                for e in exc.errors()
            ],
        }

    # Valid, but still worth reporting the shape back so the planner can see
    # what it actually built rather than what it meant to build.
    notes: list[str] = []
    exercises = [s for s in parsed.slots if s.exercise]
    items = sum(s.exercise.number_of_items for s in exercises)
    if items > MAX_EXERCISE_ITEMS_PER_LESSON * 0.8:
        notes.append(f"{items} exercise items is close to the ceiling; prefer fewer, better.")
    if parsed.image_count > MAX_IMAGES_PER_LESSON * 0.8:
        notes.append(f"{parsed.image_count} images is a lot; each one must earn its place.")
    if parsed.total_minutes > 60:
        notes.append(f"the slots total {parsed.total_minutes} minutes; the hour is 60.")
    for slot in parsed.slots:
        if slot.exercise and not slot.exercise.vocabulary_constraints:
            notes.append(f"{slot.slot_id} names no vocabulary constraints; without them "
                         "the items will drift above the band.")

    return {
        "valid": True,
        "problems": [],
        "stages": parsed.stages,
        "slot_count": len(parsed.slots),
        "exercise_sets": len(exercises),
        "exercise_items": items,
        "cognitive_operations": parsed.operations(),
        "images": parsed.image_count,
        "total_minutes": parsed.total_minutes,
        "notes": notes,
    }


BLUEPRINT_TOOLS = [
    get_stage_catalogue,
    get_exercise_types,
    should_this_have_an_image,
    get_visual_types,
    get_retrieval_directions,
    get_vocabulary_budget,
    get_reading_skills,
    get_text_constraints,
    get_support_levels,
    check_blueprint,
]
