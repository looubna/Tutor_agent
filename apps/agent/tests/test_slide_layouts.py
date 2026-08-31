"""Typed slide components, and the STEM LaTeX deck.

The change these test: the material agent used to emit a paragraph and the
renderer had to guess a layout. It could guess five, so a lesson came out as
three consecutive slides titled "Die drei Artikel" carrying 14, 10 and 8 words,
and the CSS for vocabulary cards and sorting grids was never reached.
"""

from __future__ import annotations

import typing

import pytest
from pydantic import ValidationError

from zanoba_agent.material import beamer, deck
from zanoba_agent.material.layouts import RENDERERS
from zanoba_agent.schemas.material import MaterialItem
from zanoba_agent.schemas.slides import (
    LAYOUTS_FOR_STAGE, Cell, ChoiceCards, Dialogue, Picture, PictureSet,
    RuleTable, SlideComponent, SortingGrid, Summary, Turn, layout_suits_stage)


def _kinds() -> set[str]:
    return {model.model_fields["kind"].default
            for model in typing.get_args(typing.get_args(SlideComponent)[0])}


# ---- the layouts exist and are all drawable --------------------------------

def test_every_component_has_a_renderer():
    # A component with no renderer draws nothing and reports no error, which is
    # the silent-blank-slide failure this mapping exists to prevent.
    assert _kinds() == set(RENDERERS)


def test_the_layouts_cover_the_reference_slide_shapes():
    for shape in ("picture_set", "dialogue", "rule_table", "vocab_card",
                  "sorting_grid", "tile_grid", "bubble_exchange",
                  "choice_cards", "question_list", "role_play", "summary",
                  "word_list"):
        assert shape in RENDERERS


def test_every_stage_has_layouts_it_can_use():
    from zanoba_agent.material.rubric import STAGES_BY_FOCUS

    for stages in STAGES_BY_FOCUS.values():
        for stage in stages:
            assert LAYOUTS_FOR_STAGE.get(stage), f"{stage} has no layouts"
            assert set(LAYOUTS_FOR_STAGE[stage]) <= set(RENDERERS)


# ---- one item is one slide -------------------------------------------------

def _item(stage, component, ident="m1"):
    return MaterialItem(id=ident, activity_id="a1", kind="exercise_set",
                        stage=stage, title=component.title or "t",
                        slide=component)


def test_one_item_becomes_one_slide():
    # It used to become two or three: an intro slide made from a seven-word
    # sentence, then the exercises.
    items = [
        _item("warm-up", PictureSet(
            title="Wie heißt das?", instruction="Ordne zu.",
            pictures=[Picture(url=f"u{n}", answer=w) for n, w in
                      enumerate(["der Ball", "das Haus", "die Katze"], 1)]), "m1"),
        _item("context", Dialogue(title="Im Unterricht", turns=[
            Turn(speaker="Sarah", line="Eine Frage?"),
            Turn(speaker="Lisa", line="Ja, bitte.")]), "m2"),
        _item("explanation", RuleTable(
            title="Der bestimmte Artikel", headers=["m.", "f.", "n."],
            rows=[[Cell(text="der"), Cell(text="die"), Cell(text="das")]]), "m3"),
    ]
    package = {"items": [i.model_dump() for i in items],
               "target_item_title": "der, die, das", "subject": "german"}
    slides = deck.build_slides(package, {"activities": []}, {"objectives": []})
    components = [s for s in slides if s["kind"] == "component"]
    assert len(components) == 3, "three items must make exactly three slides"
    assert [s["layout"] for s in components] == [
        "picture_set", "dialogue", "rule_table"]


def test_no_two_slides_repeat_the_same_title():
    # The symptom that made the deck look unfinished.
    items = [_item("warm-up", PictureSet(
        title="Wie heißt das?", instruction="Ordne zu.",
        pictures=[Picture(url="u1", answer="a"), Picture(url="u2", answer="b")]))]
    slides = deck.build_slides({"items": [i.model_dump() for i in items]},
                               {"activities": []}, {"objectives": []})
    titles = [s.get("title") for s in slides if s["kind"] == "component"]
    assert len(titles) == len(set(titles))


def test_a_layout_that_does_not_suit_its_stage_is_rejected():
    with pytest.raises(ValidationError, match="at the 'warm-up' stage"):
        _item("warm-up", RuleTable(title="Regel", headers=["a", "b"],
                                   rows=[[Cell(text="1"), Cell(text="2")]]))


def test_a_choice_with_an_unanswerable_option_set_is_rejected():
    with pytest.raises(ValidationError, match="not among the options"):
        ChoiceCards(title="Was ist richtig?", instruction="Wähle.",
                    options=[Cell(text="der"), Cell(text="die")], answer="das")


