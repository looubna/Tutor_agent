"""The material blueprint, and the defects it refuses.

Every test here names a way generated courseware goes wrong and shows the
blueprint rejecting it before a single exercise or image is paid for. That is
the whole argument for the blueprint stage: these are all defects that read
perfectly plausibly in finished material and are cheap to catch in a plan.
"""

from __future__ import annotations

import pytest
from pydantic import ValidationError

from conftest import COMMUNICATION_SLOTS, GRAMMAR_SLOTS, READING_SLOTS, ex, slot
from zanoba_agent.material.rubric import (
    EXERCISE_TYPES, ONE_IMAGE_PER_ITEM_TYPES, ONE_OF_REQUIRED_BY_FOCUS,
    REQUIRED_STAGES_BY_FOCUS, STAGES_BY_FOCUS)
from zanoba_agent.schemas.blueprint import (
    BlueprintSlot, ExerciseSpec, MaterialBlueprint, VisualSpec)


def rebuilt(blueprint: MaterialBlueprint, slots) -> MaterialBlueprint:
    """The same blueprint with a different slot list, so one defect is isolated."""
    data = blueprint.model_dump()
    data["slots"] = [s.model_dump() if hasattr(s, "model_dump") else s for s in slots]
    return MaterialBlueprint(**data)


# ---- the reference shapes stay valid ---------------------------------------

def test_all_four_reference_shapes_are_valid(
        grammar_blueprint, communication_blueprint,
        vocabulary_blueprint, reading_blueprint):
    # Each fixture is modelled on a published Lingoda lesson. A rule that makes
    # a real professional lesson invalid is a wrong rule, and this is where that
    # shows up rather than in production.
    for blueprint in (grammar_blueprint, communication_blueprint,
                      vocabulary_blueprint, reading_blueprint):
        assert blueprint.slots
        assert blueprint.total_minutes <= 60


def test_every_focus_has_its_own_stage_set():
    assert set(STAGES_BY_FOCUS) == {"grammar", "communication", "vocabulary",
                                    "reading", "speaking"}
    # A speaking lesson plans as a communication one, deliberately: the same
    # stages, named apart because the syllabus distinguishes them.
    assert STAGES_BY_FOCUS["speaking"] is STAGES_BY_FOCUS["communication"]
    # The four are genuinely different progressions, not one list relabelled.
    assert STAGES_BY_FOCUS["grammar"] != STAGES_BY_FOCUS["communication"]
    assert "communicative-task" in STAGES_BY_FOCUS["communication"]
    assert "retrieval" in STAGES_BY_FOCUS["vocabulary"]
    assert "gist" in STAGES_BY_FOCUS["reading"]


# ---- shared defects --------------------------------------------------------

def test_practice_before_presentation_is_rejected(grammar_blueprint):
    out_of_order = [GRAMMAR_SLOTS[4], GRAMMAR_SLOTS[3]] + GRAMMAR_SLOTS[5:]
    with pytest.raises(ValidationError, match="out of pedagogical order"):
        rebuilt(grammar_blueprint, out_of_order)


def test_a_stage_from_another_focus_is_rejected(grammar_blueprint):
    # "communicative-task" is a communication stage. A grammar lesson using it
    # means the planner mixed up its catalogues, and the ordering rules that
    # follow would then be meaningless.
    stray = slot("sx", "communicative-task",
                 exercise=ex("role_play", "respond", "communication", 1))
    with pytest.raises(ValidationError, match="not part of a grammar lesson"):
        rebuilt(grammar_blueprint, GRAMMAR_SLOTS[:4] + [stray])


def test_a_slot_serving_no_objective_cannot_be_built():
    with pytest.raises(ValidationError):
        BlueprintSlot(slot_id="s", stage="review", objective_ids=[],
                      pedagogical_goal="x" * 25, difficulty="A1",
                      presentation="summary", presentation_brief="b",
                      estimated_minutes=4, visual_decision="none needed")


def test_a_goal_that_is_not_a_goal_is_rejected():
    # "Fill in the blanks" describes the format, not what the learner gains.
    with pytest.raises(ValidationError):
        slot("s", "review", presentation="summary", presentation_brief="b",
             pedagogical_goal="Fill in the blanks.")


def test_no_image_must_still_be_a_decision():
    with pytest.raises(ValidationError, match="does not say why"):
        BlueprintSlot(slot_id="s", stage="review", objective_ids=["o1"],
                      pedagogical_goal="x" * 25, difficulty="A1",
                      presentation="summary", presentation_brief="b",
                      estimated_minutes=4, visual_decision="")


