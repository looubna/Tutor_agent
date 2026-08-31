"""Structural validation of generated material.

The old checker asked a model whether material was good, and a model asked that
about material a model wrote says yes — it passed a German lesson written
entirely in English. Everything here is counted instead, and every test is a
defect that reads perfectly plausibly in finished courseware.
"""

from __future__ import annotations

from zanoba_agent.material.language_purity import check_package, check_text
from zanoba_agent.material.validation import (
    PASS_SCORE, build_regeneration_plan, check_communicative_task,
    check_distractors, check_reading_evidence, check_structure,
    check_vocabulary, validate_package)


def item(**kw):
    base = dict(id="m1", activity_id="a1", blueprint_slot_id="s1",
                kind="exercise_set", stage="controlled-practice",
                title="Ordne zu.", instruction="Ordne zu.",
                content="Ergänze die Artikel.", objective_ids=["o1"],
                pedagogical_purpose="controlled recognition of the article",
                exercises=[], images=[])
    base.update(kw)
    return base


def exercise(**kw):
    base = dict(id="e1", prompt="_______ Garten", answer="der",
                exercise_type="gap_fill", operation="complete",
                skill="controlled_production", stage="controlled-practice",
                objective_id="o1", pedagogical_purpose="connect gender to article")
    base.update(kw)
    return base


def package(items, **kw):
    base = dict(student_id="s1", subject="german", domain="language",
                target_language="german", target_item_id="x", items=items)
    base.update(kw)
    return base


# ---- the target language ---------------------------------------------------

def test_real_reference_german_is_not_flagged():
    # Every one of these is a line from a published Lingoda A1 deck. A checker
    # that flags real courseware is worse than no checker, because it teaches
    # everyone downstream to ignore it.
    for line in [
        "Ordne zu.",
        "Lies den Text. Ergänze die Artikel unten.",
        "Hör zu und sprich nach.",
        "Der bestimmte Artikel im Plural heißt immer die.",
        "Ich verstehe das nicht. Was bedeutet Ananas?",
        "Kannst du das bitte wiederholen?",
        "Die Lehrkraft sagt ein Wort. Sprich nach.",
        "Denke an ein Wort. Die anderen raten.",
        "Frage und antworte.",
        "Spiele den Dialog nach.",
    ]:
        assert check_text(line, "german")["is_target_language"], line


def test_english_scaffolding_around_german_content_is_caught():
    for line in ["Match the Articles!", "Let's warm up your German spelling skills.",
                 "Look at these nine classroom items.",
                 "Complete each phrase with the correct definite article."]:
        assert not check_text(line, "german")["is_target_language"], line


def test_an_english_word_under_discussion_is_allowed():
    # The reference deck contains exactly this line. The English word is the
    # object of study, which is the one place it belongs.
    assert check_text('Lisa: Der heißt "the" auf Englisch.', "german")["is_target_language"]


def test_english_in_a_german_lesson_is_critical():
    report = validate_package(package([item(title="Match the Articles!")]),
                              target_language="german")
    english = [i for i in report["critical_issues"] if "English" in i["problem"]]
    assert english, "a German lesson written in English must not pass"
    assert report["status"] == "FAIL"


def test_the_check_follows_the_target_language():
    # The reading reference is French. A French lesson is checked against French.
    french = package([item(title="Lisez le texte.", instruction="Répondez aux questions.",
                           content="Complétez les phrases avec les mots corrects.")],
                     target_language="french")
    assert check_package(french, "french")["clean"]


# ---- structure -------------------------------------------------------------

def test_an_answer_not_among_its_own_options_is_unanswerable():
    issues = check_structure(item(exercises=[exercise(
        exercise_type="multiple_choice", operation="choose", skill="recognition",
        options=["die", "das"], answer="der")]))
    assert any(i["severity"] == "critical" and "not among the options" in i["problem"]
               for i in issues)


def test_an_exercise_with_no_answer_cannot_be_marked():
    issues = check_structure(item(exercises=[exercise(answer="")]))
    assert any(i["severity"] == "critical" for i in issues)