def test_the_layouts_actually_draw_content():
    grid = SortingGrid(title="Ordne zu", instruction="Ordne die Wörter zu.",
                       tiles=["Brot", "Bruder", "Banane", "Frau"],
                       categories=["der", "die", "das"])
    slides = deck.build_slides(
        {"items": [_item("noticing", grid).model_dump()]},
        {"activities": []}, {"objectives": []})
    html = deck.render_html(slides)
    assert 'class="tile"' in html and 'class="cathead"' in html
    for tile in ("Brot", "Bruder", "Banane", "Frau"):
        assert tile in html


def test_a_blank_renders_as_a_rule_not_as_nothing():
    # A blank must look like a blank on paper, or the learner sees a gap they
    # cannot tell from a layout error.
    table = RuleTable(title="Singular und Plural", headers=["Singular", "Plural"],
                      rows=[[Cell(text="", answer="der Mann"), Cell(text="die Männer")]])
    slides = deck.build_slides(
        {"items": [_item("explanation", table).model_dump()]},
        {"activities": []}, {"objectives": []})
    html = deck.render_html(slides)
    assert 'class="rule"' in html
    assert "der Mann" not in html, "the answer must not print on the learner's copy"


def test_prose_still_renders_when_no_layout_fits():
    # The fallback stays, because one unusual item should not break a lesson.
    item = MaterialItem(id="m9", activity_id="a1", kind="explanation",
                        stage="explanation", title="Hinweis",
                        content="Nomen haben ein Geschlecht.")
    slides = deck.build_slides({"items": [item.model_dump()]},
                               {"activities": []}, {"objectives": []})
    assert any(s["kind"] != "component" and s.get("body") for s in slides)


# ---- STEM goes to LaTeX ----------------------------------------------------

def test_maths_survives_escaping_and_prose_does_not():
    # A stray % comments out the rest of the line and the slide silently loses
    # half its content; a \frac must come through untouched.
    assert beamer.escape("50% of x_1 & y") == r"50\% of x\_1 \& y"
    assert r"\frac{3}{4}" in beamer.escape(r"Also $\frac{3}{4}$ und 100%")
    assert r"100\%" in beamer.escape(r"Also $\frac{3}{4}$ und 100%")


def test_the_stem_deck_uses_the_app_palette():
    # The upstream template ships a demo blue; a maths deck and a German deck
    # should be recognisably the same product.
    from zanoba_agent.material.brand import colour

    tex = beamer.render(
        {"subject": "mathematics", "target_item_title": "Fractions",
         "items": [{"id": "m1", "kind": "explanation", "title": "Regel",
                    "content": "Ein Bruch $\\frac{a}{b}$."}]},
        {"level_id": "6e"}, {"objectives": []})
    assert beamer._rgb("primary") in tex
    assert "31, 73, 125" not in tex, "the upstream demo blue must be replaced"
    assert colour("primary") == "#743ee4"


def test_one_stem_item_is_one_frame():
    tex = beamer.render(
        {"subject": "mathematics", "items": [
            {"id": "m1", "kind": "explanation", "title": "A", "content": "x"},
            {"id": "m2", "kind": "exercise_set", "title": "B",
             "exercises": [{"id": "e1", "prompt": "Calcule",
                            "expression": "\\frac{1}{2}", "answer": "0.5"}]}]},
        {}, {"objectives": [{"statement": "Je peux."}]})
    # title frame + objectives frame + one per item
    assert tex.count(r"\begin{frame}") == 4
    assert r"\displaystyle \frac{1}{2}" in tex


def test_an_answer_key_does_not_print_as_a_question():
    tex = beamer.render(
        {"items": [{"id": "m1", "kind": "exercise_set", "title": "Übung",
                    "exercises": [{"id": "e1", "prompt": "Calcule",
                                   "expression": "1+1", "answer": "2"}],
                    "answer_key": "e1 = 2"}]}, {}, {"objectives": []})
    assert r"\source{e1 = 2}" in tex, "the key belongs in the footnote, not the body"


# ---- component pictures must actually be generated -------------------------