def test_a_slot_is_either_practice_or_presentation():
    with pytest.raises(ValidationError, match="not both and not neither"):
        slot("s", "review")


def test_exercise_type_and_operation_must_describe_the_same_task():
    with pytest.raises(ValidationError, match="exercises 'complete', not 'match'"):
        ex("gap_fill", "match", "recognition", 5)


def test_six_exercises_that_all_ask_the_same_thing(grammar_blueprint):
    same = [
        slot("s1", "noticing", exercise=ex("gap_fill", "complete", "controlled_production", 6)),
        slot("s2", "explanation", presentation="rule_table", presentation_brief="b"),
        slot("s3", "controlled-practice", exercise=ex("gap_fill", "complete", "controlled_production", 6)),
        slot("s4", "guided-practice", exercise=ex("gap_fill", "complete", "controlled_production", 6)),
        slot("s5", "review", presentation="summary", presentation_brief="b"),
    ]
    with pytest.raises(ValidationError, match="cognitive operations"):
        rebuilt(grammar_blueprint, same)


def test_a_picture_of_a_grammatical_abstraction_is_refused(grammar_blueprint):
    bad = slot("s1", "warm-up", exercise=ex("matching", "match", "recognition", 6),
               visual=VisualSpec(target_concept="the definite article",
                                 language_level="A1", pedagogical_purpose="p",
                                 main_subject="m", composition="c"))
    with pytest.raises(ValidationError, match="grammatical abstraction"):
        rebuilt(grammar_blueprint, [bad] + GRAMMAR_SLOTS[1:])


def test_intentional_ambiguity_is_only_for_a_communicative_scene():
    with pytest.raises(ValidationError, match="Only a communicative scene"):
        VisualSpec(target_concept="Buch", visual_type="direct_concept",
                   language_level="A1", pedagogical_purpose="p",
                   main_subject="a book", composition="c",
                   ambiguity_tolerance="intentional")


def test_an_ambiguous_picture_must_say_what_it_makes_the_learner_say():
    with pytest.raises(ValidationError, match="student_should_communicate is empty"):
        VisualSpec(target_concept="a classroom", visual_type="communicative_scene",
                   language_level="A1", pedagogical_purpose="p",
                   main_subject="four students", composition="c",
                   ambiguity_tolerance="intentional",
                   communication_goal="identify the right student")


# ---- grammar ---------------------------------------------------------------

def test_a_grammar_lesson_needs_discovery_before_the_rule(grammar_blueprint):
    with pytest.raises(ValidationError, match="noticing"):
        rebuilt(grammar_blueprint, [s for s in GRAMMAR_SLOTS if s.stage != "noticing"])


def test_a_grammar_lesson_where_the_learner_never_produces(grammar_blueprint):
    recognition_only = [s for s in GRAMMAR_SLOTS
                        if s.stage not in ONE_OF_REQUIRED_BY_FOCUS["grammar"]]
    with pytest.raises(ValidationError, match="at least one of"):
        rebuilt(grammar_blueprint, recognition_only)


def test_explanation_straight_to_free_production_is_a_cliff(grammar_blueprint):
    cliff = [
        GRAMMAR_SLOTS[2], GRAMMAR_SLOTS[3],
        slot("sx", "controlled-practice",
             exercise=ex("matching", "match", "recognition", 4)),
        slot("sy", "communicative-practice", support="low",
             exercise=ex("open_production", "produce", "communication", 3)),
        GRAMMAR_SLOTS[8],
    ]
    with pytest.raises(ValidationError, match="rungs past anything"):
        rebuilt(grammar_blueprint, cliff)


# ---- communication ---------------------------------------------------------

def test_a_communication_lesson_without_a_task_is_a_grammar_lesson(
        communication_blueprint):
    data = communication_blueprint.model_dump()
    data["communicative_task"] = None
    with pytest.raises(ValidationError, match="grammar lesson with conversation added"):
        MaterialBlueprint(**data)


def test_a_communication_lesson_must_teach_phrases_by_function(
        communication_blueprint):
    data = communication_blueprint.model_dump()
    data["functional_language"] = []
    with pytest.raises(ValidationError, match="what any of them is FOR"):
        MaterialBlueprint(**data)


def test_a_communication_lesson_must_reach_a_real_task(communication_blueprint):
    without = [s for s in COMMUNICATION_SLOTS if s.stage != "communicative-task"]
    with pytest.raises(ValidationError, match="communicative-task"):
        rebuilt(communication_blueprint, without)


