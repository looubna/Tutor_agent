"""Material verification and the bounded quality loop."""

from __future__ import annotations

import json
from types import SimpleNamespace

import pytest
from pydantic import ValidationError

from zanoba_agent.agents.language_material import language_material_agent
from zanoba_agent.agents.quality_checker import (
    check_material_coverage, quality_checker_agent)
from zanoba_agent.agents.stem_material import stem_material_agent
from zanoba_agent.material.arithmetic import CannotVerify, check, evaluate
from zanoba_agent.schemas.material import MaterialItem, MaterialPackage
from zanoba_agent.workflows.preparation import preparation_workflow
from zanoba_agent.workflows.routing import (
    MAX_QUALITY_ATTEMPTS, PASS_ROUTE, REVISE_LANGUAGE_ROUTE, quality_gate)


# ---- independent arithmetic ------------------------------------------------

def test_exact_fractions_not_floats():
    # 0.1 + 0.2 != 0.3 in binary floating point. In exact arithmetic it does.
    assert check("0.1 + 0.2", "0.3")["verdict"] == "correct"
    assert check("1/3 + 1/3 + 1/3", "1")["verdict"] == "correct"


def test_a_wrong_answer_is_caught():
    r = check("3/4 + 1/6", "4/10")
    assert r["verdict"] == "incorrect"
    assert r["computed"] == "11/12"


def test_unverifiable_is_never_reported_as_correct():
    for expr in ("solve for x", "12 / 0", "__import__('os')"):
        assert check(expr, "1")["verdict"] == "unverifiable"


def test_the_checker_refuses_code_rather_than_running_it():
    with pytest.raises(CannotVerify):
        evaluate("__import__('os').system('echo hi')")
    with pytest.raises(CannotVerify):
        evaluate("open('/etc/passwd').read()")


def test_huge_exponents_are_refused_not_computed():
    with pytest.raises(CannotVerify):
        evaluate("9**99999")


# ---- coverage --------------------------------------------------------------

def test_uncovered_activities_are_found_by_id_not_by_reading():
    plan = json.dumps({"activities": [
        {"id": "a1", "material_needed": "text"},
        {"id": "a2", "material_needed": ""},
        {"id": "a3", "material_needed": "exercises"}]})
    pkg = json.dumps({"items": [{"activity_id": "a1"}, {"activity_id": "a9"}]})
    result = check_material_coverage(plan, pkg)
    assert result["uncovered"] == ["a3"]
    assert result["orphaned_items"] == ["a9"]
    assert result["complete"] is False


def test_full_coverage_passes():
    plan = json.dumps({"activities": [{"id": "a1", "material_needed": "text"}]})
    pkg = json.dumps({"items": [{"activity_id": "a1"}]})
    assert check_material_coverage(plan, pkg)["complete"] is True


# ---- the loop --------------------------------------------------------------

def _ctx(state=None):
    return SimpleNamespace(state=state if state is not None else {})


def _fail_report(action="regenerate_material", severity="high"):
    return {"status": "fail", "issues": [
        {"component": "material", "problem": "wrong answer",
         "action": action, "severity": severity, "item_id": "m1"}]}


def test_a_passing_report_ends_the_loop():
    ev = quality_gate(_ctx(), {"status": "pass", "issues": []})
    assert ev.actions.route == PASS_ROUTE


def test_a_blocking_failure_sends_material_back():
    ctx = _ctx({"curriculum_placement": json.dumps({"domain": "language"})})
    ev = quality_gate(ctx, _fail_report())
    assert ev.actions.route == REVISE_LANGUAGE_ROUTE


def test_low_severity_notes_do_not_loop():
    ev = quality_gate(_ctx(), _fail_report(severity="low"))
    assert ev.actions.route == PASS_ROUTE


def test_a_plan_issue_does_not_loop_the_material():
    # The diagram loops Quality back to Material and nowhere else. A plan issue
    # is reported for a human, not routed.
    ev = quality_gate(_ctx(), _fail_report(action="revise_plan"))
    assert ev.actions.route == PASS_ROUTE


