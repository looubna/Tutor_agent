"""Prepare a lesson, produce its images, render the deck, and check it.

Runs the full preparation pipeline including the new Material Planner stage, so
the material is written against a validated blueprint rather than improvised
from the topic. Costs Gemini calls.

    python scripts/build_lesson.py [student] [subject] [level]
"""
import asyncio, json, sys
from pathlib import Path
from google.adk.runners import InMemoryRunner
from google.genai import types
from zanoba_agent.agents import curriculum_agent as ca, diagnostic_agent as da
from zanoba_agent.agents import planner_tools as pt
from zanoba_agent.material import deck, images
from zanoba_agent.material.validation import validate_package
from zanoba_agent.store.history import FirestoreLessonHistory
from zanoba_agent.store.profiles import FirestoreProfileStore
from zanoba_agent.workflows.preparation import (
    BLUEPRINT_KEY, MATERIAL_KEY, OBJECTIVES_KEY, PLAN_KEY, preparation_workflow)

P = "ai-tutor-zanoba"
h, pr = FirestoreLessonHistory(project=P), FirestoreProfileStore(project=P)
ca.set_history_store(h); da.set_stores(pr, h); pt.set_stores(pr, h)


async def main(student="stu-demo-1", subject="german", level="a1-1"):
    r = InMemoryRunner(agent=preparation_workflow, app_name="z")
    s = await r.session_service.create_session(app_name="z", user_id=student)
    m = types.Content(role="user", parts=[types.Part(
        text=f"student_id={student}, subject={subject}, level_id={level}. "
             "Prepare the next 60-minute lesson.")])
    async for _ in r.run_async(user_id=student, session_id=s.id, new_message=m):
        pass
    st = (await r.session_service.get_session(
        app_name="z", user_id=student, session_id=s.id)).state
    load = lambda k: json.loads(st[k]) if isinstance(st.get(k), str) else st.get(k) or {}
    pkg, plan, objs = load(MATERIAL_KEY), load(PLAN_KEY), load(OBJECTIVES_KEY)
    bp = load(BLUEPRINT_KEY)

    focus = bp.get("focus") or plan.get("focus") or ""
    print(f"blueprint: focus={focus} slots={len(bp.get('slots', []))} "
          f"stages={' -> '.join(s.get('stage','') for s in bp.get('slots', []))}")
    print("prepared :", len(pkg.get("items", [])), "items")
    print("images   :", images.produce_for_package(
        pkg, lesson_id=pkg.get("target_item_id", "")))

    report = validate_package(pkg, blueprint=bp or None, objectives=objs,
                              band=bp.get("band", ""), focus=focus)
    print(f"checker  : {report['status']} score={report['overall_score']} "
          f"critical={len(report['critical_issues'])}")
    for name, value in report.items():
        if isinstance(value, int) and not isinstance(value, bool) \
                and name not in {"score", "overall_score"}:
            print(f"           {name:26} {value}")
    for issue in report["issues"][:8]:
        print(f"   [{issue['severity']:<8}] {issue['scope']:<8} "
              f"{issue['item_id'][:16]:<16} {issue['problem'][:60]}")

    out = deck.build(pkg, plan, objs, Path("out"))
    print(f"deck     : {len(out['slides'])} slides, "
          f"{out['pdf'].stat().st_size // 1024} KB")
    Path("out/lesson.json").write_text(json.dumps(
        {"material": pkg, "plan": plan, "objectives": objs, "blueprint": bp,
         "quality": report}, indent=1, ensure_ascii=False), encoding="utf-8")

asyncio.run(main(*(sys.argv[1:] or [])))