def test_scaffolding_may_not_come_back(communication_blueprint):
    # A "role-play" as supported as the drill before it is two people reading
    # sentences at each other.
    slots = [s.model_copy() for s in COMMUNICATION_SLOTS]
    slots[6].support_level = "high"
    with pytest.raises(ValidationError, match="support goes back UP"):
        rebuilt(communication_blueprint, slots)


def test_a_lesson_that_never_lets_go_of_the_learner(communication_blueprint):
    slots = [s.model_copy(update={"support_level": "high"})
             for s in COMMUNICATION_SLOTS]
    with pytest.raises(ValidationError, match="never gets below"):
        rebuilt(communication_blueprint, slots)


# ---- vocabulary ------------------------------------------------------------

def test_too_many_new_words_for_the_band_is_refused(vocabulary_blueprint):
    # The A1 ceiling is ten new items an hour. Sixteen is a learner who
    # half-knows sixteen words, which is worse than eight they can use.
    data = vocabulary_blueprint.model_dump()
    entries = data["vocabulary"]["entries"]
    extra = [dict(entries[0], lemma=f"Wort{n}") for n in range(8)]
    data["vocabulary"]["entries"] = entries + extra
    data["vocabulary"]["target_count"] = len(entries) + len(extra)
    with pytest.raises(ValidationError, match="half-learns"):
        MaterialBlueprint(**data)


def test_recognition_only_is_not_a_vocabulary_lesson(vocabulary_blueprint):
    data = vocabulary_blueprint.model_dump()
    for slot_data in data["slots"]:
        if slot_data.get("exercise"):
            slot_data["exercise"]["retrieval_direction"] = "word_to_meaning"
    with pytest.raises(ValidationError, match="tested recognition and called it practice"):
        MaterialBlueprint(**data)


def test_a_word_introduced_once_and_never_seen_again(vocabulary_blueprint):
    data = vocabulary_blueprint.model_dump()
    for slot_data in data["slots"]:
        slot_data["recycles"] = []
    with pytest.raises(ValidationError, match="reappear"):
        MaterialBlueprint(**data)


def test_the_vocabulary_count_must_be_honest(vocabulary_blueprint):
    data = vocabulary_blueprint.model_dump()
    data["vocabulary"]["target_count"] = 3
    with pytest.raises(ValidationError, match="target_count says"):
        MaterialBlueprint(**data)


# ---- reading ---------------------------------------------------------------

def test_a_reading_lesson_needs_its_text_specified_first(reading_blueprint):
    data = reading_blueprint.model_dump()
    data["text"] = None
    with pytest.raises(ValidationError, match="no text specification"):
        MaterialBlueprint(**data)


def test_a_reading_lesson_must_name_the_skill_it_builds(reading_blueprint):
    data = reading_blueprint.model_dump()
    data["reading_skill"] = ""
    with pytest.raises(ValidationError, match="two targets"):
        MaterialBlueprint(**data)


def test_a_declared_skill_nothing_practises_is_a_label(reading_blueprint):
    data = reading_blueprint.model_dump()
    data["reading_skill"] = "writer_purpose"
    with pytest.raises(ValidationError, match="no activity practises it"):
        MaterialBlueprint(**data)


def test_detail_before_gist_is_rejected(reading_blueprint):
    swapped = [READING_SLOTS[0], READING_SLOTS[1], READING_SLOTS[3],
               READING_SLOTS[2]] + READING_SLOTS[4:]
    with pytest.raises(ValidationError, match="out of pedagogical order"):
        rebuilt(reading_blueprint, swapped)


def test_a_text_too_long_for_the_band(reading_blueprint):
    data = reading_blueprint.model_dump()
    data["text"]["length_words"] = 600
    with pytest.raises(ValidationError, match="outside 80-180"):
        MaterialBlueprint(**data)


def test_a_genre_an_a2_learner_does_not_read(reading_blueprint):
    data = reading_blueprint.model_dump()
    data["text"]["text_type"] = "editorial"
    with pytest.raises(ValidationError, match="not one a A2 learner reads"):
        MaterialBlueprint(**data)


def test_too_many_words_needing_taught(reading_blueprint):
    data = reading_blueprint.model_dump()
    essential = dict(data["text"]["glossary"][0])
    data["text"]["glossary"] = [dict(essential, word=f"mot{n}") for n in range(12)]
    with pytest.raises(ValidationError, match="over the budget"):
        MaterialBlueprint(**data)