def test_the_loop_is_bounded():
    ctx = _ctx({"curriculum_placement": json.dumps({"domain": "language"})})
    routes = [quality_gate(ctx, _fail_report()).actions.route
              for _ in range(MAX_QUALITY_ATTEMPTS + 2)]
    assert routes[0] == REVISE_LANGUAGE_ROUTE
    assert routes[-1] == PASS_ROUTE, "an unbounded loop would keep revising"
    assert ctx.state["quality_attempts"] == MAX_QUALITY_ATTEMPTS + 2


def test_giving_up_is_recorded_not_disguised_as_success():
    ctx = _ctx({"quality_attempts": MAX_QUALITY_ATTEMPTS - 1,
                "curriculum_placement": json.dumps({"domain": "stem"})})
    ev = quality_gate(ctx, _fail_report())
    assert ev.actions.route == PASS_ROUTE
    assert ctx.state["quality_attempts"] == MAX_QUALITY_ATTEMPTS


# ---- graph shape -----------------------------------------------------------

def test_the_graph_contains_the_revision_cycle():
    edges = [(e.from_node.name, e.to_node.name) for e in preparation_workflow.graph.edges]
    assert ("language_material_agent", "quality_checker_agent") in edges
    assert ("stem_material_agent", "quality_checker_agent") in edges
    assert ("quality_gate", "language_material_agent") in edges
    assert ("quality_gate", "stem_material_agent") in edges


def test_pass_has_no_outgoing_edge_so_the_graph_terminates():
    routes = {e.route for e in preparation_workflow.graph.edges if e.route}
    assert PASS_ROUTE not in routes


def test_both_material_agents_write_one_key():
    assert (language_material_agent.output_key
            == stem_material_agent.output_key == "material_package")


def test_the_checker_cannot_rewrite_material():
    # It reports; something else repairs. A checker that fixes what it finds is
    # a second author with nobody checking it.
    names = {t.__name__ for t in quality_checker_agent.tools}
    assert names == {"validate_material", "check_target_language",
                     "verify_reading_evidence", "check_deck_format",
                     "check_material_coverage", "verify_calculation",
                     "get_cefr_guidelines"}
    # Every tool reads or measures. None of them writes material.
    assert not any(n.startswith(("write", "generate", "fix", "revise")) for n in names)


def test_the_material_agent_writes_against_a_blueprint_it_did_not_choose():
    # The architectural change: deciding what material the lesson needs and
    # writing it are two jobs now. The generator reads the blueprint and has no
    # tool that would let it plan a different one.
    instruction = language_material_agent.instruction
    assert "{material_blueprint}" in instruction
    assert "You do not decide what" in instruction
    names = {t.__name__ for t in language_material_agent.tools}
    assert "check_target_language" in names, "it must be able to verify its own German"


def test_the_planner_specifies_and_cannot_write():
    from zanoba_agent.agents.material_planner import material_planner_agent

    names = {t.__name__ for t in material_planner_agent.tools}
    assert not any(n.startswith(("write", "compose", "generate")) for n in names)
    assert material_planner_agent.output_key == "material_blueprint"


def test_material_ids_must_be_unique():
    item = lambda i: MaterialItem(id=i, activity_id="a1", kind="text", title="t", content="c")
    with pytest.raises(ValidationError, match="duplicate material ids"):
        MaterialPackage(student_id="s", subject="german", domain="language",
                        target_item_id="x", items=[item("m1"), item("m1")])


# ---- targeted regeneration through the gate --------------------------------

def _report_with_targets(targets, status="FAIL"):
    return {
        "status": status,
        "issues": [{"component": "material", "problem": "bad", "severity": "critical",
                    "action": "regenerate_material", "scope": t["scope"],
                    "item_id": t["target"]} for t in targets],
        "regeneration_targets": targets,
    }


def test_the_gate_hands_the_generator_a_repair_brief():
    # The point of targeted regeneration: the generator is told which items to
    # rewrite, so it carries the rest through instead of re-improvising the
    # lesson and losing everything that was right.
    from zanoba_agent.workflows.routing import REGENERATION_KEY

    ctx = _ctx({"curriculum_placement": json.dumps({"domain": "language"})})
    quality_gate(ctx, _report_with_targets([
        {"target": "m3#img0", "scope": "image", "reasons": ["ambiguous"],
         "instructions": ["exclude the house and the bench"]}]))

    brief = json.loads(ctx.state[REGENERATION_KEY])
    assert brief["targets"][0]["target"] == "m3#img0"
    assert brief["targets"][0]["scope"] == "image"
    assert "exclude the house" in brief["targets"][0]["instructions"][0]


