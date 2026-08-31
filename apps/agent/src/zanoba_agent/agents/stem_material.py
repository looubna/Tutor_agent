"""The STEM Material agent.

Writes explanations, worked examples, exercises, diagrams and answer keys.

The difference from the language side is not tone, it is truth conditions. A
clumsy German sentence is poor material; a wrong answer key is material that
teaches the student something false and then marks them wrong for disagreeing.
So this agent is required to put every arithmetic answer through
`verify_calculation`, which computes it in Python rather than asking a model to
check its own work.
"""

from __future__ import annotations

import os

from google.adk.agents import LlmAgent

from ..schemas.material import MaterialPackage
from .material_tools import get_stem_resources, solve_problem, verify_calculation

MODEL = os.environ.get("ZANOBA_MODEL", "gemini-3.5-flash")


def generate_problem(objective: str, count: int = 5, difficulty: str = "at") -> dict:
    """Return the shape a problem set should take for one objective.

    Args:
      objective: The objective the problems must measure.
      count: How many problems.
      difficulty: "below", "at" or "above" the curriculum default.

    Returns:
      A specification to write against. Write the problems yourself, then verify
      every answer with verify_calculation before putting it in the answer key.
    """
    return {"objective": objective, "count": max(1, min(count, 20)),
            "difficulty": difficulty,
            "requirement": "Each problem must measure the objective. Put the "
                           "arithmetic in the exercise's expression field so it "
                           "can be checked."}


def generate_examples(point: str, count: int = 2) -> dict:
    """Return the shape a set of worked examples should take.

    Args:
      point: The method being taught.
      count: How many worked examples.

    Returns:
      A specification. A worked example shows every step; a stated answer is not
      a worked example.
    """
    return {"point": point, "count": max(1, min(count, 6)),
            "requirement": "Show every step. The student must be able to follow "
                           "the method, not just see the result."}


INSTRUCTION = """\
You are the STEM Material agent. You write the material for one 60-minute
lesson, following a plan that has already been agreed.

The plan:
{lesson_plan}

What the student knows:
{diagnostic_report}

Produce one material item for EVERY activity in the plan whose material_needed
is not empty. Set activity_id on each item to the activity it serves.

How to work:
1. Call get_stem_resources for the lesson's own outcomes.
2. Call generate_examples and generate_problem for their specifications, then
   write the actual content yourself.
3. Use solve_problem to compute answers rather than calculating them yourself.
4. Call verify_calculation on EVERY arithmetic answer before it goes in an
   answer key. Put the result in the exercise's verification field.

This is not optional. You are not permitted to check your own arithmetic by
reading it again — you must run it through verify_calculation. If a verdict
comes back "incorrect", fix the answer and verify again. If it comes back
"unverifiable", say so in notes; unverifiable does not mean correct.

Rules:
- Every exercise whose answer is arithmetic must carry a machine-checkable
  expression, e.g. "3/4 + 1/6". Without it nothing can verify the answer.
- Worked examples show every step, not just the result.
- Answers go in answer_key and in the exercise's answer field, never inside
  content.
- Units matter. A number without its unit is a wrong answer in physics and a
  half answer in maths.
- Serve the plan's objectives. Do not add teaching the plan did not ask for.
"""

stem_material_agent = LlmAgent(
    name="stem_material_agent",
    model=MODEL,
    description="Writes explanations, worked examples and independently verified exercises.",
    instruction=INSTRUCTION,
    tools=[get_stem_resources, generate_problem, generate_examples,
           solve_problem, verify_calculation],
    output_schema=MaterialPackage,
    output_key="material_package",
)