def test_fifteen_questions_because_the_text_has_fifteen_facts(reading_blueprint):
    data = reading_blueprint.model_dump()
    # Each set stays inside its own type's range; the defect is the TOTAL.
    ceilings = {"gist": 8, "detail": 6, "inference": 8}
    for slot_data in data["slots"]:
        if slot_data["stage"] in ceilings:
            slot_data["exercise"]["number_of_items"] = ceilings[slot_data["stage"]]
    with pytest.raises(ValidationError, match="comprehension questions at A2 exceeds"):
        MaterialBlueprint(**data)


def test_comprehension_questions_must_be_required_to_cite_the_text(reading_blueprint):
    data = reading_blueprint.model_dump()
    for slot_data in data["slots"]:
        if slot_data["stage"] == "detail":
            slot_data["exercise"]["requires_evidence"] = False
    with pytest.raises(ValidationError, match="without requires_evidence"):
        MaterialBlueprint(**data)


def test_an_inferable_word_needs_a_clue_or_it_is_guessing():
    from zanoba_agent.schemas.blueprint import GlossedWord

    with pytest.raises(ValidationError, match="guessing, not inference"):
        GlossedWord(word="célibataire", meaning="single", support="inferable")


# ---- every page carries a picture ------------------------------------------

def test_a_content_slot_with_no_picture_is_rejected(grammar_blueprint):
    # A wall of text is not the product. The reference decks illustrate every
    # content slide; the old "only where it earns its place" rule was right
    # about decoration and wrong about how visual a published lesson is.
    bare = [s.model_copy(update={"visual": None}) if s.stage == "controlled-practice"
            else s for s in GRAMMAR_SLOTS]
    with pytest.raises(ValidationError, match="have no picture"):
        rebuilt(grammar_blueprint, bare)


def test_a_dialogue_without_its_scene_is_rejected(communication_blueprint):
    slots = [s.model_copy(update={"visual": None}) if s.presentation == "dialogue"
             else s for s in COMMUNICATION_SLOTS]
    with pytest.raises(ValidationError, match="no picture"):
        rebuilt(communication_blueprint, slots)


def test_the_summary_and_the_self_assessment_may_go_without(grammar_blueprint):
    # The reference decks leave exactly these bare — Zusammenfassung, Wortschatz
    # and "Über die Lernziele nachdenken" carry no photograph.
    from zanoba_agent.material.rubric import NO_IMAGE_STAGES

    assert "review" in NO_IMAGE_STAGES
    assert grammar_blueprint.slots[-1].stage == "review"
    assert grammar_blueprint.slots[-1].visual is None


def test_a_new_vocabulary_item_without_a_picture_is_rejected(vocabulary_blueprint):
    # A word met with a picture is learnt; a word met in a glossary is learnt
    # as a translation.
    data = vocabulary_blueprint.model_dump()
    data["vocabulary"]["entries"][0]["image"] = None
    with pytest.raises(ValidationError, match="no picture"):
        MaterialBlueprint(**data)


def test_an_abstraction_gets_a_concrete_instance_not_a_blank_slide():
    # The correction to the old rule: "the definite article" cannot be
    # photographed, but der Mann / die Frau / das Kind can, and that is how the
    # reference deck illustrates exactly this rule.
    from zanoba_agent.material.rubric import image_earns_its_place

    verdict = image_earns_its_place("explanation", "gap_fill",
                                    "the definite article", "grammar")
    assert verdict["use_image"] is True
    assert verdict["requires_concrete_instance"] is True
    # But the blueprint still refuses to let the abstraction BE the concept.
    assert "concrete example" in verdict["reason"]


def test_a_picture_matching_task_needs_a_picture_per_item(grammar_blueprint):
    # The defect the first illustrated deck had: a five-word matching exercise
    # got ONE composite image, and the model returned a six-panel grid with two
    # identical chairs and printed English on a book. A grid cannot be numbered.
    from conftest import picture

    composite = slot("s1", "warm-up",
                     exercise=ExerciseSpec(exercise_type="picture_word_match",
                                           operation="match", skill="recognition",
                                           number_of_items=5),
                     visual=picture("classroom objects"))
    with pytest.raises(ValidationError, match="each item needs its own"):
        rebuilt(grammar_blueprint, [composite] + GRAMMAR_SLOTS[1:])


def test_two_items_may_not_show_the_same_thing():
    from conftest import picture

    with pytest.raises(ValidationError, match="same thing"):
        ExerciseSpec(exercise_type="picture_word_match", operation="match",
                     skill="recognition", number_of_items=4,
                     item_visuals=[picture("Stuhl"), picture("Stuhl"),
                                   picture("Tisch"), picture("Buch")])


