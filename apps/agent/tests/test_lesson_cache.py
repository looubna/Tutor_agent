"""Prepared lessons, cached — and personalised without rebuilding them.

The claim this file exists to check: most of building a lesson is not about the
student, so it can be done once, ahead of time, and served instantly; and the
part that IS about the student touches a handful of slots, not the lesson.
"""

from __future__ import annotations

import pytest

from zanoba_agent.material import cache


@pytest.fixture(autouse=True)
def temporary_cache(tmp_path):
    cache.set_cache(cache.FileLessonCache(tmp_path))
    yield
    cache.set_cache(cache.FileLessonCache())


def blueprint_of(grammar_blueprint):
    return grammar_blueprint.model_dump()


# ---- the store -------------------------------------------------------------

def test_a_stored_lesson_comes_back(grammar_blueprint):
    key = cache.baseline_key("german", "a1-1.classroom.l3", "A1")
    cache.store(key, blueprint_of(grammar_blueprint), {"items": [{"id": "m1"}]},
                {"activities": []}, {"objectives": []})
    entry = cache.load(key)
    assert entry["material"]["items"][0]["id"] == "m1"
    assert cache.load_baseline("german", "a1-1.classroom.l3", "A1") is not None


def test_a_miss_is_a_miss_not_a_crash():
    assert cache.load_baseline("german", "nothing.here", "A1") is None


def test_material_built_under_an_older_rubric_is_not_served(grammar_blueprint):
    # A cached lesson from before a rule change may violate the rule that
    # replaced it. Serving it would quietly reintroduce the defect the change
    # was made to prevent.
    key = cache.baseline_key("german", "a1-1.classroom.l3", "A1")
    cache.store(key, blueprint_of(grammar_blueprint), {}, {}, {})
    raw = cache._cache.get(key)
    raw["version"] = "0"
    cache._cache.put(key, raw)
    assert cache.load(key) is None


def test_the_baseline_is_shared_by_every_student():
    # The point of the split: "der, die, das" at A1 is the same lesson for
    # everyone who reaches it, so it is built once and not once per learner.
    first = cache.baseline_key("german", "a1-1.classroom.l3", "A1")
    second = cache.baseline_key("german", "a1-1.classroom.l3", "A1")
    assert first == second
    assert "stu-" not in first


# ---- the fingerprint -------------------------------------------------------

def test_the_same_student_state_gives_the_same_fingerprint():
    diagnosis = {"readiness": "ready", "recommended_difficulty": "at"}
    assert cache.fingerprint(diagnosis) == cache.fingerprint(dict(diagnosis))


def test_learning_something_supersedes_the_old_personalisation():
    before = cache.fingerprint({"readiness": "ready_with_review",
                                "review_first": ["a1-1.classroom.l1"]})
    after = cache.fingerprint({"readiness": "ready", "review_first": []})
    assert before != after, "a learner who has closed the gap must not be served "\
                            "material that still compensates for it"


def test_irrelevant_profile_changes_do_not_invalidate_the_cache():
    # A fingerprint that moved whenever any field was touched would invalidate
    # constantly and buy nothing.
    diagnosis = {"readiness": "ready", "recommended_difficulty": "at"}
    profile = {"preferences": {"likes_visual_material": True}}
    first = cache.fingerprint(diagnosis, profile)
    second = cache.fingerprint(diagnosis, {**profile, "age": 31,
                                           "last_seen": "2026-08-30"})
    assert first == second


# ---- what personalisation actually costs -----------------------------------

def test_a_learner_with_no_diagnosed_gaps_reuses_everything(grammar_blueprint):
    plan = cache.personalisation_plan(
        blueprint_of(grammar_blueprint),
        {"readiness": "ready", "recommended_difficulty": "at"})
    assert plan["scope"] == "reuse"
    assert plan["regenerate"] == []
    assert plan["reuse_images"] is True


def test_a_gap_regenerates_the_practice_not_the_lesson(grammar_blueprint):
    blueprint = blueprint_of(grammar_blueprint)
    plan = cache.personalisation_plan(blueprint, {
        "readiness": "ready_with_review",
        "review_first": ["a1-1.classroom.l1"],
        "recommended_difficulty": "at"})
    assert plan["scope"] == "targeted"
    assert plan["regenerate"], "a diagnosed gap must change something"
    # The rule table and the context dialogue are the same for everyone.
    stages = {s["slot_id"]: s["stage"] for s in blueprint["slots"]}
    touched = {stages[s] for s in plan["regenerate"]}
    assert "explanation" not in touched
    assert "context" not in touched
    saving = cache.savings(blueprint, plan)
    assert saving["slots_reused"] > saving["slots_regenerated"]


def test_images_survive_personalisation(grammar_blueprint):
    # Images are the expensive half and are almost never what personalisation
    # changes: a picture of a garden is a picture of a garden whoever looks.
    blueprint = blueprint_of(grammar_blueprint)
    plan = cache.personalisation_plan(blueprint, {
        "readiness": "ready", "recommended_difficulty": "below"})
    assert plan["reuse_images"] is True
    assert cache.savings(blueprint, plan)["images_remade"] == 0


def test_a_learner_who_is_not_ready_gets_a_different_lesson(grammar_blueprint):
    # The one case where reuse would be wrong: the hour goes to prerequisites,
    # so this is not the cached lesson pitched differently, it is another lesson.
    plan = cache.personalisation_plan(blueprint_of(grammar_blueprint),
                                      {"readiness": "not_ready"})
    assert plan["scope"] == "rebuild"
    assert plan["reuse"] == []
    assert plan["reuse_images"] is False


