"""Build one lesson per language focus, end to end, and report on each.

Runs the real language branch — Lesson Planner, Material Planner, Material
agent, Material Checker — against a seeded placement, so a specific lesson can
be targeted rather than whichever one the Curriculum agent judges next. The
placement and the diagnosis are built from the curriculum file itself, so
nothing here is invented; only the choice of which lesson to build is forced.

    python scripts/build_focus_lessons.py            # all four
    python scripts/build_focus_lessons.py grammar    # just one
"""
from __future__ import annotations

import asyncio, json, sys, time
from pathlib import Path

from google.adk.runners import InMemoryRunner
from google.adk.workflow import START, Workflow
from google.genai import types

from zanoba_agent.agents.language_material import language_material_agent
from zanoba_agent.agents.language_planner import language_lesson_planner
from zanoba_agent.agents.material_planner import material_planner_agent
from zanoba_agent.agents.quality_checker import quality_checker_agent
from zanoba_agent.agents.stem_material import stem_material_agent
from zanoba_agent.agents.stem_planner import stem_lesson_planner
from zanoba_agent.curriculum import repository
from zanoba_agent.material import beamer, deck, images
from zanoba_agent.material.validation import validate_package

# The language branch on its own. Same nodes and same order as the full
# pipeline; only the three upstream stages are replaced by seeded state.
branch = Workflow(
    name="language_material_branch",
    description="Plan, specify, write and check the material for one lesson.",
    edges=[(START, language_lesson_planner, material_planner_agent,
            language_material_agent, quality_checker_agent)],
)

# The STEM branch, node for node as `preparation_workflow` runs it: planner,
# material, checker. No Material Planner and no blueprint — a maths lesson's
# material is written against the plan and the objectives directly, and the
# full pipeline routes it the same way.
stem_branch = Workflow(
    name="stem_material_branch",
    description="Plan, write and check the material for one STEM lesson.",
    edges=[(START, stem_lesson_planner, stem_material_agent, quality_checker_agent)],
)


def branch_for(subject: str) -> Workflow:
    """Whichever branch the real pipeline would route this subject down."""
    return branch if repository.domain_of(subject) == "language" else stem_branch

TARGETS = {
    "grammar":       ("german", "a1-1", "a1-1.classroom.l3", "A1"),
    "communication": ("german", "a1-1", "a1-1.classroom.l2", "A1"),
    "vocabulary":    ("german", "a1-1", "a1-1.classroom.l1", "A1"),
    "reading":       ("german", "a1-1", "a1-1.myself.l1",    "A1"),
}


def seed(student: str, subject: str, level: str, item_id: str, band: str) -> dict:
    """Build the three upstream documents from the curriculum's own content."""
    item = repository.find_item(subject, item_id)
    if item is None:
        raise SystemExit(f"no curriculum item {item_id!r} in {subject!r}")

    # The domain decides which branch runs, so it is read from the curriculum
    # rather than assumed. Seeding "language" for a maths lesson sent it down a
    # branch whose first node asks which grammar point to teach.
    domain = repository.domain_of(subject)

    placement = {
        "student_id": student, "subject": subject, "domain": domain,
        "level_id": level, "next_item_id": item.id, "next_item_title": item.title,
        "granularity": item.granularity, "focus": item.focus,
        "objectives": item.objectives, "prerequisites": item.prerequisites,
        "unmet_prerequisites": [], "completed_count": 0, "total_count": 0,
        "reason": "Seeded for a demonstration build of this specific lesson.",
    }
    diagnosis = {
        "student_id": student, "subject": subject, "level_id": level,
        "target_item_id": item.id, "mastered": [], "partially_mastered": [],
        "missing_prerequisites": [], "misconceptions": [], "recurring_errors": [],
        "readiness": "ready", "recommended_difficulty": "at", "review_first": [],
        "evidence_lesson_count": 0,
        "reason": "No lesson history on record, so the learner is treated as a "
                  "true beginner at this level and the lesson is pitched at band.",
    }
    objectives = {
        "student_id": student, "subject": subject, "level_id": level,
        "target_item_id": item.id, "focus": item.focus,
        "objectives": [
            {"id": f"o{n}", "statement": text,
             "measurable_by": "The learner does this unaided in the final activity.",
             "covers_item_id": item.id, "source_objective": text,
             "is_review": False, "estimated_minutes": 20}
            for n, text in enumerate(item.objectives[:2], 1)
        ],
        "deferred": item.objectives[2:],
        "reason": "The curriculum's own objectives for this lesson, fitted to the hour.",
    }
    return {
        "curriculum_placement": json.dumps(placement, ensure_ascii=False),
        "diagnostic_report": json.dumps(diagnosis, ensure_ascii=False),
        "lesson_objectives": json.dumps(objectives, ensure_ascii=False),
        "_title": item.title, "_band": band,
    }


