"""The diamond: *is the student have language lesson*.

Deliberately a function node, not an agent. Which planner a subject needs is
already recorded — `german.json` has levels and `mathematics.json` has programs,
and `repository.domain_of` reads it off the file. There is no judgement to make,
so there is nothing for a model to add except a chance to answer wrongly.

This is the brief's rule applied literally: an agent when it needs reasoning and
tools of its own, plain Python when the operation is deterministic.
"""

from __future__ import annotations

import json

from google.adk.events.event import Event

from ..curriculum import repository

LANGUAGE_ROUTE = "language"
STEM_ROUTE = "stem"


def route_by_domain(node_input) -> Event:
    """Send the plan down the language branch or the STEM branch.

    Reads the subject from the placement the Curriculum agent produced and looks
    up its domain. An unknown subject routes to STEM rather than failing: STEM's
    structure is the more general of the two, and a lesson planned with an extra
    prerequisite review is recoverable in a way that no lesson at all is not.
    """
    subject = ""
    payload = node_input
    if isinstance(payload, str):
        try:
            payload = json.loads(payload)
        except ValueError:
            payload = {}
    if isinstance(payload, dict):
        subject = str(payload.get("subject", ""))

    try:
        route = repository.domain_of(subject) if subject else STEM_ROUTE
    except repository.CurriculumNotFound:
        route = STEM_ROUTE

    return Event(
        author="route_by_domain",
        output={"subject": subject, "domain": route},
        route=route,
    )


# How many times material may be sent back before the lesson goes out as-is.
# Bounded because a loop that can run forever will, on the one lesson where the
# checker and the material agent disagree about something neither can fix.
MAX_QUALITY_ATTEMPTS = 3

PASS_ROUTE = "pass"
REVISE_LANGUAGE_ROUTE = "revise_language"
REVISE_STEM_ROUTE = "revise_stem"
ATTEMPTS_KEY = "quality_attempts"

# Where the gate leaves the repair brief for the Material agent to read back.
# The whole point of targeted regeneration: the generator is told which three
# items to rewrite, and carries the rest through untouched.
REGENERATION_KEY = "regeneration_request"

# Narrowest repair first. Regenerating a lesson because one image came back
# wrong is both slower and worse than regenerating the image.
_SCOPE_RANK = {"image": 0, "exercise": 1, "item": 2, "stage": 3, "lesson": 4}


def quality_gate(ctx, node_input) -> Event:
    """Pass the lesson, or send back exactly what failed.

    The counter lives in session state rather than in the report, because the
    report is written by a model and this bound must not be something a model
    can talk its way past.

    What is new here is the second half: the gate writes the checker's
    regeneration targets into state as `regeneration_request`, and the Material
    agent's instruction reads them back. So a revision pass rewrites the three
    items that failed and carries the rest through unchanged, instead of
    re-improvising the whole lesson from the topic and losing everything that
    was right.

    Exhausting the attempts does not mean the lesson is fine — it means we stop
    paying for revisions that are not converging. The unresolved issues stay in
    the report, and `gave_up` says plainly that this is what happened.
    """
    report = node_input
    if isinstance(report, str):
        try:
            report = json.loads(report)
        except ValueError:
            report = {}
    if not isinstance(report, dict):
        report = {}

    attempts = int(ctx.state.get(ATTEMPTS_KEY, 0)) + 1
    ctx.state[ATTEMPTS_KEY] = attempts

    status = str(report.get("status", "pass")).lower()
    blocking = [
        i for i in report.get("issues", [])
        if isinstance(i, dict)
        and i.get("severity") in {"high", "critical"}
        and i.get("action", "regenerate_material") == "regenerate_material"
    ]
    targets = _regeneration_targets(report, blocking)

    if status in {"pass", "PASS".lower()} or not blocking:
        route, gave_up = PASS_ROUTE, False
    elif attempts >= MAX_QUALITY_ATTEMPTS:
        route, gave_up = PASS_ROUTE, True
    else:
        domain = str(ctx.state.get("lesson_domain", "")) or _domain_from_state(ctx)
        route = REVISE_LANGUAGE_ROUTE if domain == LANGUAGE_ROUTE else REVISE_STEM_ROUTE
        gave_up = False

    # Only carry a repair brief when we are actually going back round. Leaving a
    # stale one in state would make the next lesson's first pass think it was a
    # revision of something.
    if route == PASS_ROUTE:
        ctx.state[REGENERATION_KEY] = ""
    else:
        ctx.state[REGENERATION_KEY] = json.dumps(
            {"attempt": attempts, "targets": targets}, ensure_ascii=False)

    return Event(
        author="quality_gate",
        output={
            "attempt": attempts,
            "max_attempts": MAX_QUALITY_ATTEMPTS,
            "status": status,
            "blocking_issues": len(blocking),
            "regeneration_targets": len(targets),
            "scopes": sorted({t["scope"] for t in targets}),
            "route": route,
            "gave_up": gave_up,
        },
        route=route,
    )


def _regeneration_targets(report: dict, blocking: list[dict]) -> list[dict]:
    """What to send back, narrowest scope first.

    Prefers the checker's own targets when it produced them; falls back to
    deriving them from the issues, so a checker that reported problems without
    filling in the targets still gets a targeted repair rather than a whole-
    lesson one.

    A target with no instruction is dropped to a reason-only entry rather than
    discarded — but the instruction is what matters. Asking for the same thing
    again gets the same answer back.
    """
    given = report.get("regeneration_targets") or []
    targets = [t for t in given if isinstance(t, dict) and t.get("target")]
    if not targets:
        grouped: dict[tuple, dict] = {}
        for issue in blocking:
            target = str(issue.get("item_id", "")).strip()
            scope = str(issue.get("scope", "item"))
            if not target:
                scope, target = "lesson", "*"
            key = (target, scope)
            entry = grouped.setdefault(
                key, {"target": target, "scope": scope, "reasons": [],
                      "instructions": []})
            entry["reasons"].append(str(issue.get("problem", ""))[:200])
            if issue.get("fix"):
                entry["instructions"].append(str(issue["fix"])[:200])
        targets = list(grouped.values())

    return sorted(targets, key=lambda t: _SCOPE_RANK.get(t.get("scope", "item"), 9))


def _domain_from_state(ctx) -> str:
    """Which branch this lesson took, read back off the placement."""
    placement = ctx.state.get("curriculum_placement")
    if isinstance(placement, str):
        try:
            placement = json.loads(placement)
        except ValueError:
            placement = {}
    if isinstance(placement, dict):
        return str(placement.get("domain", STEM_ROUTE))
    return STEM_ROUTE
