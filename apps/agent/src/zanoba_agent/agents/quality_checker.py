"""The Material Checker — decides whether a prepared lesson is fit to teach.

One agent for every focus and both domains, as the diagram draws it. The checks
differ by focus but the job does not: read the blueprint, the objectives and the
material together, and say whether this lesson is fit to teach and exactly what
should be redone.

What changed is the standard. The old checker asked a model whether the material
was good, and a model asked that about material a model wrote says yes — it said
yes to a German lesson written entirely in English. So everything countable is
now counted in Python before the model sees it, and the model is left only the
questions that genuinely need reading:

  Would a native speaker actually say this?
  Does this dialogue have a reason to happen?
  Could the learner finish this task while avoiding the target language?
  Is this distractor plausible, or obviously wrong?
  Does this picture read as the thing it is supposed to be?

Those are real questions and a model is the right tool for them. "Does this have
images", "is this answer among the options", "does this quote appear in the
text", "is this German" are not, and asking a model was how they got answered
wrongly.

What it must not do is regenerate anything. It reports issues with a scope and a
target attached, and something else acts. A checker that fixes what it finds is a
second author, and there is then nobody checking that.
"""

from __future__ import annotations

import json
import os
from typing import Any

from google.adk.agents import LlmAgent

from ..material.deck_spec import check_deck as _check_deck
from ..material.language_purity import check_package as _check_language
from ..material.validation import check_reading_evidence, validate_package
from ..schemas.quality import QualityReport
from .material_tools import get_cefr_guidelines, verify_calculation


def _load(raw: Any) -> dict:
    if isinstance(raw, dict):
        return raw
    try:
        return json.loads(raw)
    except (TypeError, ValueError):
        return {}


def validate_material(material_package: str, material_blueprint: str = "",
                      lesson_objectives: str = "") -> dict:
    """Run every structural check on the material and return one report.

    Args:
      material_package: The material package, as JSON.
      material_blueprint: The blueprint it was written against, as JSON.
      lesson_objectives: The lesson objectives, as JSON.

    Returns:
      A structured report: a status, an overall score, a score per dimension,
      every issue with its scope and target, the critical ones separately, and
      what to regenerate.

      Everything here is counted, not judged. Missing fields, an answer that is
      not among its own options, a slot specified and never filled, an image
      promised and never produced, a duplicate exercise, a stage out of order, a
      progression that skips two rungs, English on a target-language slide, a
      comprehension answer whose quote is not in the text, vocabulary selected
      and never used. These are the failures that read perfectly well in prose
      review and are caught for free by comparing ids and counting words.

      Your judgement is what this cannot do. Use it for naturalness, authenticity
      and whether a task actually requires the target language.
    """
    package = _load(material_package)
    if not package:
        return {"error": "material package is not readable JSON"}
    return validate_package(
        package,
        blueprint=_load(material_blueprint) or None,
        objectives=_load(lesson_objectives) or None,
    )


def verify_reading_evidence(material_package: str) -> dict:
    """Check every comprehension answer is supported by words in the text.

    Args:
      material_package: The material package, as JSON.

    Returns:
      Which questions cite evidence that really appears in the text and which do
      not. This is reading's equivalent of running the arithmetic: the claim is
      checked against the source rather than against the model's confidence.

      A question whose evidence is not in the text is either unanswerable from
      that passage or has an invented quote. Both are critical, and both read
      completely plausibly — which is exactly why this is counted rather than
      reviewed.
    """
    package = _load(material_package)
    if not package:
        return {"error": "material package is not readable JSON"}
    issues = check_reading_evidence(package)
    return {
        "checked": sum(
            1 for i in package.get("items", []) or []
            if i.get("stage") in {"gist", "detail", "inference", "vocabulary-in-context"}
            for _ in i.get("exercises") or []
        ),
        "unsupported": [i for i in issues if i["severity"] == "critical"],
        "issues": issues,
        "all_supported": not any(i["severity"] == "critical" for i in issues),
    }


