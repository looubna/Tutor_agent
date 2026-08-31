"""Run ONLY the material agent, on a vocabulary blueprint already on disk.

Four explanations for `KeyError: material_package` have now been wrong. This
stops reasoning about it: it runs the one node that fails, with its inputs taken
from a cached lesson rather than regenerated, and prints every event it emits —
so the answer comes from what the agent does rather than from what its output
implies.

One model call, about two minutes, no planner and no checker.
"""
from __future__ import annotations

import asyncio, json, sys, traceback

from google.adk.runners import InMemoryRunner
from google.genai import types

from zanoba_agent.agents.language_material import language_material_agent
from zanoba_agent.material import cache


async def main(subject="german", item_id="a1-1.myself.l1", band="A1"):
    entry = cache.load_baseline(subject, item_id, band)
    if entry is None:
        raise SystemExit(f"no cached lesson for {item_id}")

    state = {
        "material_blueprint": json.dumps(entry["blueprint"], ensure_ascii=False),
        "lesson_plan": json.dumps(entry["plan"], ensure_ascii=False),
        "diagnostic_report": json.dumps({"readiness": "ready"}),
    }
    print(f"blueprint: {len(state['material_blueprint']):,} chars, "
          f"{len(entry['blueprint'].get('slots', []))} slots, "
          f"focus={entry['blueprint'].get('focus')}")

    runner = InMemoryRunner(agent=language_material_agent, app_name="iso")
    session = await runner.session_service.create_session(
        app_name="iso", user_id="iso", state=state)

    calls, texts = [], 0
    try:
        async for event in runner.run_async(
                user_id="iso", session_id=session.id,
                new_message=types.Content(role="user", parts=[types.Part(
                    text=f"Write the material for {item_id}.")])):
            for part in (getattr(getattr(event, "content", None), "parts", None) or []):
                if getattr(part, "function_call", None):
                    calls.append(part.function_call.name)
                elif getattr(part, "text", None):
                    texts += 1
                    print(f"  TEXT {len(part.text)} chars: {part.text[:200]!r}")
            for field in ("error_message", "error_code", "finish_reason"):
                value = getattr(event, field, None)
                if value:
                    print(f"  {field}: {value}")
    except Exception:
        traceback.print_exc()

    print(f"\ntool calls ({len(calls)}): {calls}")
    print(f"plain text events: {texts}")
    final = (await runner.session_service.get_session(
        app_name="iso", user_id="iso", session_id=session.id)).state
    written = final.get("material_package")
    print(f"material_package: {'MISSING' if written is None else f'{len(str(written)):,} chars'}")


asyncio.run(main(*(sys.argv[1:] or [])))
