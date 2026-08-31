"""Curriculum agent then Diagnostic agent, both against real Firestore data."""
import asyncio, json
from google.adk.runners import InMemoryRunner
from google.genai import types
from zanoba_agent.agents import curriculum_agent as ca, diagnostic_agent as da
from zanoba_agent.store.history import FirestoreLessonHistory
from zanoba_agent.store.profiles import FirestoreProfileStore

PROJECT = "ai-tutor-zanoba"
history = FirestoreLessonHistory(project=PROJECT)
profiles = FirestoreProfileStore(project=PROJECT)
ca.set_history_store(history)
da.set_stores(profiles, history)

async def run(agent, prompt):
    r = InMemoryRunner(agent=agent, app_name="z")
    s = await r.session_service.create_session(app_name="z", user_id="u")
    m = types.Content(role="user", parts=[types.Part(text=prompt)])
    out = None
    async for ev in r.run_async(user_id="u", session_id=s.id, new_message=m):
        if ev.is_final_response() and ev.content and ev.content.parts:
            out = "".join(p.text or "" for p in ev.content.parts)
    return json.loads(out)

async def main():
    sid = "stu-demo-1"
    p = await run(ca.curriculum_agent,
                  f"student_id={sid}, subject=german, level_id=a1-1. What should be taught next?")
    print("═══ CURRICULUM AGENT (Firestore history) ═══")
    print(f"  next     {p['next_item_id']}  \"{p['next_item_title']}\"  focus={p['focus']}")
    print(f"  progress {p['completed_count']}/{p['total_count']}   unmet={p['unmet_prerequisites']}")
    print()

    d = await run(da.diagnostic_agent,
                  f"student_id={sid}, subject=german, level_id=a1-1, "
                  f"target_item_id={p['next_item_id']}. What does this student actually know?")
    print("═══ DIAGNOSTIC AGENT (Firestore profile + history) ═══")
    print(f"  readiness   {d['readiness']}    difficulty={d['recommended_difficulty']}")
    print(f"  evidence    {d['evidence_lesson_count']} lessons")
    for k in ("mastered", "partially_mastered", "missing_prerequisites"):
        for i in d.get(k) or []:
            print(f"  {k:22} {i['item_id']:24} score={i['score']}")
    for m in d.get("misconceptions") or []:
        print(f"  misconception          {m['concept']} ({m['severity']}) — {m['description'][:56]}")
    for e in d.get("recurring_errors") or []:
        print(f"  recurring error        {e['tag']} x{e['count']}")
    print(f"  review_first {d.get('review_first')}")
    print(f"  reason      {d['reason'][:260]}")

asyncio.run(main())