def test_carried_items_keep_their_ids_and_their_pictures(grammar_blueprint):
    blueprint = blueprint_of(grammar_blueprint)
    baseline = {"material": {"items": [
        {"id": "m1", "blueprint_slot_id": "s1",
         "images": [{"url": "https://x/1.png", "provider": "generated"}]},
        {"id": "m5", "blueprint_slot_id": "s5", "images": []},
    ]}}
    plan = {"regenerate": ["s5"], "reasons": {"s5": ["needs easier practice"]}}
    applied = cache.apply_plan(baseline, plan)

    kept = [i["id"] for i in applied["carried_items"]]
    assert kept == ["m1"], "only the regenerated slot is dropped"
    assert applied["carried_items"][0]["images"][0]["url"] == "https://x/1.png"
    assert applied["instructions"][0]["target"] == "s5"
    assert applied["instructions"][0]["instructions"] == ["needs easier practice"]


def test_the_baseline_is_not_mutated_by_personalising_it(grammar_blueprint):
    baseline = {"material": {"items": [{"id": "m1", "blueprint_slot_id": "s1"},
                                       {"id": "m2", "blueprint_slot_id": "s2"}]}}
    cache.apply_plan(baseline, {"regenerate": ["s2"], "reasons": {}})
    assert len(baseline["material"]["items"]) == 2, \
        "the shared baseline must survive being personalised for one student"


# ---- the read path: what happens when a student presses "Start now" --------

def _store_baseline(grammar_blueprint):
    blueprint = grammar_blueprint.model_dump()
    material = {"items": [
        {"id": f"m{n}", "blueprint_slot_id": s["slot_id"], "stage": s["stage"],
         "images": [{"url": f"https://x/{n}.png", "provider": "generated"}]
                   if s.get("visual") else []}
        for n, s in enumerate(blueprint["slots"], 1)]}
    cache.store(cache.baseline_key("german", "a1-1.classroom.l3", "A1"),
                blueprint, material, {"activities": []}, {"objectives": []})
    return blueprint


def test_a_student_with_nothing_diagnosed_is_served_the_baseline(grammar_blueprint):
    from zanoba_agent.workflows import serving

    _store_baseline(grammar_blueprint)
    result = serving.prepare_for_student(
        "german", "a1-1.classroom.l3", "A1", "stu-1",
        {"readiness": "ready", "recommended_difficulty": "at"})
    assert result["status"] == "baseline_hit"
    assert result["work_required"] is None
    assert result["lesson"]["material"]["items"], "a lesson must come back"


def test_a_diagnosed_gap_asks_for_two_slots_not_a_lesson(grammar_blueprint):
    from zanoba_agent.workflows import serving

    _store_baseline(grammar_blueprint)
    result = serving.prepare_for_student(
        "german", "a1-1.classroom.l3", "A1", "stu-1",
        {"readiness": "ready_with_review", "review_first": ["a1-1.classroom.l1"]})
    assert result["status"] == "personalise"
    # Something is servable immediately; the small rewrite runs behind it.
    assert result["lesson"] is not None
    assert result["savings"]["slots_reused"] > result["savings"]["slots_regenerated"]
    assert result["savings"]["images_remade"] == 0

    # The work is expressed in exactly the form the Material agent already
    # understands, so targeted personalisation and targeted repair are one
    # mechanism rather than two.
    import json

    request = json.loads(result["work_required"]["regeneration_request"])
    assert request["targets"][0]["scope"] == "item"
    assert request["targets"][0]["reasons"]


def test_an_uncached_lesson_is_a_miss_not_a_wait(grammar_blueprint):
    from zanoba_agent.workflows import serving

    result = serving.prepare_for_student("german", "not.cached", "A1", "stu-1", {})
    assert result["status"] == "miss"
    assert result["work_required"]["scope"] == "build"
    assert result["elapsed_ms"] < 100, "a miss must return immediately, not build"


def test_serving_never_blocks_on_generation(grammar_blueprint):
    # Every path returns in milliseconds. Work that is needed is described, not
    # performed, so the caller decides whether to run it now or in the
    # background — a student pressing "Start now" always gets something.
    from zanoba_agent.workflows import serving

    _store_baseline(grammar_blueprint)
    for diagnosis in ({"readiness": "ready"},
                      {"readiness": "ready_with_review", "review_first": ["x"]},
                      {"readiness": "not_ready"},
                      {}):
        result = serving.prepare_for_student(
            "german", "a1-1.classroom.l3", "A1", "stu-1", diagnosis)
        assert result["elapsed_ms"] < 100, diagnosis


def test_a_personalised_lesson_is_reused_until_the_student_moves(grammar_blueprint):
    from zanoba_agent.workflows import serving

    blueprint = _store_baseline(grammar_blueprint)
    diagnosis = {"readiness": "ready_with_review", "review_first": ["a1-1.classroom.l1"]}
    serving.store_personalised(
        "german", "a1-1.classroom.l3", "A1", "stu-1", diagnosis, None,
        blueprint, {"items": [{"id": "personalised"}]}, {}, {})

    again = serving.prepare_for_student(
        "german", "a1-1.classroom.l3", "A1", "stu-1", diagnosis)
    assert again["status"] == "personalised_hit"
    assert again["lesson"]["material"]["items"][0]["id"] == "personalised"

    # Once they have closed the gap, the compensating version is not served.
    moved_on = serving.prepare_for_student(
        "german", "a1-1.classroom.l3", "A1", "stu-1", {"readiness": "ready"})
    assert moved_on["status"] == "baseline_hit"
