"""Run the whole preparation pipeline as ONE ADK workflow against Firestore."""
import asyncio, json, sys
from google.adk.runners import InMemoryRunner
from google.genai import types
from zanoba_agent.agents import curriculum_agent as ca, diagnostic_agent as da
from zanoba_agent.workflows.preparation import (
    preparation_workflow, PLACEMENT_KEY, DIAGNOSIS_KEY, OBJECTIVES_KEY)
from zanoba_agent.store.history import FirestoreLessonHistory
from zanoba_agent.store.profiles import FirestoreProfileStore

P = "ai-tutor-zanoba"
h, pr = FirestoreLessonHistory(project=P), FirestoreProfileStore(project=P)
ca.set_history_store(h); da.set_stores(pr, h)

async def main(student="stu-demo-1", subject="german", level="a1-1"):
    runner = InMemoryRunner(agent=preparation_workflow, app_name="zanoba")
    session = await runner.session_service.create_session(app_name="zanoba", user_id=student)
    msg = types.Content(role="user", parts=[types.Part(
        text=f"student_id={student}, subject={subject}, level_id={level}. "
             f"Prepare the next 60-minute lesson.")])

    order = []
    async for ev in runner.run_async(user_id=student, session_id=session.id, new_message=msg):
        if ev.author and ev.author not in order and ev.author != "user":
            order.append(ev.author)

    final = await runner.session_service.get_session(
        app_name="zanoba", user_id=student, session_id=session.id)
    st = final.state
    print("node execution order:", " -> ".join(order), "\n")

    for key, label in ((PLACEMENT_KEY, "PLACEMENT"), (DIAGNOSIS_KEY, "DIAGNOSIS"),
                       (OBJECTIVES_KEY, "OBJECTIVES")):
        v = st.get(key)
        print(f"state[{key}] {'set' if v else 'MISSING'}")
        if not v: continue
        d = v if isinstance(v, dict) else json.loads(v)
        if label == "PLACEMENT":
            print(f"    -> {d['next_item_id']} \"{d['next_item_title']}\" focus={d['focus']} {d['completed_count']}/{d['total_count']}")
        elif label == "DIAGNOSIS":
            print(f"    -> readiness={d['readiness']} difficulty={d['recommended_difficulty']} review_first={d.get('review_first')}")
        else:
            tot = sum(x["estimated_minutes"] for x in d["objectives"])
            print(f"    -> {len(d['objectives'])} objectives, {tot}/50 min")
            for x in d["objectives"]:
                print(f"       [{'REVIEW' if x['is_review'] else 'NEW   '}] {x['estimated_minutes']:>2}min  {x['statement'][:78]}")
            if d.get("deferred"): print(f"       deferred: {len(d['deferred'])}")
        print()

asyncio.run(main(*(sys.argv[1:] or [])))