def test_an_activity_with_no_instruction_line():
    issues = check_structure(item(instruction="", exercises=[exercise()]))
    assert any("does not know what to do" in i["problem"] for i in issues)


def test_an_open_item_with_only_one_accepted_answer():
    issues = check_structure(item(exercises=[exercise(
        exercise_type="open_production", operation="produce", skill="communication",
        acceptable_answers=[])]))
    assert any("marked wrong for a different correct response" in i["problem"]
               for i in issues)


def test_a_distractor_that_gives_itself_away_by_length():
    issues = check_distractors(package([item(exercises=[exercise(
        exercise_type="multiple_choice", options=["ja", "nein", "vielleicht morgen früh am Bahnhof"],
        answer="vielleicht morgen früh am Bahnhof")])]))
    assert any("without reading" in i["problem"] for i in issues)


def test_a_duplicated_option_is_caught():
    issues = check_distractors(package([item(exercises=[exercise(
        exercise_type="multiple_choice", options=["der", "die", "der"], answer="die")])]))
    assert any("appears twice" in i["problem"] for i in issues)


# ---- images ----------------------------------------------------------------

def test_an_image_that_was_promised_and_never_made():
    report = validate_package(package([item(images=[
        {"purpose": "p", "prompt": "a garden", "alt_text": "a garden",
         "provider": "pending", "url": "", "spec": {"target_concept": "Garten"}}])]))
    assert any("arrives at the lesson blank" in i["problem"]
               for i in report["critical_issues"])


def test_an_image_with_no_brief_cannot_be_checked():
    report = validate_package(package([item(images=[
        {"purpose": "p", "prompt": "a cute owl teacher", "alt_text": "owl",
         "provider": "generated", "url": "http://x/1.png"}])]))
    assert any("no visual specification" in i["problem"] for i in report["issues"])


# ---- reading evidence ------------------------------------------------------

TEXT = ("Montréal est une ville historique mais aussi moderne. "
        "Nous prenons un taxi à l'aéroport. Marc viendra seul, il a divorcé.")


def _reading(exercises):
    return package([
        item(id="m1", kind="text", stage="gist", title="Un petit texte",
             content=TEXT, exercises=[]),
        item(id="m2", stage="detail", title="Fragen", content="",
             exercises=exercises)],
        target_language="french")


def test_a_question_the_text_does_not_answer_is_critical():
    report = validate_package(_reading([exercise(
        id="q1", prompt="Comment s'appelle l'hôtel ?", answer="Hôtel Bonaventure",
        evidence_text="Ils dorment à l'Hôtel Bonaventure.",
        evidence_location="paragraph_1")]), focus="reading")
    assert any("does not appear in the text" in i["problem"]
               for i in report["critical_issues"])


def test_a_question_whose_evidence_is_really_there_passes():
    issues = check_reading_evidence(_reading([exercise(
        id="q1", prompt="Comment vont-ils de l'aéroport ?", answer="en taxi",
        evidence_text="Nous prenons un taxi à l'aéroport.",
        evidence_location="paragraph_2")]))
    assert not [i for i in issues if i["severity"] == "critical"]


def test_evidence_matching_survives_retyped_punctuation():
    # A model re-quoting its own text will straighten an apostrophe. Failing on
    # typography would make the check useless.
    issues = check_reading_evidence(_reading([exercise(
        id="q1", prompt="q", answer="a",
        evidence_text="Nous prenons un taxi a l aeroport",
        evidence_location="paragraph_2")]))
    assert not [i for i in issues if i["severity"] == "critical"]


def test_a_detail_question_with_no_evidence_at_all():
    issues = check_reading_evidence(_reading([exercise(id="q1", prompt="q", answer="a")]))
    assert any("no evidence quoted" in i["problem"] for i in issues)


def test_an_inference_question_whose_answer_is_stated_outright():
    pkg = package([
        item(id="m1", kind="text", stage="gist", content=TEXT, exercises=[]),
        item(id="m2", stage="inference", content="", exercises=[exercise(
            id="q1", prompt="Pourquoi Marc vient-il seul ?",
            answer="Marc viendra seul, il a divorcé",
            evidence_text="Marc viendra seul, il a divorcé.",
            evidence_location="paragraph_3")])], target_language="french")
    issues = check_reading_evidence(pkg)
    assert any("it is a detail question" in i["problem"] for i in issues)


