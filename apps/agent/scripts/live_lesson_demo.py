"""Drive a short live lesson: the tutor teaches on the paper, the clock governs.

Offline apart from the model calls: the worksheet below stands in for the one
the material agents publish, so the demo shows what the student would see —
the page the tutor turned to, and the marks it made on it — without a database.
"""
import asyncio, json, os
from datetime import datetime, timedelta, timezone
from google.adk.runners import InMemoryRunner
from google.genai import types
from zanoba_agent.agents.live_tutor import live_tutor_agent, bind_session, session_surfaces
from zanoba_agent.live import state_machine as sm
from zanoba_agent.live.publish import MarksNotAccepted, publish_marks
from zanoba_agent.schemas.lesson_state import LessonState, ObjectiveProgress, Scheduled
from zanoba_agent.store.profiles import FirestoreProfileStore

NOW = datetime.now(timezone.utc)
state = LessonState(
    lesson_id="L-demo", student_id="stu-demo-1", subject="german", level_id="a1-1",
    target_item_id="a1-1.classroom.l3",
    scheduled=Scheduled(start_time=NOW, duration_minutes=60),
    objectives=[ObjectiveProgress(objective_id="o1", statement="I can name the three genders of German nouns."),
                ObjectiveProgress(objective_id="o2", statement="I can use der, die and das with classroom nouns.")])
plan = {"activities": [
    {"id":"a1","phase":"retrieval","title":"Spelling warm-up","minutes":10},
    {"id":"a2","phase":"discovery","title":"Spotting genders","minutes":10},
    {"id":"a3","phase":"explanation","title":"der, die, das","minutes":15}]}
material = {"items": [
    {"id":"m1","activity_id":"a3","kind":"explanation","title":"The three genders",
     "content":"German nouns are der (masculine), die (feminine) or das (neuter). Learn the article with the word.",
     "answer_key":"der Tisch, die Tür, das Fenster"}]}

# The paper the student is holding. In a real class this is the published
# LessonDoc for the booking; here it is inline so the demo runs offline.
paper = {"lessonId": "german.a1-1.classroom.l3", "version": 1, "title": "der, die, das",
         "slides": [
    {"id":"s1","title":"Wortschatz","blocks":[{"kind":"cards","cols":3,"items":[
        {"lead":"der Tisch"},{"lead":"die Tür"},{"lead":"das Fenster"}]}]},
    {"id":"s2","title":"Ergänze die Artikel","blocks":[
        {"kind":"exercise","skillId":"artikel","rows":[
            {"prompt":"___ Tisch","answer":"der"},
            {"prompt":"___ Tür","answer":"die"},
            {"prompt":"___ Fenster","answer":"das"}]}]},
    {"id":"s3","title":"Zusammenfassung","blocks":[{"kind":"goals","items":[
        "Ich kenne die drei Artikel."]}]}]}

sm.observe_presence(state, True, False, NOW)
sm.start_lesson(state, NOW)
bind_session(state, plan, material, paper=paper,
             profiles=FirestoreProfileStore(project="ai-tutor-zanoba"))

async def turn(runner, session, text, label):
    msg = types.Content(role="user", parts=[types.Part(text=text)])
    calls, said = [], []
    async for ev in runner.run_async(user_id="stu-demo-1", session_id=session.id, new_message=msg):
        for p in (ev.content.parts if ev.content else []) or []:
            if p.function_call: calls.append(p.function_call.name)
            if p.text and ev.is_final_response(): said.append(p.text)
    print(f"\n── {label}")
    print(f"   tools: {calls}")
    print(f"   tutor: {' '.join(said)[:260]}")
    # A mark is no use until it is on the student's paper, so it goes out at the
    # end of the turn that made it rather than at the end of the lesson.
    booking = os.environ.get("ZANOBA_DEMO_BOOKING")
    if booking:
        _, _, sheet = session_surfaces()
        try:
            print(f"   paper: sent {publish_marks(sheet, booking)} mark(s)")
        except MarksNotAccepted as exc:
            print(f"   paper: not sent — {exc}")

async def main():
    runner = InMemoryRunner(agent=live_tutor_agent, app_name="live")
    s = await runner.session_service.create_session(app_name="live", user_id="stu-demo-1")
    await turn(runner, s, "The student has just joined. Begin the lesson.", "lesson opens")
    await turn(runner, s, "Student says: 'die Tisch?'  (the correct article is der)", "wrong answer")
    wb, audio, sheet = session_surfaces()
    print("\n── state after two turns")
    print(f"   live_state {state.live_state} | activity {state.current_activity_id}")
    print(f"   whiteboard {[(a.op, a.content[:40]) for a in wb.snapshot()]}")
    print(f"   showing    page {sheet.showing or '(none)'}")
    for op in sheet.settled():
        detail = getattr(op, "text", None) or getattr(op, "words", "")
        print(f"   paper      {op.op:<7} on {op.on.box} · {detail}")
    print(f"   marks made {sheet.marks_made()}  (POST these to /api/lesson/<id>/marks)")
    print(f"   mistakes   {state.interaction.mistakes}")
    print(f"   objectives {[(o.objective_id,o.status) for o in state.objectives]}")
    # The clock, not the tutor, closes the lesson.
    sm.enforce_schedule(state, NOW + timedelta(minutes=61))
    print(f"\n── after the scheduled hour")
    print(f"   live_state {state.live_state} | status {state.status}")
    print(f"   unfinished {[o.objective_id for o in state.unfinished_objectives()]}")

asyncio.run(main())
