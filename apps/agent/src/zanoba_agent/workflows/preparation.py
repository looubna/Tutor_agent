"""The preparation pipeline — the container box at the top of the diagram.

Three agents in a fixed order:

    START -> curriculum_agent -> diagnostic_agent -> objective_agent
                                                        |
                                              route_by_domain
                                               /            \\
                              language_lesson_planner   stem_lesson_planner
                                        |                       |
                              material_planner_agent            |
                                        |                       |
                              language_material_agent   stem_material_agent
                                        \\                     /
                                         quality_checker_agent
                                                  |
                                            quality_gate
                                          (targeted revision)

The first three stages are sequential because each one needs the answer before it, and for no other
reason. The Curriculum agent must name a target lesson before the Diagnostic
agent can judge readiness *for that lesson*; the Objective agent needs both
answers before it can decide what fits the hour. Running them in parallel would
not be faster, it would be wrong.

Data moves between them through session state, not through the prompt. Each
agent declares an `output_key`, ADK writes its structured output there, and the
next agent's instruction reads it back with `{that_key}`. A missing key raises
rather than quietly producing an answer from nothing — which is the failure
mode worth having, because an Objective agent inventing objectives with no
placement to work from would look perfectly plausible.
"""

from __future__ import annotations

from google.adk.workflow import START, Workflow

from ..agents.curriculum_agent import curriculum_agent
from ..agents.diagnostic_agent import diagnostic_agent
from ..agents.language_material import language_material_agent
from ..agents.language_planner import language_lesson_planner
from ..agents.material_planner import material_planner_agent
from ..agents.objective_agent import objective_agent
from ..agents.quality_checker import quality_checker_agent
from ..agents.stem_material import stem_material_agent
from ..agents.stem_planner import stem_lesson_planner
from .routing import (
    LANGUAGE_ROUTE,
    PASS_ROUTE,
    REVISE_LANGUAGE_ROUTE,
    REVISE_STEM_ROUTE,
    STEM_ROUTE,
    quality_gate,
    route_by_domain,
)

# The state keys each stage writes. Named here so a reader can see the contract
# of the pipeline without opening three agent modules.
PLACEMENT_KEY = "curriculum_placement"
DIAGNOSIS_KEY = "diagnostic_report"
OBJECTIVES_KEY = "lesson_objectives"
PLAN_KEY = "lesson_plan"
BLUEPRINT_KEY = "material_blueprint"
MATERIAL_KEY = "material_package"
QUALITY_KEY = "quality_report"

preparation_workflow = Workflow(
    name="preparation_pipeline",
    description=(
        "Decides what to teach one student in one 60-minute lesson: what the "
        "syllabus says next, what they actually know, and which objectives fit."
    ),
    edges=[
        (START, curriculum_agent, diagnostic_agent, objective_agent, route_by_domain),
        (route_by_domain, {LANGUAGE_ROUTE: language_lesson_planner,
                           STEM_ROUTE: stem_lesson_planner}),
        # The language branch plans its material before writing it. The blueprint
        # is what the generator writes against and what the checker grades
        # against, so both are working from the same document for the first time.
        (language_lesson_planner, material_planner_agent,
         language_material_agent, quality_checker_agent),
        (stem_lesson_planner, stem_material_agent, quality_checker_agent),
        (quality_checker_agent, quality_gate),
        # The loop. PASS has no outgoing edge, so the graph ends there.
        (quality_gate, {REVISE_LANGUAGE_ROUTE: language_material_agent,
                        REVISE_STEM_ROUTE: stem_material_agent}),
    ],
)
