import uuid

from google.adk import Agent, Event
from google.adk.runners import InMemoryRunner
from google.genai import types

MATH_TUTOR_INSTRUCTION = """\
You are a friendly, patient AI Math tutor leading a live, one-on-one video lesson \
with a student. Your replies are spoken out loud by an avatar, word for word, so:

- Write in plain, natural spoken language. Never use markdown, bullet points, \
  asterisks, headers, or LaTeX — say math the way a person would say it out loud \
  (e.g. "x squared plus one", not "x^2 + 1" or "$x^2+1$").
- Keep each reply short and conversational (1-4 sentences at a time), like a real \
  tutor talking, not a wall of text.
- Don't just hand over answers. Ask guiding questions, give hints, and let the \
  student do the solving. Confirm understanding before moving on.
- Adapt to the student's apparent level based on how they talk about the problem.
- Be warm and encouraging, especially when the student is stuck or gets something \
  wrong. Normalize mistakes as part of learning.
- If the student greets you or the conversation is just starting, briefly ask what \
  they'd like to work on today.
"""

TUTOR_AGENT_NAME = "math_tutor"
APP_NAME = "mentora-tutor-agent"

tutor_agent = Agent(
    name=TUTOR_AGENT_NAME,
    model="gemini-3.5-flash",
    instruction=MATH_TUTOR_INSTRUCTION,
)

runner = InMemoryRunner(tutor_agent, app_name=APP_NAME)


async def respond(subject: str, history: list[dict[str, str]]) -> str:
    """Runs one tutoring turn. `history` is the full ordered conversation so
    far, including the latest student utterance as its last entry. Each call
    uses a fresh in-memory session and replays history into it — our own DB
    (not ADK) is the source of truth for conversation state, so this keeps
    the agent stateless and unable to desync from it."""
    if not history or history[-1]["role"] != "student":
        raise ValueError("history must end with a student turn")

    session_id = str(uuid.uuid4())
    session = await runner.session_service.create_session(
        app_name=APP_NAME, user_id=session_id, session_id=session_id
    )

    for turn in history[:-1]:
        role = "user" if turn["role"] == "student" else "model"
        author = "user" if role == "user" else TUTOR_AGENT_NAME
        await runner.session_service.append_event(
            session,
            Event(
                author=author,
                content=types.Content(role=role, parts=[types.Part(text=turn["content"])]),
            ),
        )

    new_message = types.Content(
        role="user", parts=[types.Part(text=history[-1]["content"])]
    )

    reply_text = ""
    async for event in runner.run_async(
        user_id=session_id, session_id=session_id, new_message=new_message
    ):
        if event.is_final_response() and event.content and event.content.parts:
            reply_text = event.content.parts[0].text or ""

    return reply_text.strip()
