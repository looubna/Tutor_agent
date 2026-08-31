import asyncio, json
from google.adk.runners import InMemoryRunner
from google.genai import types
from zanoba_agent.agents.curriculum_agent import curriculum_agent, set_history_store
from zanoba_agent.curriculum.history import InMemoryLessonHistory

async def ask(prompt, label):
    set_history_store(InMemoryLessonHistory())   # no history at all
    runner = InMemoryRunner(agent=curriculum_agent, app_name="z")
    s = await runner.session_service.create_session(app_name="z", user_id="u")
    msg = types.Content(role="user", parts=[types.Part(text=prompt)])
    final, calls = None, []
    async for ev in runner.run_async(user_id="u", session_id=s.id, new_message=msg):
        for p in (ev.content.parts if ev.content else []) or []:
            if p.function_call: calls.append(p.function_call.name)
        if ev.is_final_response() and ev.content and ev.content.parts:
            final = "".join(p.text or "" for p in ev.content.parts)
    d = json.loads(final)
    print(f"--- {label} ---")
    print("  tools:", [c for c in calls if c != "set_model_response"])
    for k in ("next_item_id","next_item_title","granularity","focus","completed_count","total_count"):
        print(f"  {k}: {d.get(k)}")
    print("  reason:", d.get("reason","")[:190])
    print()

async def main():
    await ask("student_id=new-1, subject=german, level_id=a1-1. What should be taught next?",
              "brand-new student, German A1.1")
    await ask("student_id=new-2, subject=mathematics, level_id=fr.sixieme. What next?",
              "STEM, French Sixieme (units only)")

asyncio.run(main())
