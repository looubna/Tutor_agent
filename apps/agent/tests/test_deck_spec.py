"""The lesson-deck format requirements, taken from the reference decks."""

from __future__ import annotations

import json

from zanoba_agent.agents.quality_checker import check_deck_format, quality_checker_agent
from zanoba_agent.material.deck_spec import MIN_IMAGE_COVERAGE, MIN_SLIDES, check_deck


def _slide(n, kind="explanation", images=None, body="A short line of teaching.", **kw):
    return {"number": n, "kind": kind, "title": f"Slide {n}", "body": body,
            "images": images or [], **kw}


def _good_image():
    return {"provider": "generated", "url": "https://x/i.png",
            "alt_text": "A classroom.", "purpose": "context", "prompt": "classroom"}


def _deck(n=MIN_SLIDES, images_from=2):
    slides = [_slide(1, "cover"), _slide(2, "objectives")]
    slides += [_slide(i, images=[_good_image()] if i >= images_from else [])
               for i in range(3, n)]
    slides.append(_slide(n, "recap", phase="recap"))
    return {"slides": slides}


def test_a_compliant_deck_passes():
    assert check_deck(_deck())["compliant"] is True


def test_a_short_deck_is_rejected():
    r = check_deck(_deck(n=8))
    assert r["compliant"] is False
    assert any(v["rule"] == "slide_count" for v in r["violations"])


def test_a_pending_image_is_a_blocking_failure():
    # The rule this whole spec exists for: a specification is a promise, and a
    # deck of promises arrives at the lesson blank.
    deck = _deck()
    deck["slides"][5]["images"] = [
        {"provider": "pending", "alt_text": "A classroom.", "prompt": "classroom"}]
    r = check_deck(deck)
    assert r["compliant"] is False
    assert r["images_pending"] >= 1
    assert any(v["rule"] == "image_not_produced" and v["severity"] == "high"
               for v in r["violations"])


def test_an_image_with_a_url_but_no_alt_text_is_flagged():
    deck = _deck()
    deck["slides"][5]["images"] = [
        {"provider": "generated", "url": "https://x/i.png", "alt_text": ""}]
    assert any(v["rule"] == "image_alt_text" for v in check_deck(deck)["violations"])


def test_too_few_illustrated_slides_is_rejected():
    r = check_deck(_deck(images_from=99))   # nothing illustrated
    assert r["compliant"] is False
    assert r["image_coverage"] < MIN_IMAGE_COVERAGE
    assert any(v["rule"] == "image_coverage" for v in r["violations"])


def test_text_only_phases_are_not_penalised_for_having_no_image():
    # An IPA drill or a recap legitimately has no photograph.
    deck = {"slides": [_slide(1, "cover"), _slide(2, "objectives")]
            + [_slide(i, phase="recap") for i in range(3, MIN_SLIDES)]
            + [_slide(MIN_SLIDES, "recap", phase="recap")]}
    assert not any(v["rule"] == "image_coverage" for v in check_deck(deck)["violations"])


def test_the_deck_must_open_with_cover_then_objectives():
    deck = _deck()
    deck["slides"][0]["kind"] = "explanation"
    assert any(v["rule"] == "structure" for v in check_deck(deck)["violations"])


def test_an_overloaded_slide_breaks_one_idea_per_slide():
    deck = _deck()
    deck["slides"][4]["body"] = "word " * 120
    assert any(v["rule"] == "slide_density" for v in check_deck(deck)["violations"])


def test_an_activity_slide_needs_an_instruction_line():
    deck = _deck()
    deck["slides"][4]["exercises"] = [{"prompt": "___ Tisch", "answer": "der"}]
    assert any(v["rule"] == "missing_instruction" for v in check_deck(deck)["violations"])


def test_an_item_based_package_is_checked_as_slides():
    # The material agents emit items, not slides. The check adapts rather than
    # silently passing a package it does not recognise.
    package = json.dumps({"items": [
        {"id": "m1", "kind": "text", "title": "T", "content": "Short.",
         "images": [{"provider": "pending", "alt_text": "x"}]}]})
    r = check_deck_format(package)
    assert r["compliant"] is False
    assert r["slide_count"] == 1


