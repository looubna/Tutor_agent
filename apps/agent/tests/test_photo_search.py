"""The picture pipeline's second route: finding a real photograph.

Every test here is offline. `photos.search` is the only thing that talks to a
network and it is stubbed everywhere, because a test suite whose result depends
on what Openverse ranked first this morning is not a test suite.
"""

from __future__ import annotations

import pytest

from zanoba_agent.material import images, layouts, photos
from zanoba_agent.schemas.blueprint import VisualSpec


def spec(**overrides) -> dict:
    base = {
        "target_concept": "Tisch", "visual_type": "direct_concept",
        "language_level": "A1", "pedagogical_purpose": "vocabulary retrieval",
        "main_subject": "a wooden dining table", "composition": "centred, plain ground",
    }
    return base | overrides


# ------------------------------------------------------ the search query ----

def test_the_search_query_drops_the_exclusions():
    # A generator is told what to leave out. A search engine handed "no people"
    # returns pictures of people, so the two strings cannot be the same string.
    written = VisualSpec(**spec(must_show=["four legs"],
                                must_not_show=["chairs", "people"]))
    query = written.to_search_query()
    assert "chairs" not in query and "people" not in query
    assert "wooden dining table" in query
    assert "four legs" in query
    # The generator prompt still carries them — that is what it is for.
    assert "chairs" in written.to_prompt()


def test_an_explicit_search_query_wins():
    written = VisualSpec(**spec(search_query="empty classroom desk plain background"))
    assert written.to_search_query() == "empty classroom desk plain background"


def test_the_query_does_not_repeat_itself():
    # must_show routinely restates the subject, and searching for the same words
    # twice ranks worse than searching for them once.
    written = VisualSpec(**spec(main_subject="a wooden table",
                                must_show=["wooden table", "flat top"]))
    words = written.to_search_query().split()
    assert len(words) == len({w.lower() for w in words})


# --------------------------------------------------------- which route ------

def _routes(monkeypatch, *, photo_found: bool):
    """Record which route each picture actually took."""
    taken: list[str] = []

    def fake_search(query, alt_text, purpose, lesson_id="", orientation="landscape"):
        taken.append("search")
        if photo_found:
            return {"provider": "searched", "url": "https://x/found.jpg",
                    "credit": "A Photographer · CC BY 4.0 · Openverse",
                    "source_page": "https://example.org/p", "prompt": query}
        return {"provider": "failed", "reason": "nothing found", "url": ""}

    def fake_generate(**kw):
        taken.append("generate")
        return {"provider": "generated", "url": "https://x/made.png", "prompt": "p"}

    monkeypatch.setattr(images, "search_photo", fake_search)
    monkeypatch.setattr(images, "generate", fake_generate)
    return taken


def test_auto_searches_first(monkeypatch):
    taken = _routes(monkeypatch, photo_found=True)
    result = images.resolve({"spec": spec()}, lesson_id="t")
    assert taken == ["search"]
    assert result["provider"] == "searched"
    assert result["credit"].startswith("A Photographer")


def test_auto_falls_back_to_generating(monkeypatch):
    # A blank slide is worse than a picture from the other route, so an empty
    # search is not a failure — but it is recorded, because "we asked for a
    # photograph and got a rendering" should be visible in the material.
    taken = _routes(monkeypatch, photo_found=False)
    result = images.resolve({"spec": spec()}, lesson_id="t")
    assert taken == ["search", "generate"]
    assert result["provider"] == "generated"
    assert "nothing found" in result["search_fallback"]


def test_generate_does_not_search(monkeypatch):
    # The staged scene with the exact props an exercise names. Searching for it
    # wastes a request and risks returning something plausible and wrong.
    taken = _routes(monkeypatch, photo_found=True)
    result = images.resolve({"spec": spec(source="generate")}, lesson_id="t")
    assert taken == ["generate"]
    assert result["provider"] == "generated"


def test_photo_search_still_falls_back(monkeypatch):
    taken = _routes(monkeypatch, photo_found=False)
    images.resolve({"spec": spec(source="photo_search")}, lesson_id="t")
    assert taken == ["search", "generate"]


# ------------------------------------------------------------- backfill ----