def check_target_language(material_package: str, target_language: str = "") -> dict:
    """Check every learner-facing string is in the target language.

    Args:
      material_package: The material package, as JSON.
      target_language: The language it must be in, e.g. "german". Read from the
        package when omitted.

    Returns:
      Every field containing English, with the words found. A German lesson is
      in German from the cover to the last page — titles, instruction lines,
      prompts, options, answers, the summary — and English scaffolding around
      target-language content is the defect this catches.

      Quoted text is exempt: a dialogue about what an English word means is
      allowed to contain it.
    """
    package = _load(material_package)
    if not package:
        return {"error": "material package is not readable JSON"}
    language = target_language or package.get("target_language") or ""
    if not language:
        return {"skipped": "no target language on the package"}
    return _check_language(package, language)


def check_deck_format(material_package: str) -> dict:
    """Check the material against the lesson-deck format requirements.

    Args:
      material_package: The material package, as JSON.

    Returns:
      Whether it is compliant, and every violation with its severity and the
      slide at fault. Counted, not judged: slide totals, image coverage, images
      specified but never produced, words per slide, missing alt text.

      An image with provider "pending" is a promise, not a picture. A deck of
      promises looks complete here and arrives at the lesson blank, so it counts
      as a blocking failure.
    """
    package = _load(material_package)
    slides = package.get("slides")
    if slides is None:
        # The package is item-based; present each item as a slide so the format
        # rules can be applied to what actually exists.
        slides = [
            {
                "number": n,
                "kind": item.get("kind", ""),
                "phase": item.get("stage") or item.get("phase", ""),
                "title": item.get("title", ""),
                "body": item.get("content", ""),
                "instruction": item.get("instruction", ""),
                "images": item.get("images") or [],
                "exercises": item.get("exercises") or [],
            }
            for n, item in enumerate(package.get("items", []), 1)
        ]
    return _check_deck({"slides": slides})


def check_material_coverage(lesson_plan: str, material_package: str) -> dict:
    """Check every activity that asked for material actually got some.

    Args:
      lesson_plan: The lesson plan, as JSON.
      material_package: The material package, as JSON.

    Returns:
      Which activities needed material, which received it, and which are
      uncovered. Computed by comparing ids, not by reading — a missing item is
      exactly the thing prose review skims past.
    """
    plan, package = _load(lesson_plan), _load(material_package)
    needed = {
        a.get("id"): a.get("material_needed", "")
        for a in plan.get("activities", [])
        if (a.get("material_needed") or "").strip()
    }
    covered = {i.get("activity_id") for i in package.get("items", [])}
    uncovered = sorted(set(needed) - covered)
    orphaned = sorted(covered - {a.get("id") for a in plan.get("activities", [])})
    return {
        "activities_needing_material": sorted(needed),
        "activities_covered": sorted(x for x in covered if x),
        "uncovered": uncovered,
        "orphaned_items": orphaned,
        "complete": not uncovered,
    }


MODEL = os.environ.get("ZANOBA_MODEL", "gemini-3.5-flash")