def test_the_checker_has_the_format_gate_wired():
    names = {t.__name__ for t in quality_checker_agent.tools}
    assert "check_deck_format" in names
    # An image record that promises a picture nobody made is the failure that
    # produces a deck which looks complete and arrives blank.
    assert "promise" in quality_checker_agent.instruction


# ---- per-item pictures reach the slide -------------------------------------

def _picture_package(count=6):
    from zanoba_agent.material import deck  # noqa: F401

    return {"items": [{
        "id": "m1", "activity_id": "a1", "kind": "exercise_set", "stage": "warm-up",
        "title": "Wie heißt das?", "instruction": "Ordne zu.", "content": "",
        "exercises": [
            {"id": f"e{n}", "prompt": "", "answer": word,
             "image": {"url": f"https://x/{n}.png", "provider": "generated"}}
            for n, word in enumerate(
                ["Garten", "Telefon", "Ball", "Park", "Haus", "Katze"][:count], 1)]}]}


def test_a_picture_set_stays_on_one_slide():
    # Splitting six numbered photographs across two slides breaks the numbering
    # the learner is matching against.
    from zanoba_agent.material import deck

    slides = deck.build_slides(_picture_package(6),
                               {"activities": [{"id": "a1", "phase": "warm-up"}]},
                               {"objectives": []})
    practice = [s for s in slides if s["kind"] == "practice"]
    assert len(practice) == 1
    assert len(practice[0]["exercises"]) == 6


def test_per_item_pictures_actually_render():
    # They were generated and then dropped: the practice slide only drew text
    # prompts, so every picture in a matching task was paid for and never seen.
    from zanoba_agent.material import deck

    slides = deck.build_slides(_picture_package(6),
                               {"activities": [{"id": "a1", "phase": "warm-up"}]},
                               {"objectives": []})
    html = deck.render_html(slides)
    assert html.count('class="shot"') == 6
    for n in range(1, 7):
        assert f"https://x/{n}.png" in html


def test_the_word_is_a_blank_when_the_learner_must_supply_it():
    from zanoba_agent.material import deck

    slides = deck.build_slides(_picture_package(4),
                               {"activities": [{"id": "a1", "phase": "warm-up"}]},
                               {"objectives": []})
    html = deck.render_html(slides)
    # No prompt text given, so the caption is a rule to write on, not the answer.
    assert html.count('class="blank"') == 4
    assert "Garten" not in html, "the answer must not be printed on the worksheet"


# ---- the deck wears the product's brand ------------------------------------

def test_the_deck_uses_the_web_app_palette():
    # The deck a student downloads is the product. It used to be drawn in a
    # purple-to-magenta gradient copied off the reference lessons, which is
    # another company's brand.
    from zanoba_agent.material import brand, deck

    css = deck._CSS
    assert brand.colour("primary") in css
    assert brand.colour("foreground") in css
    assert brand.colour("primary-tint") in css
    for borrowed in ("#6d28f5", "#3b2ff0", "#d6249f", "#dde6fb", "#2f27e8"):
        assert borrowed not in css, f"{borrowed} is not a Zanoba colour"


def test_the_palette_is_read_from_the_frontend_not_restated():
    # Two copies of a brand drift. The stylesheet wins when it is on disk.
    from zanoba_agent.material import brand

    assert brand.tokens()["primary"] == "#743ee4"
    assert brand._GLOBALS_CSS.exists(), "the web app's stylesheet should be found"


def test_the_brand_survives_deploying_the_agent_alone():
    # Cloud Run gets the agent without the frontend. A deck that renders
    # unbranded in production because a sibling directory was missing would be
    # a strange way to fail.
    from zanoba_agent.material import brand

    assert brand._VENDORED["primary"] == brand.tokens()["primary"], \
        "the vendored fallback must match what the stylesheet says"


def test_the_logo_is_embedded_not_linked():
    # Chrome prints the deck with no network. A remote src would leave a blank
    # corner on every slide and nothing would report it.
    from zanoba_agent.material import brand, deck

    uri = brand.logo_data_uri()
    assert uri.startswith("data:image/png;base64,")
    assert len(uri) > 1000, "the logo should actually be in there"
    assert uri in deck._CSS


