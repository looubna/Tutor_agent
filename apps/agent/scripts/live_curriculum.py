import asyncio, json
from datetime import datetime, timezone
from google.adk.runners import InMemoryRunner
from google.genai import types
from zanoba_agent.agents.curriculum_agent import curriculum_agent, set_history_store
from zanoba_agent.curriculum.history import CompletedLesson, InMemoryLessonHistory

# A student who has finished the opener and the first two classroom lessons.
set_history_store(InMemoryLessonHistory([
    CompletedLesson(lesson_id=i, subject="german", level_id="a1-1",
                    completed_at=datetime(2026, 8, d, tzinfo=timezone.utc))
    for d, i in [(1, "a1-1.get-started.l1"), (3, "a1-1.classroom.l1"), (5, "a1-1.classroom.l2")]
]))

async def main():
    runner = InMemoryRunner(agent=curriculum_agent, app_name="zanoba")
    session = await runner.session_service.create_session(app_name="zanoba", user_id="stu-1")
    msg = types.Content(role="user", parts=[types.Part(
        text="student_id=stu-1, subject=german, level_id=a1-1. What should be taught next?")])
    final, calls = None, []
    async for ev in runner.run_async(user_id="stu-1", session_id=session.id, new_message=msg):
        for p in (ev.content.parts if ev.content else []) or []:
            if p.function_call: calls.append(p.function_call.name)
        if ev.is_final_response() and ev.content and ev.content.parts:
            final = "".join(p.text or "" for p in ev.content.parts)
    print("tool calls:", calls)
    print()
    print(json.dumps(json.loads(final), indent=2)[:1400])

asyncio.run(main())