def test_the_image_pipeline_walks_component_pictures():
    # The gap that produced a lesson billed for five images and rendering none:
    # the images were made against item["images"], the components carried their
    # own Picture fields, and nothing connected the two.
    from zanoba_agent.material import images

    made = []

    def fake_generate(**kw):
        made.append((kw.get("spec") or {}).get("target_concept"))
        return {"prompt": "p", "alt_text": "a", "purpose": "p",
                "provider": "generated", "url": "https://x/new.png"}

    def spec(concept):
        return {"target_concept": concept, "visual_type": "direct_concept",
                "language_level": "A1", "pedagogical_purpose": "vocabulary",
                "main_subject": concept, "composition": "centred"}

    package = {"items": [{
        "id": "m1",
        "images": [{"prompt": "", "spec": spec("Klassenzimmer"), "provider": "pending"}],
        "exercises": [{"id": "e1", "image": {"prompt": "", "spec": spec("Heft"),
                                             "provider": "pending"}}],
        "slide": {
            "kind": "picture_set",
            "pictures": [{"spec": spec("Tisch"), "provider": "pending"},
                         {"spec": spec("Stuhl"), "provider": "pending"}],
            "scene": {"spec": spec("Schule"), "provider": "pending"},
        }}]}

    # The search half is stubbed to find nothing, so every picture falls through
    # to the generator and the walk is what is being measured — not which route
    # a given concept happens to have a stock photograph for. Also keeps the
    # test off the network.
    def no_photo(*a, **kw):
        return {"provider": "failed", "reason": "stubbed", "url": ""}

    original, images.generate = images.generate, fake_generate
    no_search, images.search_photo = images.search_photo, no_photo
    try:
        result = images.produce_for_package(package, lesson_id="t", limit=20)
    finally:
        images.generate, images.search_photo = original, no_search

    assert result["generated"] == 5
    assert set(made) == {"Klassenzimmer", "Heft", "Tisch", "Stuhl", "Schule"}
    # And the urls land on the components, not beside them.
    assert package["items"][0]["slide"]["pictures"][0]["url"] == "https://x/new.png"
    assert package["items"][0]["slide"]["scene"]["url"] == "https://x/new.png"


def test_a_component_picture_carries_its_own_brief():
    # Without a spec there is nothing to generate from, which is how the
    # pictures came back attached to the wrong field.
    from zanoba_agent.schemas.slides import Picture

    assert "spec" in Picture.model_fields
    assert Picture().provider == "pending"


def test_a_cell_may_bold_part_of_a_word_but_not_inject_markup():
    # The agent writes "wohn-<b>e</b>" to bold the ending it is teaching, which
    # Cell.emphasis cannot express. Everything else stays escaped.
    from zanoba_agent.material.layouts import rich

    assert rich("wohn-<b>e</b>") == "wohn-<b>e</b>"
    assert rich("<script>alert(1)</script>") == "&lt;script&gt;alert(1)&lt;/script&gt;"
    assert rich("3 < 5") == "3 &lt; 5"


def test_an_item_that_numbers_itself_is_not_numbered_twice():
    # The renderer numbers every row, so "1. Sarah is from the UK." printed as
    # "1  1. Sarah is from the UK."
    from zanoba_agent.material.layouts import question_list

    html = question_list({"kind": "question_list", "title": "t", "instruction": "i",
                          "items": [{"text": "1. Sarah is from the UK."},
                                    {"text": "2) Alex is from Canada."},
                                    {"text": "Alex and Sarah are in an office."}]})
    assert "1. Sarah" not in html and "Sarah is from the UK." in html
    assert "2) Alex" not in html and "Alex is from Canada." in html
    # A sentence that merely starts with a digit is left alone.
    assert "Alex and Sarah are in an office." in html


def test_line_breaks_in_an_item_survive_to_the_page():
    # A multiple-choice item arrives as one string with its options on separate
    # lines. HTML collapsed the real newline to a space; an escaped one printed
    # as a literal backslash-n mid-sentence.
    from zanoba_agent.material.layouts import rich

    assert rich("'Hi, I'm Sarah.'\na) Nice to meet you.") == \
        "'Hi, I'm Sarah.'<br>a) Nice to meet you."
    assert rich("'Hi, I'm Sarah.'\\na) Nice to meet you.") == \
        "'Hi, I'm Sarah.'<br>a) Nice to meet you."
    # Escaping is unaffected.
    assert rich("3 < 5") == "3 &lt; 5"


def test_a_crowded_picture_grid_is_sized_to_fit_the_slide():
    # Eight pictures at the four-picture height made a grid taller than the
    # pane; it overflowed upward and printed its first row over the instruction.
    from zanoba_agent.material.layouts import _tile_height, picture_set

    assert _tile_height(4) > _tile_height(6) > _tile_height(8)
    def grid(n):
        return picture_set({"kind": "picture_set", "title": "t", "instruction": "i",
                            "pictures": [{"url": f"https://x/{i}.jpg", "caption": ""}
                                         for i in range(n)]})
    assert f"height:{_tile_height(4)}px" in grid(4)
    assert f"height:{_tile_height(8)}px" in grid(8)


def test_the_cover_prefers_a_scene_over_an_isolated_object():
    # The cover panel is a tall strip, so a close-up of one object on a plain
    # ground crops to an unrecognisable shape — a waving hand became a brown
    # smear down the side of the first page a student sees.
    from zanoba_agent.material import deck

    made = lambda name: {"provider": "searched", "url": f"https://x/{name}.jpg"}
    package = {"items": [
        {"id": "i1", "slide": {"kind": "picture_set",
                               "pictures": [made("hand"), made("taxi")]}},
        {"id": "i2", "slide": {"kind": "dialogue", "scene": made("cafe")}},
    ]}
    slides = deck.build_slides(package, {"activities": []}, {"objectives": []})
    assert slides[0]["kind"] == "cover"
    assert slides[0]["images"][0]["url"].endswith("cafe.jpg")