def test_every_slide_carries_the_mark_and_the_cover_the_lockup():
    from zanoba_agent.material import deck

    slides = deck.build_slides(
        {"items": [{"id": "m1", "activity_id": "a1", "kind": "explanation",
                    "title": "Die drei Artikel", "content": "Der, die, das.",
                    "images": []}],
         "target_item_title": "der, die, das"},
        {"activities": [{"id": "a1", "phase": "explanation"}], "focus": "grammar"},
        {"objectives": [{"statement": "Ich kann die Artikel unterscheiden."}]})
    html = deck.render_html(slides)
    # One mark per non-cover slide, plus the full lockup on the cover.
    assert html.count('class="mark"') == len(slides) - 1
    assert html.count('class="logo"') == 1


# ---- a dialogue is turns, not a paragraph ----------------------------------

RUN_ON = ("Herr Müller: Hallo Tim! Wo ist das Buch? Tim: Hallo Herr Müller! Hier "
          "ist das Buch. Herr Müller: Und wo ist die Schere? Tim: Die Schere ist "
          "auf dem Tisch. Herr Müller: Danke, Tim!")


def test_a_run_on_dialogue_is_split_into_turns():
    # What the generator actually produced: every turn in one paragraph. A
    # learner cannot follow it and it does not look like a conversation.
    from zanoba_agent.material.deck import _dialogue_turns, is_dialogue

    assert is_dialogue(RUN_ON)
    turns = _dialogue_turns(RUN_ON)
    assert [who for who, _ in turns] == [
        "Herr Müller", "Tim", "Herr Müller", "Tim", "Herr Müller"]
    assert turns[1][1] == "Hallo Herr Müller! Hier ist das Buch."


def test_the_previous_sentence_is_not_absorbed_into_the_speaker():
    # "... Hier ist das Buch. Herr Müller: ..." must not yield a speaker called
    # "Buch. Herr Müller" — the last word of a sentence is capitalised too.
    from zanoba_agent.material.deck import _dialogue_turns

    assert all("." not in who for who, _ in _dialogue_turns(RUN_ON))


def test_prose_is_not_mistaken_for_a_dialogue():
    from zanoba_agent.material.deck import is_dialogue

    assert not is_dialogue(
        "Im Deutschen hat jedes Nomen ein Geschlecht. Das ist wichtig. "
        "Man lernt den Artikel mit dem Wort.")


def test_dialogue_turns_render_one_per_line():
    from zanoba_agent.material import deck

    slides = deck.build_slides(
        {"items": [{"id": "m1", "activity_id": "a1", "kind": "dialogue",
                    "stage": "context", "title": "Im Klassenzimmer",
                    "content": RUN_ON, "images": []}]},
        {"activities": [{"id": "a1", "phase": "context"}]}, {"objectives": []})
    html = deck.render_html(slides)
    assert html.count('class="turn"') == 5
    assert '<span class="who">Herr Müller</span>' in html


def test_the_cover_carries_a_photograph_not_a_void():
    # An empty left panel printed as a dark void down 42% of the first page.
    from zanoba_agent.material import deck

    package = {"subject": "german", "target_item_title": "der, die, das",
               "items": [{"id": "m1", "activity_id": "a1", "kind": "text",
                          "title": "T", "content": "Kurz.",
                          "images": [{"provider": "generated",
                                      "url": "https://x/cover.png",
                                      "alt_text": "a", "purpose": "p"}]}]}
    slides = deck.build_slides(package, {"activities": []}, {"objectives": []})
    assert slides[0]["kind"] == "cover"
    assert slides[0]["images"], "the cover should reuse a lesson photograph"
    assert "https://x/cover.png" in deck.render_html(slides)


def test_the_cover_names_the_language_in_itself():
    # "SPRACHE: German" puts an English word on the cover of a German deck.
    from zanoba_agent.material import brand, deck

    slides = deck.build_slides({"subject": "german", "items": [
        {"id": "m1", "activity_id": "a1", "kind": "text", "title": "T",
         "content": "Kurz.", "images": []}]}, {"activities": []}, {"objectives": []})
    assert slides[0]["language"] == "Deutsch"
    assert brand.language_name("french") == "Français"
