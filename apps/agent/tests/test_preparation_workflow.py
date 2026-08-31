"""The preparation pipeline's shape.

Structural tests, no model calls. The graph either wires the three agents in
the order the diagram draws, or it does not — that is checkable for free, and
worth checking because a mis-wired edge produces plausible output rather than
an error.
"""

from __future__ import annotations

from zanoba_agent.workflows.preparation import (
    BLUEPRINT_KEY,
    DIAGNOSIS_KEY,
    OBJECTIVES_KEY,
    PLACEMENT_KEY,
    preparation_workflow,
)


def _edges() -> list[tuple[str, str]]:
    return [(e.from_node.name, e.to_node.name) for e in preparation_workflow.graph.edges]


def test_the_pipeline_is_the_shape_the_diagram_draws():
    assert _edges() == [
        ("__START__", "curriculum_agent"),
        ("curriculum_agent", "diagnostic_agent"),
        ("diagnostic_agent", "objective_agent"),
        ("objective_agent", "route_by_domain"),
        ("route_by_domain", "language_lesson_planner"),
        ("route_by_domain", "stem_lesson_planner"),
        # The language branch specifies its material before writing it.
        ("language_lesson_planner", "material_planner_agent"),
        ("material_planner_agent", "language_material_agent"),
        ("language_material_agent", "quality_checker_agent"),
        ("stem_lesson_planner", "stem_material_agent"),
        ("stem_material_agent", "quality_checker_agent"),
        ("quality_checker_agent", "quality_gate"),
        ("quality_gate", "language_material_agent"),
        ("quality_gate", "stem_material_agent"),
    ]


def test_the_preparation_stages_are_sequential():
    # Everything up to the diamond runs in a line, because each stage needs the
    # answer before it. Only the two gates branch, and they branch to
    # alternatives, not to work done in parallel.
    from collections import Counter

    fan_out = Counter(src for src, _ in _edges())
    assert fan_out["route_by_domain"] == 2
    assert fan_out["quality_gate"] == 2
    linear = {k: v for k, v in fan_out.items() if k not in {"route_by_domain", "quality_gate"}}
    assert all(n == 1 for n in linear.values())


def test_both_branches_meet_at_one_checker():
    # One Quality checker for both domains, as the diagram draws it.
    into_checker = {src for src, dst in _edges() if dst == "quality_checker_agent"}
    assert into_checker == {"language_material_agent", "stem_material_agent"}


def test_every_agent_is_reachable_from_start():
    edges = _edges()
    reached, frontier = {"__START__"}, ["__START__"]
    while frontier:
        node = frontier.pop()
        for src, dst in edges:
            if src == node and dst not in reached:
                reached.add(dst)
                frontier.append(dst)
    assert reached == {
        "__START__", "curriculum_agent", "diagnostic_agent", "objective_agent",
        "route_by_domain", "language_lesson_planner", "stem_lesson_planner",
        "material_planner_agent", "language_material_agent", "stem_material_agent",
        "quality_checker_agent", "quality_gate",
    }


def test_each_stage_writes_the_key_the_next_stage_reads():
    by_name = {n.name: n for n in preparation_workflow.graph.nodes}
    assert by_name["curriculum_agent"].output_key == PLACEMENT_KEY
    assert by_name["diagnostic_agent"].output_key == DIAGNOSIS_KEY
    assert by_name["objective_agent"].output_key == OBJECTIVES_KEY
    assert by_name["material_planner_agent"].output_key == BLUEPRINT_KEY

    # The blueprint is only worth producing if the two stages downstream of it
    # actually read it: the generator writes against it, the checker grades
    # against it. When nothing read it, it was documentation.
    assert f"{{{BLUEPRINT_KEY}}}" in by_name["language_material_agent"].instruction
    assert BLUEPRINT_KEY in by_name["quality_checker_agent"].instruction

    # The contract only holds if the downstream instructions actually read them.
    assert f"{{{PLACEMENT_KEY}}}" in by_name["diagnostic_agent"].instruction
    assert f"{{{PLACEMENT_KEY}}}" in by_name["objective_agent"].instruction
    assert f"{{{DIAGNOSIS_KEY}}}" in by_name["objective_agent"].instruction


def test_every_agent_returns_structured_output():
    # The router is exempt: it is a plain function node that emits a route, not
    # an agent producing a document.
    exempt = {"__START__", "route_by_domain", "quality_gate"}
    for node in preparation_workflow.graph.nodes:
        if node.name in exempt:
            continue
        assert node.output_schema is not None, f"{node.name} returns unstructured text"


def test_the_router_is_not_an_agent():
    # Choosing a branch is a file lookup, not a judgement. Making it an agent
    # would add a model call whose only new capability is being wrong.
    for name in ("route_by_domain", "quality_gate"):
        node = next(n for n in preparation_workflow.graph.nodes if n.name == name)
        assert getattr(node, "model", None) is None
        assert not getattr(node, "tools", [])


def test_nodes_are_inferred_from_edges_not_listed_twice():
    names = [n.name for n in preparation_workflow.graph.nodes]
    assert len(names) == len(set(names))


def test_the_placement_carries_the_student_forward():
    # Downstream nodes receive the placement and nothing else. Without a
    # student_id on it, the Diagnostic agent looked up an empty student and
    # reported a beginner with no evidence — on real data that had plenty.
    from zanoba_agent.schemas.placement import CurriculumPlacement

    assert "student_id" in CurriculumPlacement.model_fields
    assert CurriculumPlacement.model_fields["student_id"].is_required()