INSTRUCTION = """\
You are the Material Checker. You decide whether one prepared lesson is fit to
teach, and if not, exactly what should be redone — and no more than that.

The objectives:
{lesson_objectives}

The blueprint the material was written against:
{material_blueprint?}

The plan:
{lesson_plan}

The material:
{material_package}

## Run the counted checks first. All of them.

1. validate_material — the structural report. Take its issues as YOURS: every
   critical issue it returns is a critical issue in your report, with the same
   item_id, scope and fix. Take its dimension scores into your `dimensions`.
2. check_target_language — any English on a learner-facing field is CRITICAL.
   A German lesson is in German from the cover to the last page. Material that
   is otherwise excellent still fails on this.
3. check_material_coverage — an uncovered activity is a tutor arriving at minute
   30 with nothing.
4. check_deck_format — an image with provider "pending" is a promise, not a
   picture, and a deck of promises arrives blank.
5. For a READING lesson: verify_reading_evidence. Every unsupported answer is
   critical. Do not read the text and decide the answer is probably in there —
   run it.
6. For a STEM lesson: verify_calculation on EVERY arithmetic answer. Do not read
   the arithmetic and judge it; run it. "unverifiable" is not "correct".

Never mark something correct because it looks right. Only the tool result counts.
List what you actually ran in checks_run and do not claim a check you skipped.

## Then judge what the tools cannot

These need reading, and they are the reason you exist rather than a script.

NATURALNESS — would a native speaker actually say this? A sentence that exists
only to demonstrate the target reads like one. "Der Computer ist ein Computer."
is grammatical and worthless.

AUTHENTICITY — would this situation really happen? Does the dialogue have a
REASON — somebody wants something, has misunderstood, needs help? Two people
greeting each other in a vacuum is a list of phrases with colons in front.

DISTRACTORS — is each wrong option plausible, and does it reflect a mistake a
learner at this level actually makes? Options that are obviously wrong test
nothing.

ALIGNMENT — does each item serve the objective its slot claims? Does the
assessment measure the objectives?

Then, by focus:

GRAMMAR — is the rule stated correctly and briefly? Does the noticing stage
actually withhold the rule, or does it print the answer above the exercise?

COMMUNICATION — could the learner complete the final task while AVOIDING the
target language? If yes, that is a critical failure, however well written it is.
Is there a real information gap, or do both speakers already know everything? Do
the success criteria describe observable communication rather than grammatical
accuracy? Does the support actually fall away, or is the "role-play" two people
reading predetermined sentences?

VOCABULARY — is every word worth the learner's time at this level? Does the
learner ever have to RETRIEVE a word rather than recognise one on the slide? Are
the example sentences things a person would say? Do the words come back after
the stage that introduced them? A lesson that is technically correct and is
essentially a word list with quizzes FAILS.

READING — is the text coherent and natural for its genre, or does it read as an
AI textbook passage? Is an "inference" question actually answerable only by
inferring, or is the answer stated outright? Does the lesson teach how to
understand the text, or only test whether the learner did? Does a pre-reading
image support prediction without giving the answers away?

IMAGES — for each one: is the intended concept immediately identifiable? Is it
dominant in the frame? Could this picture reasonably be a different concept?
Are there distracting elements? Is it right for the band? Does it support the
actual exercise? Ambiguity is a defect EXCEPT on a communicative scene whose
spec says ambiguity_tolerance "intentional" — there it is the point, and the
question instead is whether it gives the learner something to ask about.

## The verdict

- status "FAIL" if there is any critical issue, or overall_score below 70.
- status "PASS" otherwise. Low-severity notes may still be listed.

A material item does NOT pass just because it is grammatically correct. Correct
and pedagogically useless is a fail.

## Regeneration targets — the narrowest thing that fixes it

Set the scope on every issue: image, exercise, item, stage or lesson.

  image 3 came back ambiguous        -> scope "image", target that image
  exercise 5 has no defensible answer -> scope "exercise", target that exercise
  the dialogue is lifeless            -> scope "item", target that item
  the whole controlled stage is flat  -> scope "stage"
  the blueprint itself is wrong       -> scope "lesson", action revise_blueprint

Only "lesson" when the blueprint is genuinely invalid. Regenerating everything
because one picture failed is slower AND worse: it throws away what was right.

Every regeneration target needs an INSTRUCTION, not just a complaint. "Regenerate
this image" gets the same image back. "Regenerate: the frame contains a house and
a bench as well as the garden, so the learner cannot tell which one to name —
exclude buildings and furniture" gets a different one.

Never rewrite the material yourself. Report, do not repair.
"""

quality_checker_agent = LlmAgent(
    name="quality_checker_agent",
    model=MODEL,
    description="Validates a prepared lesson and names targeted revisions.",
    instruction=INSTRUCTION,
    tools=[validate_material, check_target_language, verify_reading_evidence,
           check_deck_format, check_material_coverage, verify_calculation,
           get_cefr_guidelines],
    output_schema=QualityReport,
    output_key="quality_report",
)