def test_the_picture_count_must_equal_the_item_count():
    from conftest import picture

    with pytest.raises(ValidationError, match="exactly one each"):
        ExerciseSpec(exercise_type="picture_naming", operation="produce",
                     skill="controlled_production", number_of_items=6,
                     item_visuals=[picture("Tisch"), picture("Stuhl")])


def test_items_carrying_their_own_pictures_satisfy_the_slide_rule(grammar_blueprint):
    # A picture-matching slot is illustrated by its items, not by a slot image.
    picture_slot = [s for s in grammar_blueprint.slots
                    if s.exercise and s.exercise.item_visuals]
    assert picture_slot, "the grammar fixture should have one"
    assert picture_slot[0].visual is None
    assert len(picture_slot[0].exercise.item_visuals) == \
        picture_slot[0].exercise.number_of_items


# ---- one picture, one thing ------------------------------------------------

def test_a_direct_concept_picture_may_not_name_a_set():
    # "book should have image of book only, chair image of chair" — a composite
    # is easier to ask for and fails invisibly: the six-panel grid this rule
    # exists for came back with two identical chairs and English text on a book.
    for concept in ("classroom objects", "various items", "a set of words",
                    "labeled classroom objects", "different things"):
        with pytest.raises(ValidationError, match="must show ONE thing"):
            VisualSpec(target_concept=concept, visual_type="direct_concept",
                       language_level="A1", pedagogical_purpose="p",
                       main_subject="m", composition="c")


def test_one_object_per_picture_is_stated_in_the_prompt():
    spec = VisualSpec(target_concept="Buch", visual_type="direct_concept",
                      language_level="A1", pedagogical_purpose="vocabulary",
                      main_subject="one closed hardback book",
                      composition="centred on a plain surface")
    prompt = spec.to_prompt()
    assert "A single Buch, one only" in prompt
    assert "Not a set, not a collage, not a grid" in prompt


# ---- rich, not empty -------------------------------------------------------

def test_a_thin_lesson_is_rejected(grammar_blueprint):
    # "Prefer six excellent exercises to twenty repetitive ones" was read as
    # licence to produce five sparse slides. Both a floor and a ceiling, or the
    # rule only ever pushes one way.
    # Every required stage is present and the item count is fine — the only
    # thing wrong is that five slots is not sixty minutes of teaching.
    # Every required stage present, the progression intact, four distinct
    # operations, enough items — the only thing wrong is six slots for an hour.
    bare_minimum = [GRAMMAR_SLOTS[2], GRAMMAR_SLOTS[3], GRAMMAR_SLOTS[4],
                    GRAMMAR_SLOTS[5], GRAMMAR_SLOTS[6], GRAMMAR_SLOTS[8]]
    with pytest.raises(ValidationError, match="not an hour of teaching"):
        rebuilt(grammar_blueprint, bare_minimum)


def test_a_lesson_that_hands_back_paid_minutes_is_rejected(grammar_blueprint):
    thin = [s.model_copy(update={"estimated_minutes": 3}) for s in GRAMMAR_SLOTS]
    with pytest.raises(ValidationError, match="minutes of a 60-minute lesson"):
        rebuilt(grammar_blueprint, thin)


def test_too_few_exercise_items_across_the_hour(grammar_blueprint):
    from conftest import picture

    sparse = []
    for s in GRAMMAR_SLOTS:
        if s.exercise and s.exercise.exercise_type not in ONE_IMAGE_PER_ITEM_TYPES:
            low = EXERCISE_TYPES[s.exercise.exercise_type]["items"][0]
            sparse.append(s.model_copy(update={
                "exercise": s.exercise.model_copy(update={"number_of_items": low})}))
        else:
            sparse.append(s)
    total = sum(x.exercise.number_of_items for x in sparse if x.exercise)
    if total < 18:
        with pytest.raises(ValidationError, match="too thin"):
            rebuilt(grammar_blueprint, sparse)


# ---- the language is not the model's choice --------------------------------

def test_the_target_language_comes_from_the_curriculum():
    from zanoba_agent.agents.material_tools import get_target_language

    assert get_target_language("german")["target_language"] == "german"
    assert get_target_language("french")["target_language"] == "french"
    assert get_target_language("korean")["target_language"] == "korean"
    # And an unknown subject says so rather than guessing.
    assert "error" in get_target_language("klingon")


def test_both_material_agents_can_look_the_language_up():
    from zanoba_agent.agents.language_material import language_material_agent
    from zanoba_agent.agents.material_planner import material_planner_agent

    for agent in (material_planner_agent, language_material_agent):
        names = {t.__name__ for t in agent.tools}
        assert "get_target_language" in names
        assert "research_language" in names, "it must be able to look up real usage"