def test_a_picture_with_no_brief_gets_one_from_its_own_answer():
    # The defect this exists for: the material agent writes a picture set with
    # captions and answers and forgets the specs, so the pipeline skips every
    # one and the slide prints as five captions with holes above them.
    package = {"items": [{"id": "m1", "slide": {
        "kind": "picture_set",
        "pictures": [
            {"answer": "der Tisch", "alt_text": "Ein Holztisch.", "provider": "pending"},
            {"caption": "die Lampe", "alt_text": "Eine Lampe.", "provider": "pending"},
            {"alt_text": "Ein offenes Buch auf weissem Hintergrund.",
             "provider": "pending"},
        ]}}]}

    assert images.backfill_specs(package) == 3
    pictures = package["items"][0]["slide"]["pictures"]
    # The article is what a German vocabulary card teaches and no help at all to
    # a photo library.
    assert pictures[0]["search_query"] == "Tisch"
    assert pictures[1]["search_query"] == "Lampe"
    # Falling back to the alt text, with the words that describe a photograph
    # rather than appear in one stripped out.
    assert "offenes" in pictures[2]["search_query"]
    assert "auf" not in pictures[2]["search_query"].split()


def test_backfill_leaves_a_picture_that_already_has_a_brief():
    package = {"items": [{"id": "m1", "slide": {"kind": "picture_set", "pictures": [
        {"spec": spec(), "provider": "pending"},
        {"prompt": "already written", "provider": "pending"},
        {"answer": "Tisch", "provider": "generated", "url": "https://x/y.png"},
    ]}}]}
    assert images.backfill_specs(package) == 0


# ------------------------------------------------------------- the deck ----

def test_no_source_line_is_printed_on_a_slide():
    # A credit under every image is clutter on a teaching slide. The attribution
    # stays on the record; it just does not reach the page.
    html = layouts.picture_set({
        "kind": "picture_set", "title": "t", "instruction": "i",
        "pictures": [
            {"url": "https://x/a.jpg", "caption": "der Tisch",
             "credit": "A Photographer · Pexels License · Pexels"},
            {"url": "https://x/b.png", "caption": "die Lampe"},
        ]})
    assert "Pexels" not in html and 'class="credit"' not in html
    assert "https://x/a.jpg" in html and "der Tisch" in html


def test_uncredited_slides_mean_only_pexels_is_searched(monkeypatch):
    # A CC BY photograph on an uncredited slide is a licence violation. With a
    # key, Pexels is the only library used; without one the CC aggregators are
    # the fallback, because the alternative there is no lesson at all.
    monkeypatch.setenv("PEXELS_API_KEY", "k")
    assert [n for n, _ in photos._providers()] == ["pexels"]
    monkeypatch.delenv("PEXELS_API_KEY")
    assert [n for n, _ in photos._providers()] == ["openverse", "wikimedia"]


