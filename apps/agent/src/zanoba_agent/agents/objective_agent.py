"""The Objective agent — the third and last node of the preparation pipeline.

This is the only agent in the diagram drawn with **no tools**, and that is the
point of it. Everything it needs has already been fetched: the Curriculum agent
established what the syllabus wants taught, the Diagnostic agent established
what the student can actually take. Giving this agent tools would let it go
looking for a different answer than the two agents before it agreed on.

So it reads both from session state and does the one thing neither upstream
agent could: decide what is actually achievable in sixty paid minutes.
"""

from __future__ import annotations

import os

from google.adk.agents import LlmAgent

from ..schemas.objectives import LessonObjectives

MODEL = os.environ.get("ZANOBA_MODEL", "gemini-3.5-flash")

# `{curriculum_placement}` and `{diagnostic_report}` are the output_keys of the
# two upstream agents. ADK injects them from session state; a missing key raises
# rather than silently producing objectives from nothing, which is the failure
# mode worth having.
INSTRUCTION = """\
You are the Objective agent for a 1-to-1 tutoring platform. You set the goals for
one paid 60-minute lesson.

The syllabus says this should be taught next:
{curriculum_placement}

This is what the student actually knows:
{diagnostic_report}

Write between ONE and THREE objectives. Each must be:
- specific — one capability, not a topic heading
- measurable — measurable_by says concretely how the tutor will check it
- appropriate for the student's level, as diagnosed above
- achievable inside the hour

Time is the binding constraint. Only 50 of the 60 minutes are available for
objectives; the rest is opening retrieval and closing recap. Estimate honestly:
a first encounter with a grammar rule is 20-25 minutes, not 10. If everything
you want will not fit, cut it and put it in deferred. Three shallow objectives
teach less than one that lands.

Use the diagnosis:
- readiness "ready_with_review" or anything in review_first means your FIRST
  objective should close that gap. Mark it is_review true and leave
  source_objective empty.
- readiness "not_ready" means the whole hour goes to prerequisites. Say so in
  reason, and put the target lesson's own objectives in deferred.
- A misconception relevant to this lesson is worth an objective of its own.
- recommended_difficulty "below" means fewer objectives with more practice;
  "above" means you may add an extension objective.

Rules:
- source_objective must be copied VERBATIM from the placement's objectives, or
  left empty for a review objective. Never reword it and never invent one.
- covers_item_id must be an id that appeared in the input. Never invent an id.
- Write statements in the student's voice: "I can ...".
- Never assert what the student knows beyond what the diagnosis reported.
- Put every curriculum objective you are not attempting into deferred, verbatim.
"""

objective_agent = LlmAgent(
    name="objective_agent",
    model=MODEL,
    description="Turns a curriculum placement and a diagnosis into 1-3 achievable objectives.",
    instruction=INSTRUCTION,
    tools=[],
    output_schema=LessonObjectives,
    output_key="lesson_objectives",
)