def test_the_repair_brief_is_ordered_narrowest_first():
    ctx = _ctx({"curriculum_placement": json.dumps({"domain": "language"})})
    quality_gate(ctx, _report_with_targets([
        {"target": "*", "scope": "lesson", "reasons": ["weak"], "instructions": ["redo"]},
        {"target": "m2", "scope": "item", "reasons": ["flat"], "instructions": ["rewrite"]},
        {"target": "m3#img0", "scope": "image", "reasons": ["bad"], "instructions": ["redo"]},
    ]))
    from zanoba_agent.workflows.routing import REGENERATION_KEY

    scopes = [t["scope"] for t in json.loads(ctx.state[REGENERATION_KEY])["targets"]]
    assert scopes == ["image", "item", "lesson"]


def test_targets_are_derived_when_the_checker_did_not_supply_them():
    # A checker that reports problems without filling in targets still gets a
    # targeted repair rather than a whole-lesson one.
    ctx = _ctx({"curriculum_placement": json.dumps({"domain": "language"})})
    quality_gate(ctx, {"status": "FAIL", "issues": [
        {"component": "material", "problem": "no answer", "severity": "critical",
         "action": "regenerate_material", "scope": "item", "item_id": "m4",
         "fix": "supply the answer"}]})
    from zanoba_agent.workflows.routing import REGENERATION_KEY

    targets = json.loads(ctx.state[REGENERATION_KEY])["targets"]
    assert targets[0]["target"] == "m4"
    assert targets[0]["instructions"] == ["supply the answer"]


def test_a_pass_clears_the_repair_brief():
    # A stale brief would make the next lesson's first pass believe it was a
    # revision of something.
    from zanoba_agent.workflows.routing import REGENERATION_KEY

    ctx = _ctx({REGENERATION_KEY: '{"targets": [{"target": "m1"}]}'})
    quality_gate(ctx, {"status": "PASS", "issues": []})
    assert ctx.state[REGENERATION_KEY] == ""


def test_a_critical_issue_loops_even_when_status_says_pass():
    # The status is written by a model; the issues are counted. A report that
    # says "pass" while carrying a critical failure must not be taken at its word.
    ctx = _ctx({"curriculum_placement": json.dumps({"domain": "language"})})
    ev = quality_gate(ctx, {"status": "FAIL", "issues": [
        {"component": "material", "problem": "English on a German slide",
         "severity": "critical", "action": "regenerate_material",
         "scope": "item", "item_id": "m1"}]})
    assert ev.actions.route == REVISE_LANGUAGE_ROUTE


def test_only_the_named_images_are_remade():
    # A lesson with one bad photograph should cost one photograph.
    from zanoba_agent.material import images

    calls = []

    def fake_generate(**kw):
        calls.append(kw)
        return {"prompt": kw["prompt"], "alt_text": kw["alt_text"],
                "purpose": kw["purpose"], "provider": "generated",
                "url": "https://x/new.png"}

    original, images.generate = images.generate, fake_generate
    try:
        package = {"items": [
            {"id": "m1", "images": [{"prompt": "a", "alt_text": "a", "purpose": "p",
                                     "provider": "generated", "url": "https://x/1.png"}]},
            {"id": "m2", "images": [{"prompt": "b", "alt_text": "b", "purpose": "p",
                                     "provider": "generated", "url": "https://x/2.png"}]},
        ]}
        result = images.regenerate(package, [
            {"target": "m2#img0", "scope": "image", "reasons": ["contains a house"]}])
    finally:
        images.generate = original

    assert result["regenerated"] == 1
    assert len(calls) == 1
    # The rejection reason reaches the next prompt, so the second attempt is a
    # different request. Asking again for the same thing returns the same thing.
    assert calls[0]["avoid"] == ["contains a house"]
    assert package["items"][0]["images"][0]["url"] == "https://x/1.png", "untouched"
    assert package["items"][1]["images"][0]["url"] == "https://x/new.png"
    assert package["items"][1]["images"][0]["attempts"] == 1
