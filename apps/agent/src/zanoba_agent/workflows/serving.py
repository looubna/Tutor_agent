"""Getting a prepared lesson in front of a student, fast.

The pipeline in `preparation` builds a lesson from nothing in eight and a half
minutes. That is the right amount of time to spend and the wrong amount of time
to make someone wait, so this module is the read path: what happens when a
student presses "Start now".

Three outcomes, and the common one is the fast one:

  HIT        the baseline for this lesson exists and the student's diagnosis
             changes nothing about it. Served in under a millisecond.
  PERSONALISE the baseline exists and the diagnosis changes two or three slots.
             Those are regenerated; everything else, including every image, is
             carried through with its original ids and urls.
  MISS       nothing is cached, or the student is not ready for this lesson at
             all, in which case it is not this lesson that they need. Build it.

The design rests on one observation: "der, die, das" at A1 is the same grammar
point, the same rule table and the same photograph of a garden for every learner
who reaches it. Only the practice is personal. Because the blueprint records
which slot every item was written against, "this learner needs more controlled
practice" is a statement about two slot ids rather than a reason to start again.
"""

from __future__ import annotations

import json
import time
from typing import Any

from ..material import cache


def prepare_for_student(subject: str, item_id: str, band: str, student_id: str,
                        diagnosis: dict | None = None,
                        profile: dict | None = None) -> dict[str, Any]:
    """Return the lesson to teach this student, and say how it was obtained.

    Never blocks on generation. When work is needed it is described rather than
    performed, so the caller decides whether to run it now, run it in the
    background while the student reads the objectives, or fall back to the
    baseline. A student who presses "Start now" should always get something.
    """
    started = time.time()
    marks = cache.fingerprint(diagnosis, profile)
    personal_key = cache.personalised_key(subject, item_id, band, student_id, marks)

    # Already personalised for this student, at this state of knowledge.
    ready = cache.load(personal_key)
    if ready is not None:
        return _served(ready, "personalised_hit", started, {},
                       "this student's version of the lesson was already built "
                       "and nothing they know has changed since")

    baseline = cache.load_baseline(subject, item_id, band)
    if baseline is None:
        return {
            "status": "miss",
            "lesson": None,
            "work_required": {"scope": "build", "reason": "nothing cached"},
            "elapsed_ms": round((time.time() - started) * 1000, 2),
            "explanation": "no baseline for this lesson yet. Run the preparation "
                           "pipeline, or warm it with scripts/warm_lessons.py so "
                           "the next student does not wait.",
        }

    plan = cache.personalisation_plan(baseline.get("blueprint", {}),
                                      diagnosis, profile)

    if plan["scope"] == "reuse":
        return _served(baseline, "baseline_hit", started,
                       cache.savings(baseline.get("blueprint", {}), plan),
                       "nothing in this student's diagnosis changes the lesson, "
                       "so the shared baseline is exactly right")

    if plan["scope"] == "rebuild":
        return {
            "status": "miss",
            "lesson": baseline,
            "work_required": {"scope": "build", "reason": plan["reasons"].get("*", [""])[0]},
            "elapsed_ms": round((time.time() - started) * 1000, 2),
            "explanation": "this learner is not ready for this lesson, so what "
                           "they need is a different lesson rather than this one "
                           "adjusted. The baseline is returned as a fallback but "
                           "should not be taught as it stands.",
        }

    applied = cache.apply_plan(baseline, plan)
    savings = cache.savings(baseline.get("blueprint", {}), plan)
    return {
        "status": "personalise",
        # Servable immediately while the small regeneration runs behind it.
        "lesson": baseline,
        "carried_items": applied["carried_items"],
        "work_required": {
            "scope": "targeted",
            "regenerate_slots": applied["regenerate_slots"],
            "regeneration_request": json.dumps(
                {"attempt": 1, "targets": applied["instructions"]},
                ensure_ascii=False),
        },
        "savings": savings,
        "personalised_key": personal_key,
        "elapsed_ms": round((time.time() - started) * 1000, 2),
        "explanation": (
            f"{savings['slots_reused']} of {savings['slots_total']} slots and "
            f"{savings['images_reused']} of {savings['images_total']} images are "
            f"reused; only {', '.join(applied['regenerate_slots'])} need "
            f"rewriting ({savings['work_avoided']} of the work avoided)."),
    }


def _served(entry: dict, status: str, started: float, savings: dict,
            explanation: str) -> dict:
    return {
        "status": status,
        "lesson": entry,
        "work_required": None,
        "savings": savings,
        "elapsed_ms": round((time.time() - started) * 1000, 2),
        "explanation": explanation,
    }


def store_personalised(subject: str, item_id: str, band: str, student_id: str,
                       diagnosis: dict | None, profile: dict | None,
                       blueprint: dict, package: dict, plan: dict,
                       objectives: dict, quality: dict | None = None) -> str:
    """Save a personalised lesson so the same student never rebuilds it.

    Keyed by what the personalisation was computed from, so when the student
    learns the thing it was compensating for, this version is superseded rather
    than served stale.
    """
    key = cache.personalised_key(subject, item_id, band, student_id,
                                 cache.fingerprint(diagnosis, profile))
    cache.store(key, blueprint, package, plan, objectives, quality,
                student_id=student_id, subject=subject, item_id=item_id, band=band)
    return key