# ---- communication ---------------------------------------------------------

TASK = {"task": "spell a name", "situation": "meeting a classmate",
        "learner_role": "student", "interlocutor_role": "classmate",
        "goal": "write the name down correctly",
        "required_language": ["Wie schreibt man das?", "Ich buchstabiere"],
        "success_criteria": ["asks for the spelling"],
        "information_gap": "each knows only their own name"}


def test_a_task_that_uses_none_of_the_language_taught():
    pkg = package([item(id="m1", stage="communicative-task",
                        content="Talk to your partner about the weather.",
                        instruction="Sprecht zusammen.")])
    issues = check_communicative_task(pkg, {"communicative_task": TASK})
    assert any("does not require the target language" in i["problem"] for i in issues)


def test_a_lesson_that_never_reaches_a_task():
    pkg = package([item(id="m1", stage="controlled-practice")])
    issues = check_communicative_task(pkg, {"communicative_task": TASK})
    assert any(i["severity"] == "critical" and "never used it" in i["problem"]
               for i in issues)


def test_a_task_with_no_observable_success_criteria():
    issues = check_communicative_task(
        package([item(id="m1", stage="communicative-task",
                      content="Wie schreibt man das? Ich buchstabiere: ...")]),
        {"communicative_task": {**TASK, "success_criteria": []}})
    assert any("whether communication succeeded" in i["problem"] for i in issues)


# ---- vocabulary ------------------------------------------------------------

SELECTION = {"entries": [
    {"lemma": "Hallo", "meaning": "hello", "example": "Hallo, ich bin Amir."},
    {"lemma": "Tschüss", "meaning": "bye", "example": "Tschüss, bis morgen!"},
    {"lemma": "Danke", "meaning": "thanks", "example": "Danke schön!"}]}


def test_a_word_selected_and_never_used_is_critical():
    pkg = package([item(id="m1", content="Hallo. Tschüss.")])
    issues = check_vocabulary(pkg, {"vocabulary": SELECTION})
    assert any(i["severity"] == "critical" and "never used" in i["problem"]
               for i in issues)


def test_recognition_only_practice_is_reported():
    pkg = package([item(id="m1", content="Hallo Tschüss Danke", exercises=[
        exercise(retrieval_direction="word_to_meaning")])])
    issues = check_vocabulary(pkg, {"vocabulary": SELECTION})
    assert any("only asks the learner to recognise the word" in i["problem"]
               for i in issues)


def test_an_example_that_just_repeats_the_word():
    selection = {"entries": [{"lemma": "Computer", "meaning": "computer",
                              "example": "Der Computer ist ein Computer."}]}
    pkg = package([item(id="m1", content="Computer Computer Computer",
                        exercises=[exercise(retrieval_direction="picture_to_word"),
                                   exercise(id="e2", retrieval_direction="situation_to_word")])])
    issues = check_vocabulary(pkg, {"vocabulary": selection})
    assert any("repeats the word rather than showing it in use" in i["problem"]
               for i in issues)


# ---- targeted regeneration -------------------------------------------------

def test_a_bad_image_costs_one_image_not_a_lesson():
    plan = build_regeneration_plan([
        {"item_id": "m3#img0", "scope": "image", "severity": "critical",
         "category": "technical", "problem": "ambiguous", "fix": "exclude the house"}])
    assert len(plan) == 1
    assert plan[0]["scope"] == "image"
    assert plan[0]["target"] == "m3#img0"
    assert plan[0]["instructions"] == ["exclude the house"]


def test_three_broken_exercises_in_one_item_regenerate_it_once():
    plan = build_regeneration_plan([
        {"item_id": f"m2/e{n}", "scope": "exercise", "severity": "critical",
         "category": "technical", "problem": "no answer", "fix": "supply the answer"}
        for n in range(3)])
    assert len(plan) == 1
    assert plan[0]["target"] == "m2"


