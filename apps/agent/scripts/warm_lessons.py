"""Pre-build lesson material so "Start now" starts now.

Runs the expensive half of the pipeline ahead of time, once per curriculum
lesson rather than once per student, and stores the result. A student opening a
lesson then gets it from the cache in milliseconds instead of waiting eight
minutes for a model to write it.

    python scripts/warm_lessons.py german a1-1              # a whole level
    python scripts/warm_lessons.py german a1-1 --chapter a1-1.classroom
    python scripts/warm_lessons.py german a1-1 --force      # rebuild cached ones

Safe to re-run: anything already cached at the current version is skipped, so an
interrupted warm continues where it stopped rather than paying twice.
"""
from __future__ import annotations

import asyncio, sys, time

from zanoba_agent.curriculum import repository
from zanoba_agent.material import cache, images

sys.path.insert(0, str(__import__("pathlib").Path(__file__).parent))
from build_focus_lessons import branch_for, seed  # noqa: E402

from google.adk.runners import InMemoryRunner  # noqa: E402
from google.genai import types  # noqa: E402
import json  # noqa: E402



async def _run(agent, state: dict, prompt: str) -> dict:
    """Run one stage in its OWN session and return the state it leaves behind."""
    runner = InMemoryRunner(agent=agent, app_name="warm")
    session = await runner.session_service.create_session(
        app_name="warm", user_id="baseline", state=state)
    async for _ in runner.run_async(
            user_id="baseline", session_id=session.id,
            new_message=types.Content(role="user", parts=[types.Part(text=prompt)])):
        pass
    return dict((await runner.session_service.get_session(
        app_name="warm", user_id="baseline", session_id=session.id)).state)


async def run_in_stages(subject, item, band, state: dict) -> dict:
    """Plan, then write, then check — each from a clean session.

    Run as one graph, every node shares a session, so by the time the material
    agent starts, its context already holds the lesson planner's and the material
    planner's entire conversations — every tool call and every tool result. For a
    grammar lesson that fits. For a VOCABULARY lesson, whose blueprint is 41,000
    characters across ten slots because every word gets its own picture, it does
    not: the agent's output was first squeezed (a lesson came back with no
    exercises at all) and then disappeared entirely, leaving `material_package`
    unwritten and the checker raising KeyError on a state key that was never set.

    The same agent, given the same blueprint in a session of its own, writes the
    lesson without complaint. So the stages are run as separate sessions and the
    documents are handed between them explicitly. Nothing about the agents
    changes; they simply stop inheriting each other's history.
    """
    from zanoba_agent.agents.language_material import language_material_agent
    from zanoba_agent.agents.language_planner import language_lesson_planner
    from zanoba_agent.agents.material_planner import material_planner_agent
    from zanoba_agent.agents.quality_checker import quality_checker_agent
    from zanoba_agent.agents.stem_material import stem_material_agent
    from zanoba_agent.agents.stem_planner import stem_lesson_planner

    ask = f"Build the baseline material for {item.id} ({item.focus}, {band})."
    language = repository.domain_of(subject) == "language"

    planners = ([language_lesson_planner, material_planner_agent] if language
                else [stem_lesson_planner])
    writer = language_material_agent if language else stem_material_agent

    for planner in planners:
        state = await _run(planner, state, ask)
    # The clean break. Everything the writer needs is in state; none of what it
    # does not need — the planners' turns — comes with it.
    state = await _run(writer, state, ask)
    return await _run(quality_checker_agent, state, ask)


async def warm_one(subject: str, level: str, item, band: str,
                   make_images: bool, force: bool) -> str:
    key = cache.baseline_key(subject, item.id, band)
    if not force and cache.load(key) is not None:
        return "cached"
    if item.granularity != "lesson":
        return "skipped (not a lesson)"
    # A focus is a language idea — grammar, vocabulary, reading. A language
    # lesson without one is an orientation page with no stage set to build
    # from; a maths lesson never has one and must not be skipped for it.
    if repository.domain_of(subject) == "language" and not item.focus:
        return "skipped (no focus)"

    state = seed("baseline", subject, level, item.id, band)
    state.pop("_title"); state.pop("_band")
    final = await run_in_stages(subject, item, band, state)
    load = lambda k: (json.loads(final[k]) if isinstance(final.get(k), str)
                      else final.get(k) or {})
    package, blueprint = load("material_package"), load("material_blueprint")
    if not package.get("items"):
        return "FAILED (no material)"

    if make_images:
        # Every content slide carries a picture and a vocabulary lesson carries
        # one per word, so a cap of ten silently truncated the lesson and the
        # checker then failed it for a picture nobody had made. Most of these
        # are now searched rather than generated, so the cap is about lesson
        # length rather than cost.
        print("   ", images.produce_for_package(package, lesson_id=item.id, limit=40))

    cache.store(key, blueprint, package, load("lesson_plan"),
                json.loads(state["lesson_objectives"]), load("quality_report"),
                subject=subject, item_id=item.id, band=band, focus=item.focus)
    return "built"


async def main(subject="german", level="a1-1", *flags):
    force = "--force" in flags
    make_images = "--noimages" not in flags
    chapter = None
    if "--chapter" in flags:
        chapter = flags[flags.index("--chapter") + 1]

    # The band is the CEFR one for a language and empty for a STEM subject,
    # which is what the cache key expects. Splitting the level id gave
    # "FR.SIXIEME" for maths and keyed every lesson under a band that is not one.
    band = repository.band_of(subject, level)
    items = [i for i in repository.items_in_order(subject, level)
             if chapter is None or i.parent_id == chapter]
    print(f"warming {len(items)} items in {subject} {level} "
          f"(band {band}, images={'on' if make_images else 'off'})\n")

    started = time.time()
    for item in items:
        at = time.time()
        try:
            outcome = await warm_one(subject, level, item, band, make_images, force)
        except Exception as exc:
            outcome = f"FAILED ({type(exc).__name__}: {exc})"
        took = time.time() - at
        print(f"  {item.id:28} {str(item.focus or '-'):14} {outcome:22} {took:6.0f}s")
    print(f"\ntotal {time.time() - started:.0f}s. "
          f"Every student who opens one of these now gets it instantly.")


asyncio.run(main(*(sys.argv[1:] or [])))