def test_a_black_and_white_photograph_is_rejected():
    # A vocabulary test came back with a monochrome Sagrada Familia sitting
    # between four colour flags, which reads as a mistake rather than a style.
    import io

    from PIL import Image

    def encode(pixels):
        image = Image.new("RGB", (64, 64))
        image.putdata(pixels * (4096 // len(pixels)))
        buffer = io.BytesIO()
        image.save(buffer, "PNG")
        return buffer.getvalue()

    assert photos.is_monochrome(encode([(90, 90, 90), (200, 200, 200)]))
    assert not photos.is_monochrome(encode([(255, 0, 0), (0, 120, 255)]))
    # An undecodable blob is not judged monochrome — that would throw away a
    # usable photograph over a decoder problem.
    assert not photos.is_monochrome(b"not an image")


def test_the_deck_renders_a_searched_photograph():
    # Gating on provider == "generated" predated the search and silently dropped
    # every photograph the pipeline found rather than drew.
    from zanoba_agent.material import deck

    assert "searched" in deck._PRODUCED and "generated" in deck._PRODUCED


# ------------------------------------------------------- the search itself ---

def test_an_unusable_candidate_is_rejected_before_it_is_downloaded():
    assert not photos._usable({"url": "https://x/flag.svg", "width": 2000})
    assert not photos._usable({"url": "https://x/tiny.jpg", "width": 320})
    assert not photos._usable({"url": "", "width": 2000})
    assert photos._usable({"url": "https://x/good.jpg", "width": 1024})


def test_an_empty_query_never_reaches_a_library(monkeypatch):
    monkeypatch.setattr(photos, "PROVIDERS", ())
    assert photos.search("   ")["candidates"] == []


def test_a_library_that_is_down_does_not_fail_the_lesson(monkeypatch):
    def broken(query, count, orientation):
        raise RuntimeError("503")

    def working(query, count, orientation):
        return [{"provider": "w", "url": "https://x/a.jpg", "title": "a table",
                 "creator": "c", "license": "CC BY", "license_url": "",
                 "source_page": "", "width": 1024, "height": 768}]

    monkeypatch.setattr(photos, "PROVIDERS", (("broken", broken), ("working", working)))
    result = photos.search("table")
    assert result["provider"] == "working"
    assert "broken (RuntimeError)" in result["attempted"]


def test_the_credit_line_names_who_what_and_where():
    assert photos.credit({"creator": "Jane Doe", "license": "CC BY 4.0",
                          "provider": "openverse"}) == "Jane Doe · CC BY 4.0 · Openverse"
    assert photos.credit({"license": "Pexels License",
                          "provider": "pexels"}) == "Pexels License · Pexels"


@pytest.mark.parametrize("source", ["auto", "photo_search", "generate"])
def test_every_source_is_a_valid_spec(source):
    assert VisualSpec(**spec(source=source)).source == source


def test_the_ladder_drops_qualifiers_one_rung_at_a_time():
    # "wooden dining table plain background" is exactly the right description
    # and returns nothing; "wooden dining table" returns a hundred. Precision
    # first, then recall.
    rungs = VisualSpec(**spec(main_subject="a wooden dining table",
                              must_show=["four legs", "flat top"])).to_search_queries()
    assert rungs[0].endswith("plain background")
    assert rungs[-1] == "Tisch"
    assert all(rungs[i] != rungs[i + 1] for i in range(len(rungs) - 1))


def test_the_search_tries_every_rung_before_giving_up(monkeypatch):
    asked: list[str] = []

    def only_answers_the_short_one(query, count, orientation):
        asked.append(query)
        if query != "table":
            return []
        return [{"provider": "w", "url": "https://x/a.jpg", "title": "table",
                 "creator": "c", "license": "CC BY", "license_url": "",
                 "source_page": "", "width": 1024, "height": 768}]

    monkeypatch.setattr(photos, "PROVIDERS", (("w", only_answers_the_short_one),))
    result = photos.search(["table plain background", "wooden table", "table"])
    assert asked == ["table plain background", "wooden table", "table"]
    assert result["query"] == "table"
    assert result["rung"] == 2


def test_a_result_about_something_else_is_dropped(monkeypatch):
    # Asked for two women talking in a cafe, Wikimedia returned a bass guitarist
    # at the Hard Rock Cafe, ranked first. A title is weak evidence, but zero
    # overlap with the query is strong evidence that nobody filed this picture
    # under the thing being asked for.
    def wrong_thing(query, count, orientation):
        return [{"provider": "w", "url": "https://x/a.jpg",
                 "title": "Screaming Bikini (6465321649)", "creator": "c",
                 "license": "CC BY", "license_url": "", "source_page": "",
                 "width": 1024, "height": 768},
                {"provider": "w", "url": "https://x/b.jpg",
                 "title": "Two women talking over lunch", "creator": "c",
                 "license": "CC BY", "license_url": "", "source_page": "",
                 "width": 1024, "height": 768}]

    monkeypatch.setattr(photos, "PROVIDERS", (("w", wrong_thing),))
    result = photos.search("two women talking in a cafe")
    assert len(result["candidates"]) == 1
    assert result["candidates"][0]["title"].startswith("Two women")


def test_nothing_relevant_reads_as_no_results(monkeypatch):
    def only_junk(query, count, orientation):
        return [{"provider": "w", "url": "https://x/a.jpg",
                 "title": "[food] Minty Grapes", "creator": "c",
                 "license": "CC BY", "license_url": "", "source_page": "",
                 "width": 1024, "height": 768}]

    monkeypatch.setattr(photos, "PROVIDERS", (("w", only_junk),))
    result = photos.search("a cup of coffee")
    assert result["candidates"] == []
    assert "none about it" in result["attempted"][0]


def test_stopwords_do_not_count_as_a_match():
    # "plain background" and "a"/"the" appear in half of all titles; matching on
    # them would let anything through.
    assert photos.relevance({"title": "A plain white background"},
                            "a cup of coffee plain background") == 0.0


def test_the_checker_sees_the_pictures_the_deck_actually_renders():
    # A picture set whose five photographs were never produced scored a hundred
    # on visual quality, because the checker only ever looked at item["images"]
    # — the field the deck renders least.
    from zanoba_agent.material.validation import check_images

    package = {"items": [{"id": "s1", "slide": {
        "kind": "picture_set",
        "pictures": [{"alt_text": "Ein Tisch.", "provider": "pending", "url": ""},
                     {"alt_text": "Ein Stuhl.", "provider": "pending", "url": ""}],
    }}]}
    issues = check_images(package)
    blank = [i for i in issues if "not produced" in i["problem"]]
    assert len(blank) == 2
    assert {i["item_id"] for i in blank} == {"s1#pic0", "s1#pic1"}


def test_a_rejected_component_picture_can_be_remade_by_name(monkeypatch):
    # The checker's name and the regenerator's name have to agree, and they only
    # agree by being the same function.
    from zanoba_agent.material import images as im

    monkeypatch.setattr(im, "generate", lambda **kw: {
        "provider": "generated", "url": "https://x/redone.png", "prompt": "p"})
    package = {"items": [{"id": "s1", "slide": {"kind": "picture_set", "pictures": [
        {"spec": spec(), "provider": "searched", "url": "https://x/wrong.jpg"},
        {"spec": spec(), "provider": "searched", "url": "https://x/fine.jpg"},
    ]}}]}
    result = im.regenerate(package, [{"scope": "image", "target": "s1#pic0",
                                      "reasons": ["shows a doll's table"]}])
    assert result["regenerated"] == 1 and result["untouched"] == 1
    pictures = package["items"][0]["slide"]["pictures"]
    assert pictures[0]["url"] == "https://x/redone.png"
    assert pictures[0]["rejected_reasons"] == ["shows a doll's table"]
    # Everything not named is left exactly as it is.
    assert pictures[1]["url"] == "https://x/fine.jpg"


# --------------------------------------------- the checker and the slides ----

def test_a_sorting_grid_offers_its_options_on_the_slide():
    # The categories print once above the tiles; each item is "which column does
    # this word go in". The checker charged a twenty-point defect six times for a
    # slide that renders perfectly, which took a finished lesson to zero.
    from zanoba_agent.material.validation import check_structure

    item = {
        "id": "s5", "title": "Wortarten sortieren",
        "slide": {"kind": "sorting_grid", "tiles": ["Deutschland", "Spanien"],
                  "categories": ["Land", "Nationalität", "Sprache"]},
        "exercises": [{"id": "e1", "prompt": "Kategorie für: Deutschland",
                       "answer": "Land", "options": [],
                       "exercise_type": "classification"}],
    }
    assert not [i for i in check_structure(item) if "options" in i["problem"]]


def test_one_mistake_is_charged_once_not_once_per_item():
    # Six copies of one defect must cost less than six different defects, or the
    # score says the opposite of what is true.
    from zanoba_agent.material.validation import _score

    repeated = [{"severity": "high", "category": "technical", "item_id": f"s5/e{n}",
                 "problem": "classification item has 0 options"} for n in range(6)]
    varied = [{"severity": "high", "category": "technical", "item_id": f"s{n}",
               "problem": f"defect number {n} of a different kind"} for n in range(6)]
    assert _score(repeated) > _score(varied)
    # And a single repeated defect never zeroes an otherwise finished lesson.
    assert _score(repeated) >= 60


def test_picture_naming_counts_as_productive_retrieval():
    # A picture set with blank captions IS picture-to-word retrieval. Read off
    # the component, because the agent routinely leaves the field empty.
    from zanoba_agent.material.validation import inferred_direction

    naming = {"slide": {"kind": "picture_set", "pictures": [
        {"caption": ""}, {"caption": ""}]}}
    labelled = {"slide": {"kind": "picture_set", "pictures": [
        {"caption": "der Tisch"}, {"caption": "die Lampe"}]}}
    assert inferred_direction(naming) == "picture_to_word"
    # A caption already filled in is the recognition version of the same slide.
    assert inferred_direction(labelled) == "word_to_meaning"
    assert inferred_direction({"slide": {"kind": "tile_grid"}}) == "word_to_sentence"
    assert inferred_direction({}) == ""


def test_english_objectives_never_reach_a_german_deck():
    # The curriculum authors objectives in English, for the teacher. Falling
    # back to them put two English slides in the middle of a German deck.
    from zanoba_agent.material.deck import target_language_objectives

    english = {"objectives": [{"statement": "I can say which languages I speak."}]}
    assert target_language_objectives({"target_language": "german"}, english) == []
    # What the agent wrote in German is used as-is.
    written = {"target_language": "german",
               "learner_objectives": ["Ich kann sagen, woher ich komme."]}
    assert target_language_objectives(written, english) == written["learner_objectives"]
    # An English lesson keeps its English objectives.
    assert target_language_objectives({"target_language": "english"}, english)


def test_a_picture_needs_only_a_search_query(monkeypatch):
    # Copying a fifteen-field VisualSpec onto each of twenty pictures made a
    # vocabulary lesson's output too large for the agent to finish. A short
    # English search string carries the same information for the pipeline.
    from zanoba_agent.material.validation import check_images

    package = {"items": [{"id": "s1", "slide": {"kind": "picture_set", "pictures": [
        {"search_query": "a red apple on a white background", "alt_text": "an apple",
         "provider": "searched", "url": "https://x/a.jpg"}]}}]}
    assert [i for i in check_images(package) if "search query" in i["problem"]] == []

    # But a picture that says nothing about itself is still a defect.
    silent = {"items": [{"id": "s1", "slide": {"kind": "picture_set", "pictures": [
        {"alt_text": "", "provider": "searched", "url": "https://x/a.jpg"}]}}]}
    assert [i for i in check_images(silent) if "search query" in i["problem"]]