def test_repairs_are_ordered_narrowest_first():
    plan = build_regeneration_plan([
        {"item_id": "", "scope": "lesson", "severity": "critical",
         "category": "pedagogical", "problem": "objective untaught", "fix": "add it"},
        {"item_id": "m1#img0", "scope": "image", "severity": "critical",
         "category": "technical", "problem": "not made", "fix": "make it"}])
    assert [r["scope"] for r in plan] == ["image", "lesson"]
    assert "only regenerate everything if" in plan[-1]["note"]


def test_low_severity_notes_do_not_trigger_regeneration():
    assert build_regeneration_plan([
        {"item_id": "m1", "scope": "item", "severity": "low",
         "category": "pedagogical", "problem": "no explanation", "fix": ""}]) == []


# ---- the verdict -----------------------------------------------------------

def test_correct_but_pedagogically_useless_material_still_fails():
    # Grammatically flawless German, and a lesson that teaches nothing: no
    # objectives, no purpose, no instruction, an image that does not exist.
    report = validate_package(package([item(
        objective_ids=[], pedagogical_purpose="", instruction="",
        exercises=[exercise(pedagogical_purpose="")],
        images=[{"purpose": "", "prompt": "ein Garten", "alt_text": "",
                 "provider": "pending", "url": ""}])]))
    assert report["status"] == "FAIL"
    assert report["overall_score"] < PASS_SCORE


def test_the_report_scores_each_dimension_for_its_focus():
    report = validate_package(package([item()]), focus="reading")
    for dimension in ("text_quality", "question_quality", "evidence_alignment"):
        assert dimension in report
    report = validate_package(package([item()]), focus="communication")
    for dimension in ("communication_alignment", "authenticity", "interaction_quality"):
        assert dimension in report


def test_five_english_prompts_in_one_item_are_one_repair():
    # Scope has to match the id's granularity. With item scope on an
    # exercise-level id the planner cannot collapse them, and asks for five
    # separate repairs of the same item.
    pkg = package([item(exercises=[
        exercise(id=f"e{n}", prompt=word)
        for n, word in enumerate(["table", "chair", "bag", "lamp", "book"], 1)])])
    report = validate_package(pkg, target_language="german")
    plan = report["regeneration_targets"]
    assert len([r for r in plan if r["target"] == "m1"]) == 1
    assert plan[0]["scope"] == "exercise"
    assert len(plan[0]["reasons"]) == 5


def test_english_content_words_are_caught_not_just_english_prose():
    # The gap the first rebuilt lesson fell through: a German matching exercise
    # whose prompts were "table", "chair", "bag". No function words, so a
    # function-word check scored it 100.
    assert not check_text("table", "german")["is_target_language"]
    assert not check_text("chair", "german")["is_target_language"]
    # And the German for them is still clean.
    for word in ["der Tisch", "der Stuhl", "die Tasche", "die Lampe", "das Buch"]:
        assert check_text(word, "german")["is_target_language"], word


def test_an_item_that_carries_a_slide_is_complete_without_prose():
    """`MaterialItem` says to prefer `slide` to `content` always.

    The checker used to demand `content` anyway, so every item the material
    agent built as a rule table or a question list — which is every well-formed
    STEM item — was failed as empty. Both French maths lessons came out of the
    pipeline marked FAIL with material that was in fact fine.
    """
    from zanoba_agent.material.validation import check_structure

    withslide = {
        "id": "m1", "title": "Tableau de numération",
        "pedagogical_purpose": "présenter la structure des grands nombres",
        "objective_ids": ["o1"],
        "slide": {"kind": "rule_table", "headers": ["Classe", "Chiffres"],
                  "rows": [[{"text": "milliers"}, {"text": "3"}]]},
    }
    critical = [i for i in check_structure(withslide) if i["severity"] == "critical"]
    assert critical == []

    # An item with none of the three is still empty, and still refused.
    empty = {**withslide, "slide": None}
    problems = [i["problem"] for i in check_structure(empty) if i["severity"] == "critical"]
    assert any("no slide" in p for p in problems)
