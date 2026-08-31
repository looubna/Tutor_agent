"""The deterministic half of curriculum retrieval.

These run without a model. Ordering, prerequisites and the language/STEM shape
difference are all index work, and if they are wrong no instruction written for
the agent above can rescue them.
"""

from __future__ import annotations

import pytest

from zanoba_agent.curriculum import repository


def test_both_domains_are_detected_from_the_file_itself():
    assert repository.domain_of("german") == "language"
    assert repository.domain_of("mathematics") == "stem"


def test_unknown_subject_names_what_is_available():
    with pytest.raises(repository.CurriculumNotFound) as exc:
        repository.load("klingon")
    assert "german" in str(exc.value)


def test_language_items_are_flattened_in_teaching_order():
    items = repository.items_in_order("german", "a1-1")
    assert [x.order for x in items] == list(range(1, len(items) + 1))
    # Chapters stay contiguous: a chapter's lessons are not interleaved.
    seen: list[str] = []
    for item in items:
        if item.parent_id not in seen:
            seen.append(item.parent_id)
    assert len(seen) == len(set(seen))


def test_language_lesson_carries_its_own_focus():
    items = {x.id: x for x in repository.items_in_order("german", "a1-1")}
    assert items["a1-1.classroom.l1"].focus == "vocabulary"
    assert items["a1-1.classroom.l3"].focus == "grammar"
    # An orientation lesson teaches no single skill and must not claim one.
    assert items["a1-1.get-started.l1"].focus is None


def test_stem_units_stand_in_for_lessons_where_none_are_authored():
    # A unit with no lessons beneath it is still bookable — the planner teaches
    # the unit. The US ladder is still at that stage.
    items = repository.items_in_order("mathematics", "6th-grade")
    assert items, "the US programme should be loaded"
    assert all(x.granularity == "unit" for x in items)


def test_the_french_programme_is_taught_lesson_by_lesson():
    # 6e now has authored lessons, so the teachable item is the lesson and not
    # the whole chapter — a chapter is several hours, and a booking is one.
    items = repository.items_in_order("mathematics", "fr.sixieme")
    assert items, "the French programme should be loaded"
    assert all(x.granularity == "lesson" for x in items)
    assert items[0].title == "Lire et écrire les nombres entiers"
    assert items[0].parent_title == "Nombres entiers et décimaux"


def test_every_french_maths_unit_has_lessons():
    # "Finish the French programme" means no chapter is left as a bare heading.
    for level in ("fr.sixieme", "fr.cinquieme", "fr.quatrieme", "fr.troisieme",
                  "fr.seconde", "fr.premiere", "fr.terminale"):
        items = repository.items_in_order("mathematics", level)
        assert items, f"{level} has no teachable items"
        assert all(x.granularity == "lesson" for x in items), \
            f"{level} still has chapters with no lessons under them"


def test_the_french_programme_is_written_in_french():
    # A French maths course is in French. Nothing here should read as English.
    from zanoba_agent.material.language_purity import check_text

    for level in ("fr.sixieme", "fr.troisieme", "fr.terminale"):
        for item in repository.items_in_order("mathematics", level):
            for text in [item.title, *item.objectives]:
                assert check_text(text, "french")["is_target_language"], \
                    f"{item.id}: {text!r} does not read as French"


def test_prerequisites_follow_syllabus_order():
    prereqs = repository.prerequisites_of("german", "a1-1.classroom.l3")
    assert prereqs == [
        "a1-1.get-started.l1",
        "a1-1.classroom.l1",
        "a1-1.classroom.l2",
    ]


def test_the_first_item_of_a_level_has_no_prerequisites():
    items = repository.items_in_order("german", "a1-1")
    assert repository.prerequisites_of("german", items[0].id) == []


def test_prerequisites_do_not_leak_across_levels():
    # a1-2 sits after a1-1, but ordering inside a level must not drag in
    # everything from the level before — those are different questions.
    for item in repository.items_in_order("german", "a1-2")[:1]:
        assert all(not p.startswith("a1-1.") for p in repository.prerequisites_of("german", item.id))


def test_unknown_item_resolves_to_nothing_rather_than_raising():
    assert repository.find_item("german", "a1-1.nope.l9") is None
    assert repository.prerequisites_of("german", "a1-1.nope.l9") == []


def test_every_subject_file_loads():
    for subject in repository.available_subjects():
        curriculum = repository.load(subject)
        assert curriculum.curriculum_id
        assert repository.level_ids(subject), f"{subject} has no levels"
