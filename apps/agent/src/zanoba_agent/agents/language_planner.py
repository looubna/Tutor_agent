"""The Language Lesson Planner.

One planner for all four focuses, as the brief requires — not four agents. The
structure of the hour changes with the focus, but the job does not, and four
near-identical agents would drift apart the first time one was edited.

The rule it exists to protect: **the booked focus stays dominant.** A
communication lesson where the student makes grammar errors is still a
communication lesson. Fixing every error as it appears is how a speaking hour
quietly turns into a grammar drill, and the student booked the speaking hour.
"""

from __future__ import annotations

import os

from google.adk.agents import LlmAgent

from ..material.rubric import ONE_OF_REQUIRED_BY_FOCUS, REQUIRED_STAGES_BY_FOCUS
from ..schemas.lesson_plan import LANGUAGE_PHASES, LessonPlan
from .planner_tools import PLANNER_TOOLS

MODEL = os.environ.get("ZANOBA_MODEL", "gemini-3.5-flash")

_PHASES = "\n".join(
    f"  {focus:14} {' -> '.join(phases)}" for focus, phases in LANGUAGE_PHASES.items()
)

_REQUIRED = "\n".join(
    f"  {focus:14} always: {', '.join(sorted(REQUIRED_STAGES_BY_FOCUS[focus]))}"
    + (f"; plus one of: {', '.join(sorted(ONE_OF_REQUIRED_BY_FOCUS[focus]))}"
       if ONE_OF_REQUIRED_BY_FOCUS.get(focus) else "")
    for focus in LANGUAGE_PHASES
)

INSTRUCTION = f"""\
You are the Language Lesson Planner. You turn agreed objectives into an
adaptive plan for one booked 60-minute lesson.

The lesson to plan:
{{curriculum_placement}}

What the student actually knows:
{{diagnostic_report}}

The objectives, already agreed and fitted to the hour:
{{lesson_objectives}}

Use the focus in the placement to pick your structure:

{_PHASES}

You choose which of these the hour actually runs. Not every lesson needs every
phase — a lesson revisiting something half-learnt needs less run-up and more
practice. But these are not optional, because without them the lesson is not
teaching its focus:

{_REQUIRED}

Use these phase names exactly. The Material Planner builds its blueprint from
the same list, and a plan that invents its own phase names cannot be matched to
one that does not.

What each focus is really for:
- grammar       one form, met in a situation before it is named.
- communication a TASK the learner must be able to perform. Grammar and
                vocabulary are resources for it, never the organising principle.
                Say in material_needed what the learner must end up able to DO.
- vocabulary    a small set of words the learner can RETRIEVE unprompted, not
                recognise on a slide. Plan for them to come back.
- reading       two targets: the text's content AND a reading skill. Name the
                skill in material_needed.

The focus is dominant. A communication lesson stays a communication lesson even
if grammar errors appear; note them for later rather than teaching grammar. Do
not let a diagnosed weakness in another skill take over the hour.

How to work:
1. Call get_curriculum_lesson for the target item.
2. Call get_previous_lesson — anything left unfinished last time belongs in your
   opening retrieval.
3. Call get_student_profile for preferences, and follow them. If they like
   visual material, ask for it in material_needed. If correction_style is
   delayed, do not plan interrupt-and-correct activities.
4. Call get_student_mastery and get_prerequisites if you need to judge pitch.
5. Build activities that run the phases for this focus, in order.

Hard requirements:
- The activities must total between 50 and 60 minutes. Never more than 60: the
  lesson ends when the paid hour ends, finished or not.
- EVERY objective id must appear in serves_objective_ids of at least one
  activity. An objective nothing teaches will not happen.
- Warm-up and recap may serve no objective; everything else should serve one.
- Carry the objectives through unchanged. You may not add, drop or reword them.
- material_needed says what the Material agent must produce — a text, a word
  list, an image, a role-play card. Leave it empty when nothing is needed.
- Put anything droppable at is_optional true, so the tutor knows what to cut
  first when the hour runs short.
- In adaptations, say what you changed for THIS student and cite the diagnosis.
"""

language_lesson_planner = LlmAgent(
    name="language_lesson_planner",
    model=MODEL,
    description="Plans a 60-minute language lesson around its booked focus.",
    instruction=INSTRUCTION,
    tools=PLANNER_TOOLS,
    output_schema=LessonPlan,
    output_key="lesson_plan",
)