async def build(focus: str, student: str = "stu-demo-1", make_images: bool = True):
    subject, level, item_id, band = TARGETS[focus]
    state = seed(student, subject, level, item_id, band)
    title, band = state.pop("_title"), state.pop("_band")

    print(f"\n{'=' * 78}\n{focus.upper():14} {item_id}  —  {title}\n{'=' * 78}")
    started = time.time()

    runner = InMemoryRunner(agent=branch, app_name="z")
    session = await runner.session_service.create_session(
        app_name="z", user_id=student, state=state)
    message = types.Content(role="user", parts=[types.Part(
        text=f"Build the material for {item_id} ({focus}, {band}).")])
    async for _ in runner.run_async(user_id=student, session_id=session.id,
                                    new_message=message):
        pass
    final = (await runner.session_service.get_session(
        app_name="z", user_id=student, session_id=session.id)).state

    load = lambda k: (json.loads(final[k]) if isinstance(final.get(k), str)
                      else final.get(k) or {})
    plan, blueprint = load("lesson_plan"), load("material_blueprint")
    package, verdict = load("material_package"), load("quality_report")
    objectives = json.loads(state["lesson_objectives"])

    print(f"plan     : {len(plan.get('activities', []))} activities, "
          f"{sum(a.get('minutes', 0) for a in plan.get('activities', []))} min")
    slots = blueprint.get("slots", [])
    print(f"blueprint: {len(slots)} slots  "
          f"{' -> '.join(s.get('stage', '?') for s in slots)}")
    print(f"           images planned: {sum(1 for s in slots if s.get('visual'))}"
          f"   exercise items: "
          f"{sum((s.get('exercise') or {}).get('number_of_items', 0) for s in slots)}")
    print(f"material : {len(package.get('items', []))} items, "
          f"{sum(len(i.get('exercises') or []) for i in package.get('items', []))} exercises")

    if make_images:
        # Every content slide carries a picture now, and a vocabulary lesson
        # carries one per word, so a cap of ten silently truncated the lesson
        # and the checker then failed it for an image nobody had made.
        print("images   :", images.produce_for_package(
            package, lesson_id=item_id, limit=40))

    report = validate_package(package, blueprint=blueprint or None,
                              objectives=objectives, band=band, focus=focus,
                              target_language="german")
    print(f"checker  : {report['status']}  score={report['overall_score']}  "
          f"critical={len(report['critical_issues'])}")
    dims = {k: v for k, v in report.items()
            if isinstance(v, int) and not isinstance(v, bool)
            and k not in {"score", "overall_score"}}
    print("           " + "  ".join(f"{k}={v}" for k, v in dims.items()))
    for issue in report["issues"][:6]:
        print(f"   [{issue['severity']:<8}] {issue['scope']:<8} "
              f"{issue['item_id'][:18]:<18} {issue['problem'][:56]}")

    # Render the deck: HTML for a language lesson, Beamer for STEM, because a
    # maths lesson is fractions and matrices and HTML draws those badly.
    try:
        domain = package.get("domain", "language")
        if domain == "stem":
            built = beamer.build(package, plan, objectives, Path("out") / focus)
        else:
            built = deck.build(package, plan, objectives, Path("out") / focus)
        pages = len(built.get("slides", [])) or "?"
        print(f"deck     : {pages} slides -> {built['pdf']} "
              f"({built['pdf'].stat().st_size // 1024} KB)")
        layouts = [i.get("slide", {}).get("kind") for i in package.get("items", [])
                   if i.get("slide")]
        print(f"           layouts: {layouts or 'none — items are prose'}")
    except Exception as exc:
        print(f"deck     : FAILED {type(exc).__name__}: {exc}")

    out = Path("out") / f"lesson-{focus}.json"
    out.parent.mkdir(exist_ok=True)
    out.write_text(json.dumps(
        {"plan": plan, "blueprint": blueprint, "material": package,
         "objectives": objectives, "quality": report, "agent_verdict": verdict},
        indent=1, ensure_ascii=False), encoding="utf-8")
    print(f"saved    : {out}   ({time.time() - started:.0f}s)")
    return report


async def main(which=None, images_on="images"):
    focuses = [which] if which in TARGETS else list(TARGETS)
    results = {}
    for focus in focuses:
        try:
            results[focus] = await build(focus, make_images=(images_on == "images"))
        except Exception as exc:
            print(f"  !! {focus} failed: {type(exc).__name__}: {exc}")
            results[focus] = None
    print(f"\n{'=' * 78}\nSUMMARY")
    for focus, report in results.items():
        if report is None:
            print(f"  {focus:14} FAILED TO BUILD")
        else:
            print(f"  {focus:14} {report['status']:4} score={report['overall_score']:3} "
                  f"critical={len(report['critical_issues'])}")


# Guarded, because `warm_lessons.py` imports `seed` and `branch_for` from here.
# Without this, warming a level ran all four demonstration builds first — four
# full pipeline runs, paid for, before the thing you actually asked for started.
if __name__ == "__main__":
    asyncio.run(main(*(sys.argv[1:] or [])))
