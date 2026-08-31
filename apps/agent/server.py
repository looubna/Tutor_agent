"""HTTP service for the tutoring agents. Runs on Cloud Run.

Two halves, and they run on different clocks.

`POST /prepare` is the slow one: a student, a subject and a level go in, the
whole preparation graph runs, and the artifacts it produces come out. Minutes,
paid once, ahead of the class.

`POST /lesson/turn` is the live one: one turn of one lesson, taken while a
student waits. It resolves the prepared lesson from the cache rather than
building it, fetches the paper from the web app, runs the tutor for a turn, and
posts whatever the tutor wrote back onto the student's copy before it answers.
Seconds, and the student is watching.

Everything the agents read — curriculum from disk, profile and history from
Firestore — is resolved server-side, so a caller needs to know nothing but who
the student is and which class this is.
"""

from __future__ import annotations

import asyncio
import base64
import contextlib
import json
import logging
import os
import re
import time
from datetime import datetime, timezone

from fastapi import FastAPI, HTTPException, WebSocket, WebSocketDisconnect
from google.adk.agents.live_request_queue import LiveRequestQueue
from google.adk.runners import InMemoryRunner
from google.genai import types
from pydantic import BaseModel, Field

from zanoba_agent.agents import curriculum_agent as _ca
from zanoba_agent.agents import diagnostic_agent as _da
from zanoba_agent.agents import planner_tools as _pt
from zanoba_agent.agents.live_tutor import (
    bind_session, clear_beats, lesson_briefing, spoken_tutor, turn_beats)
from zanoba_agent.curriculum import repository as _curriculum
from zanoba_agent.live import state_machine as sm
from zanoba_agent.live import tickets
from zanoba_agent.live.audio import (
    INPUT_MIME, LIVE_MODEL, LIVE_VOICE, language_note, live_run_config)
from zanoba_agent.live.paper import LivePaper
from zanoba_agent.live.publish import MarksNotAccepted, NoPaper, fetch_sheet, publish_marks
from zanoba_agent.live.session import LessonRegistry, LiveLesson
from zanoba_agent.schemas.lesson_state import (
    LessonState, ObjectiveProgress, Scheduled)
from zanoba_agent.store.history import FirestoreLessonHistory
from zanoba_agent.store.profiles import FirestoreProfileStore
from zanoba_agent.workflows.serving import prepare_for_student
from zanoba_agent.workflows.preparation import (
    DIAGNOSIS_KEY,
    OBJECTIVES_KEY,
    PLACEMENT_KEY,
    MATERIAL_KEY,
    PLAN_KEY,
    QUALITY_KEY,
    preparation_workflow,
)

PROJECT = os.environ.get("GOOGLE_CLOUD_PROJECT", "ai-tutor-zanoba")
MODEL = os.environ.get("ZANOBA_MODEL", "gemini-3.5-flash")
APP_NAME = "zanoba"

# Wired once at import. Firestore clients are lazy, so this costs nothing until
# a request actually arrives.
_history = FirestoreLessonHistory(project=PROJECT)
_profiles = FirestoreProfileStore(project=PROJECT)
_ca.set_history_store(_history)
_da.set_stores(_profiles, _history)
_pt.set_stores(_profiles, _history)

app = FastAPI(
    title="Zanoba tutoring agents",
    description="Prepares a 60-minute 1-to-1 lesson from curriculum and student evidence.",
    version="0.1.0",
)


class PrepareRequest(BaseModel):
    student_id: str
    subject: str = Field(description='e.g. "german" or "mathematics"')
    level_id: str = Field(description='e.g. "a1-1" or "fr.sixieme"')


class PrepareResponse(BaseModel):
    student_id: str
    subject: str
    level_id: str
    nodes_run: list[str]
    elapsed_seconds: float
    placement: dict | None = None
    diagnosis: dict | None = None
    objectives: dict | None = None
    plan: dict | None = None
    material: dict | None = None
    quality: dict | None = None


def _as_dict(value) -> dict | None:
    """State values arrive as a dict or as the JSON string the model emitted."""
    if value is None:
        return None
    if isinstance(value, dict):
        return value
    try:
        return json.loads(value)
    except (TypeError, ValueError):
        return {"raw": str(value)}


@app.get("/health")
def health() -> dict:
    """Liveness, plus enough to tell which build is running."""
    return {
        "status": "ok",
        "project": PROJECT,
        "model": MODEL,
        "pipeline": preparation_workflow.name,
        "nodes": [n.name for n in preparation_workflow.graph.nodes],
        "live_lessons": len(_lessons),
        "live_model": LIVE_MODEL,
        "live_voice": LIVE_VOICE,
        # Whether this instance can actually reach a student's paper. A tutor
        # that cannot is still a tutor, but it teaches without writing anything
        # down, and that is worth seeing on the health check rather than
        # discovering mid-lesson.
        "paper_reachable": bool(os.environ.get("ZANOBA_WEB_URL")
                                and os.environ.get("AGENT_TOKEN")),
    }


@app.post("/prepare", response_model=PrepareResponse)
async def prepare(request: PrepareRequest) -> PrepareResponse:
    """Run the preparation pipeline for one lesson."""
    started = time.monotonic()
    runner = InMemoryRunner(agent=preparation_workflow, app_name=APP_NAME)
    session = await runner.session_service.create_session(
        app_name=APP_NAME, user_id=request.student_id
    )
    message = types.Content(
        role="user",
        parts=[
            types.Part(
                text=(
                    f"student_id={request.student_id}, subject={request.subject}, "
                    f"level_id={request.level_id}. Prepare the next 60-minute lesson."
                )
            )
        ],
    )

    nodes_run: list[str] = []
    async for event in runner.run_async(
        user_id=request.student_id, session_id=session.id, new_message=message
    ):
        if event.author and event.author != "user" and event.author not in nodes_run:
            nodes_run.append(event.author)

    final = await runner.session_service.get_session(
        app_name=APP_NAME, user_id=request.student_id, session_id=session.id
    )
    state = final.state if final else {}

    return PrepareResponse(
        student_id=request.student_id,
        subject=request.subject,
        level_id=request.level_id,
        nodes_run=nodes_run,
        elapsed_seconds=round(time.monotonic() - started, 2),
        placement=_as_dict(state.get(PLACEMENT_KEY)),
        diagnosis=_as_dict(state.get(DIAGNOSIS_KEY)),
        objectives=_as_dict(state.get(OBJECTIVES_KEY)),
        plan=_as_dict(state.get(PLAN_KEY)),
        material=_as_dict(state.get(MATERIAL_KEY)),
        quality=_as_dict(state.get(QUALITY_KEY)),
    )


# ── the live lesson ─────────────────────────────────────────────────────────
#
# `/prepare` builds a lesson. This teaches one.
#
# A turn carries the whole identity of the class, not just a booking id, so an
# instance that has never seen this booking starts the lesson instead of
# refusing it. That is what makes the endpoint safe to put behind a load
# balancer at all — see `live/session.py` for what is and is not preserved when
# that happens, and run with session affinity so it stays the rare case.

_log = logging.getLogger(__name__)
# Uvicorn configures the root logger for itself, which leaves this module's INFO
# lines with nowhere to go — and a live session that produces nothing then looks
# identical to one nobody opened. ZANOBA_LIVE_DEBUG=1 turns them back on.
if os.environ.get("ZANOBA_LIVE_DEBUG"):
    logging.basicConfig(level=logging.INFO, force=True,
                        format="%(asctime)s %(levelname)s %(name)s: %(message)s")
    _log.setLevel(logging.INFO)

_lessons = LessonRegistry()

# How long to wait for the live model to say anything at all before giving up on
# it. The Gemini live models are previews and their connection sometimes hangs:
# ADK logs "Trying to connect to live model" and then nothing arrives, ever. A
# student sitting in silence cannot tell that from a tutor thinking, so the wait
# is bounded and the browser is told, which is what lets it fall back to typing.
LIVE_FIRST_EVENT_SECONDS = float(os.environ.get("ZANOBA_LIVE_TIMEOUT", "20"))

# The tutor's tools reach their lesson through module-level state in
# `live_tutor`, so two lessons cannot be bound at once in one process. This lock
# is what makes that safe: a turn binds and runs while holding it, and the next
# turn waits. It serialises turns across students on one instance, which at the
# scale this runs at costs a queue of seconds and buys the absence of a class of
# bug where one student's answer is marked on another student's paper.
_turn_lock = asyncio.Lock()

# One runner per lesson, built when the lesson opens.
#
# It used to be a single shared runner on the full text tutor, whose instruction
# opens "start every turn by calling get_lesson_status" — so every answer cost
# four or five round trips to the model before a word came back, and the student
# sat there for ten seconds. The tutor is briefed instead now: what those tools
# returned does not change between one sentence and the next, so it is written
# into the instruction once and the tutor keeps only the tools that DO
# something. Same answer, a fraction of the wait.
def _who_you_are_teaching(request: "TurnRequest") -> str:
    """The student, in the words a tutor would already have in their head."""
    name = request.student_name.strip() or "the student"
    if request.lessons_so_far <= 0:
        return (f"\n\nWHO YOU ARE TEACHING\n"
                f"{name}. This is your FIRST lesson together — you have never "
                f"met. Do not open by launching into the syllabus. Greet them by "
                f"name, say who you are in a sentence, and spend the first "
                f"minute finding out about them: what year they are in, how "
                f"they get on with this subject, what they find hard, what they "
                f"want out of these lessons. Two or three questions, one at a "
                f"time, and listen to the answers — they tell you how to pitch "
                f"the hour. Then begin.")
    return (f"\n\nWHO YOU ARE TEACHING\n"
            f"{name}. You have taught them {request.lessons_so_far} time(s) "
            f"before, so greet them by name like someone you know."
            + (f"\nLast time you worked on: {request.last_lesson}. Open by "
               f"saying so and asking how it has sat with them since — one "
               f"question, then move on to today."
               if request.last_lesson else ""))


def _runner_for(lesson: LiveLesson, language: str, who: str = "") -> InMemoryRunner:
    if lesson.runner is None:
        lesson.runner = InMemoryRunner(
            agent=spoken_tutor(MODEL, language_note(language),
                           who + lesson_briefing()),
            app_name=APP_NAME)
    return lesson.runner


class TurnRequest(BaseModel):
    """One turn of one lesson, plus enough to start it if it is not running."""

    booking_id: str
    student_id: str
    subject: str = Field(description='e.g. "german" or "mathematics"')
    level_id: str = Field(description='e.g. "a1-1" or "fr.sixieme"')
    item_id: str = Field(
        default="",
        description="The curriculum lesson being taught, e.g. "
        '"a1-1.classroom.l3". Empty teaches from the paper alone.')
    start_time: datetime = Field(description="When the booked hour starts.")
    duration_minutes: int = 60

    student_name: str = Field(
        default="", description="What to call the student. A tutor who has "
        "taught you before knows your name.")
    lessons_so_far: int = Field(
        default=0, description="Completed lessons in this subject. Zero means "
        "this is the first time they have met.")
    last_lesson: str = Field(
        default="", description='What the previous lesson covered and when, '
        'e.g. "Comparer et ranger les décimaux, mardi dernier".')

    language: str = Field(
        default="",
        description="BCP-47 tag the class is spoken in, e.g. \"fr-FR\".")

    student_work: str = Field(
        default="",
        description="What the student has written on their paper, as a base64 "
        "PNG of their own handwriting. The tutor is shown it: a student who "
        "works on the page rather than saying the answer out loud is still "
        "answering, and a tutor that cannot see the page is marking blind.")

    student_said: str = Field(
        default="",
        description="What the student just said. Empty means they have only "
        "just joined and the tutor should open the lesson.")
    student_present: bool = True
    additional_person_detected: bool = False


class TurnResponse(BaseModel):
    booking_id: str
    started: bool = Field(description="True when this turn opened the lesson.")
    said: str = Field(description="What the tutor says this turn.")
    tools_called: list[str] = Field(default_factory=list)
    beats: list[dict] = Field(
        default_factory=list,
        description="The turn as a sequence of moments: what was said, and the "
        "line written while it was being said. Replayed in order, so the "
        "student watches the working appear as they hear it.")

    live_state: str
    status: str
    minutes_remaining: float
    lesson_over: bool

    paper_available: bool
    showing_page: str | None = None
    board: list[str] = Field(
        default_factory=list,
        description="Lines on the shared whiteboard, in the order written.")
    showing_material: dict | None = Field(
        default=None,
        description="The material item the tutor has put on the student's "
        "screen, if any. Answer keys are never in here.")
    marks_made: int = 0
    marks_published: int = 0

    objectives: list[dict] = Field(default_factory=list)
    notes: list[str] = Field(
        default_factory=list,
        description="Anything that went wrong but did not stop the lesson — a "
        "paper that could not be fetched, marks that could not be sent.")


# Things a model emits that are not words.
#
# Placeholders ("_", "."), and internal-looking tokens — `sf_first_turn_done`
# turned up as a whole reply and was read aloud at a child as one word. If it
# has no spaces and looks like an identifier, it is not a sentence.
_NOT_SPEECH = re.compile(r"^[a-z0-9_]+$")


def _own_words(said: str, student_name: str) -> str:
    """Drop anything the model wrote as the student.

    It answers its own question in their voice — "celine: Je suis en 6ème..." —
    and read aloud that is the tutor telling a child what they think. Only a
    turn that opens in someone else's name is cut; a colon inside a sentence is
    ordinary punctuation.
    """
    first = said.lstrip().split("\n", 1)[0]
    speaker = re.match(r"^\s*([\w' -]{1,24}):\s", first)
    if not speaker:
        return said
    who = speaker.group(1).strip().lower()
    if who in {student_name.strip().lower(), "student", "élève", "eleve"} or (
            student_name and who in student_name.strip().lower()):
        _log.warning("dropped a reply written in the student's voice: %r", first[:60])
        return ""
    return said


def _is_not_speech(said: str) -> bool:
    trimmed = said.strip(" _.-…\t\n")
    if len(trimmed) < 2:
        return True
    return bool(_NOT_SPEECH.match(trimmed)) and " " not in trimmed


def _now() -> datetime:
    return datetime.now(timezone.utc)


def _objectives_from(prepared: dict, subject: str = "", item_id: str = "") -> list[ObjectiveProgress]:
    """What the student should be able to do by the end of the hour.

    Three sources, in order of how much they know about this student.

    The prepared lesson is best: its objectives were written against this
    learner's diagnosis. Failing that, the curriculum item's own can-do
    outcomes — every authored lesson has them, and "Je sais comparer deux
    nombres décimaux" is a real goal for the hour even when nothing has been
    prepared. Only when there is neither does it fall back to the paper, which
    is a goal in the shape of an instruction and the weakest of the three.

    The middle case is what makes a syllabus teachable the day it is loaded,
    rather than after a pipeline has been run over every lesson in it.
    """
    listed = ((prepared.get("objectives") or {}).get("objectives")) or []
    if listed:
        return [
            ObjectiveProgress(objective_id=o.get("id", f"o{i + 1}"),
                              statement=o.get("statement", ""))
            for i, o in enumerate(listed)
        ]

    if subject and item_id:
        try:
            item = _curriculum.find_item(subject, item_id)
        except Exception:
            item = None
        if item and item.objectives:
            return [
                ObjectiveProgress(objective_id=f"o{i + 1}", statement=outcome)
                for i, outcome in enumerate(item.objectives)
            ]

    return [ObjectiveProgress(objective_id="o1",
                              statement="Work through this lesson's paper.")]


def _begin(request: TurnRequest, notes: list[str]) -> LiveLesson:
    """Open a lesson: find what was prepared, fetch the paper, set the clock.

    Nothing here is allowed to fail the lesson. A cold cache means teaching from
    the paper alone, which is the document the lesson was written as anyway; an
    unreachable paper means teaching without one and saying so. A student who
    has joined a call gets a lesson.
    """
    prepared: dict = {}
    if request.item_id:
        try:
            band = _curriculum.band_of(request.subject, request.level_id)
            served = prepare_for_student(
                request.subject, request.item_id, band, request.student_id)
            prepared = served.get("lesson") or {}
            if served["status"] == "miss":
                notes.append(
                    "No prepared lesson was cached for this class, so the tutor "
                    "teaches from the curriculum's own outcomes and whatever "
                    "paper exists. Warm it with scripts/warm_lessons.py.")
        except Exception as exc:  # a cold cache must not cost a class
            notes.append(f"Could not load the prepared lesson: {exc}")

    try:
        paper = LivePaper(fetch_sheet(request.booking_id))
    except NoPaper as exc:
        notes.append(str(exc))
        paper = LivePaper()

    state = LessonState(
        lesson_id=request.booking_id,
        student_id=request.student_id,
        subject=request.subject,
        level_id=request.level_id,
        target_item_id=request.item_id,
        scheduled=Scheduled(start_time=request.start_time,
                            duration_minutes=request.duration_minutes),
        objectives=_objectives_from(prepared, request.subject, request.item_id),
    )
    return _lessons.put(LiveLesson(
        booking_id=request.booking_id,
        state=state,
        plan=prepared.get("plan") or {},
        material=prepared.get("material") or {},
        paper=paper,
    ))


def _opening_prompt(lesson: LiveLesson, request: TurnRequest) -> str:
    """What the tutor is told at the start of a turn.

    The student's own words where there are any. Where there are none, the fact
    that they have just arrived — which is a different instruction from silence,
    and the tutor should greet rather than wait.
    """
    if request.student_said.strip():
        return f"The student says: {request.student_said.strip()}"
    if request.student_work:
        return ("The student has written something on their paper and said "
                "nothing. Look at it and respond to what they wrote.")
    if not request.student_present:
        return ("The student is not in front of the camera. Do not teach to an "
                "empty room.")
    return ("The student has just joined and has not spoken yet. Open the "
            "lesson: greet them, say what the hour is for, and put the first "
            "page of the paper in front of them.")


# Reading the student's page is its own step, not something the tutor is asked
# to remember to do.
#
# Handing the picture to the tutor along with everything else did not work: it
# has a plan, a briefing, eleven tools and a conversation to keep up with, and
# the page went unlooked-at — twice it answered something else entirely, once it
# said nothing at all. The same model reads the same handwriting perfectly when
# that is the only thing it is asked to do. So it is asked separately, and the
# tutor is told in words what the student wrote.
# One client, made on first use and kept. Building one per call is what the
# async path was doing, and it is what broke it.
_genai_client = None


def _genai():
    global _genai_client
    if _genai_client is None:
        from google import genai

        _genai_client = genai.Client()
    return _genai_client


_READER = "Transcribe the handwriting in this image, exactly as written.\n" \
          "Reply with the transcription and nothing else — no preamble, no " \
          "quotation marks, no explanation.\n" \
          "If there is nothing written, or you cannot read it, reply with the " \
          "single word NOTHING."


async def _read_the_page(work: str) -> str:
    """What the student has written, as text. Empty when there is nothing."""
    if not work:
        return ""
    try:
        raw = base64.b64decode(work.split(",", 1)[-1])
    except (ValueError, TypeError):
        return ""

    def _ask() -> str:
        # The SYNC client, on a thread. The async one builds a fresh aiohttp
        # session per call and then trips over its own connector
        # ("assert self._connector is not None") from inside a request handler;
        # the sync client has none of that machinery and simply works.
        response = _genai().models.generate_content(
            model=MODEL,
            contents=types.Content(role="user", parts=[
                types.Part(text=_READER),
                types.Part(inline_data=types.Blob(data=raw, mime_type="image/png")),
            ]),
        )
        return (response.text or "").strip()

    try:
        read = await asyncio.to_thread(_ask)
    except Exception as exc:
        # Never a reason to lose the turn: the tutor answers without having
        # seen the page, which is a worse lesson, not a broken one.
        _log.warning("could not read the student's page: %s", exc)
        return ""

    return "" if read.upper().startswith("NOTHING") else read


async def _run_turn(lesson: LiveLesson, prompt: str, language: str = "",
                    who: str = "") -> tuple[str, list[str]]:
    """Run the tutor for one turn. Returns what it said and what it called."""
    runner = _runner_for(lesson, language, who)
    if not lesson.adk_session_id:
        session = await runner.session_service.create_session(
            app_name=APP_NAME, user_id=lesson.state.student_id)
        lesson.adk_session_id = session.id

    parts = [types.Part(text=prompt)]
    message = types.Content(role="user", parts=parts)
    tools: list[str] = []
    final: list[str] = []
    async for event in runner.run_async(
        user_id=lesson.state.student_id,
        session_id=lesson.adk_session_id,
        new_message=message,
    ):
        for part in (event.content.parts if event.content else []) or []:
            if part.function_call:
                tools.append(part.function_call.name)
            if part.text and event.is_final_response():
                final.append(part.text)
    return " ".join(t.strip() for t in final if t.strip()), tools


@app.post("/lesson/turn", response_model=TurnResponse)
async def lesson_turn(request: TurnRequest) -> TurnResponse:
    """Take one turn of a live lesson.

    The order matters. Presence and the clock are settled first, by the state
    machine, because whether the hour is over is not the tutor's to decide and
    asking a model would add a way to get it wrong. Then the tutor teaches. Then
    whatever it wrote goes onto the student's paper — before the response
    returns, so the browser polling for marks and the reply it is reading arrive
    in the right order.
    """
    notes: list[str] = []
    now = _now()

    async with _turn_lock:
        lesson = _lessons.get(request.booking_id)
        started = lesson is None
        if lesson is None:
            lesson = _begin(request, notes)

        # The clock and the camera, before anything a model says.
        sm.observe_presence(lesson.state, request.student_present,
                            request.additional_person_detected, now)
        if lesson.state.live_state == "STUDENT_DETECTED":
            sm.start_lesson(lesson.state, now)
        sm.enforce_schedule(lesson.state, now)

        if lesson.state.live_state == "LESSON_END":
            _lessons.close(request.booking_id)
            _lessons.sweep()
            return _response(lesson, started=started, said="", tools=[], sent=0,
                             notes=notes + ["The booked hour is over."])

        if lesson.state.live_state == "STUDENT_ABSENT":
            # Nobody to teach. Waiting costs nothing; a model turn spent saying
            # so costs money and produces a tutor talking to an empty room.
            return _response(lesson, started=started, said="", tools=[], sent=0,
                             notes=notes + ["The student is away from the camera."])

        bind_session(lesson.state, lesson.plan, lesson.material,
                     profiles=_profiles, audio=lesson.audio,
                     paper=lesson.paper, stage=lesson.stage, board=lesson.board)

        if request.student_said.strip():
            lesson.audio.hear(request.student_said.strip())

        clear_beats()
        # Where the transcript stood before this turn, so what the tutor says
        # now can be reported exactly rather than as a guess at a window of it.
        spoken_before = len(lesson.audio.transcript())

        prompt = _opening_prompt(lesson, request)
        written = await _read_the_page(request.student_work)
        if written:
            lesson.audio.hear(f"(written on the paper) {written}")
            prompt += (
                f"\n\nThe student has just WRITTEN this on their paper, in their "
                f"own handwriting:\n\n    {written}\n\n"
                "Respond to it. Say what they have written, then mark it: "
                "fill_in_gap or circle_on_paper green if it is right; "
                "circle_on_paper red and write_on_paper the correction if it is "
                "not. Never ask them to say aloud what they have already "
                "written down in front of you.")

        try:
            final, tools = await _run_turn(lesson, prompt, request.language,
                                           _who_you_are_teaching(request))
        except Exception as exc:
            _log.exception("turn failed for booking %s", request.booking_id)
            raise HTTPException(
                status_code=502,
                detail=f"The tutor could not take this turn: {exc}") from exc

        # Speech has exactly one channel per turn.
        #
        # The tutor speaks through `say` and `explain`, and the model also
        # produces a final response. Taking both doubles the turn, and worse:
        # a model that has already said everything through its tools will fill
        # the final response with whatever comes next in the dialogue — which
        # is the student's line. A real run produced a tutor that greeted the
        # class and then invented a student asking about quadratic equations.
        #
        # So the final response is a fallback, used only when the tutor spoke
        # through no tool at all. What it said through its tools is what it
        # said.
        # Only the TUTOR's utterances count. What the student said, and what
        # they wrote on the page, both land in the transcript too — counting
        # those made the tutor look like it had already spoken, and its actual
        # reply was dropped as a duplicate.
        spoke_through_tools = any(
            u.speaker == "tutor" for u in lesson.audio.transcript()[spoken_before:])
        if final and not spoke_through_tools:
            lesson.audio.speak(final)

        sent = 0
        try:
            sent = publish_marks(lesson.paper, request.booking_id)
        except MarksNotAccepted as exc:
            # The lesson continues. The marks are still queued, so the next turn
            # carries them rather than losing them.
            notes.append(str(exc))

        said = " ".join(
            u.text for u in lesson.audio.transcript()[spoken_before:]
            if u.speaker == "tutor"
        )
        # Anything explained on the paper is already in the beats, and the
        # browser speaks those as it draws them. Leaving it in `said` as well
        # would have the tutor say every line twice.
        # Page-turn beats carry no speech, so they are skipped rather than
        # exploding on a missing key.
        spoken_in_beats = {b["say"] for b in turn_beats() if "say" in b}
        if spoken_in_beats:
            said = " ".join(
                u.text for u in lesson.audio.transcript()[spoken_before:]
                if u.speaker == "tutor" and u.text not in spoken_in_beats
            )
        # A model that has put everything into tool calls sometimes returns a
        # placeholder — "_", ".", "ok" — as its reply. Read aloud that is a
        # noise, and in the transcript it is a line of nothing. Better to say
        # plainly that it did not speak than to hand the student a grunt.
        said = _own_words(said, request.student_name)
        if _is_not_speech(said):
            said = ""

        # It acted and said nothing.
        #
        # A tutor that marks the paper in silence has done the work and left
        # the student with no idea it happened — they are looking at the page
        # waiting to be spoken to. Rather than invent words for it, it is asked
        # to say what it just did. One extra round trip, and only when the turn
        # would otherwise be silent.
        if not said and tools:
            _log.info("turn %s: acted (%s) without speaking; asking for words",
                      request.booking_id, ", ".join(tools))
            try:
                again, _ = await _run_turn(
                    lesson,
                    "You did that without saying anything, so the student heard "
                    "silence. Say it now, in one or two sentences: what you just "
                    "wrote or turned to, and what they should do next. Words "
                    "only — do not call another tool.",
                    request.language)
                said = again if len(again.strip(" _.-…\t\n")) >= 2 else ""
            except Exception:
                _log.warning("turn %s: could not recover a spoken reply",
                             request.booking_id)

        return _response(lesson, started=started, said=said, tools=tools,
                         sent=sent, notes=notes, beats=turn_beats())


def _response(lesson: LiveLesson, *, started: bool, said: str,
              tools: list[str], sent: int, notes: list[str],
              beats: list[dict] | None = None) -> TurnResponse:
    state = lesson.state
    return TurnResponse(
        booking_id=lesson.booking_id,
        started=started,
        said=said,
        tools_called=tools,
        beats=beats or [],
        live_state=state.live_state,
        status=state.status,
        minutes_remaining=round(state.minutes_remaining(_now()), 1),
        lesson_over=state.live_state == "LESSON_END",
        paper_available=lesson.paper.is_open,
        showing_page=lesson.paper.showing or None,
        showing_material=lesson.stage.showing(),
        board=lesson.board_lines(),
        marks_made=lesson.paper.marks_made(),
        marks_published=sent,
        objectives=[{"id": o.objective_id, "statement": o.statement,
                     "status": o.status} for o in state.objectives],
        notes=notes,
    )


# ── the spoken lesson ───────────────────────────────────────────────────────
#
# The same class as `/lesson/turn`, heard instead of read. The browser opens
# this socket directly rather than through the web app, because putting another
# hop in front of every 20ms of PCM buys nothing; it presents a ticket the web
# app signed, which is how a socket with no cookie knows whose lesson it is.


class LiveHello(BaseModel):
    """The first frame: who this is, and proof the web app said so."""

    ticket: str
    booking_id: str
    student_id: str
    subject: str = ""
    level_id: str = ""
    item_id: str = ""
    start_time: datetime
    duration_minutes: int = 60
    # BCP-47, from the web app's `speechLocale`. A native-audio model takes no
    # language code, so this reaches the model through its instruction.
    language: str = ""


async def _send(websocket: WebSocket, payload: dict) -> None:
    with contextlib.suppress(RuntimeError, WebSocketDisconnect):
        await websocket.send_json(payload)


@app.websocket("/lesson/live")
async def lesson_live(websocket: WebSocket) -> None:
    """Teach one lesson aloud.

    Three things run at once: the browser's microphone going in, the model's
    voice coming out, and the tutor's marks going onto the paper as it makes
    them. The marks are flushed on every event rather than at the end, because
    an hour is a long time to hold a student's worksheet hostage to a socket
    that might drop.
    """
    await websocket.accept()

    try:
        hello = LiveHello.model_validate(await websocket.receive_json())
    except Exception as exc:
        await _send(websocket, {"type": "error", "detail": f"Bad hello: {exc}"})
        await websocket.close(code=1008)
        return

    secret = os.environ.get("AGENT_TOKEN", "")
    try:
        if tickets.verify(hello.ticket, secret) != hello.booking_id:
            raise tickets.BadTicket("Ticket is for a different lesson.")
    except tickets.BadTicket as exc:
        await _send(websocket, {"type": "error", "detail": str(exc)})
        await websocket.close(code=1008)
        return

    notes: list[str] = []
    now = _now()
    lesson = _lessons.get(hello.booking_id)
    if lesson is None:
        lesson = _begin(TurnRequest(**hello.model_dump(exclude={"ticket", "language"}),
                                    student_said=""), notes)

    sm.observe_presence(lesson.state, True, False, now)
    if lesson.state.live_state == "STUDENT_DETECTED":
        sm.start_lesson(lesson.state, now)
    sm.enforce_schedule(lesson.state, now)
    if lesson.state.live_state == "LESSON_END":
        await _send(websocket, {"type": "closed", "detail": "The booked hour is over."})
        await websocket.close()
        return

    bind_session(lesson.state, lesson.plan, lesson.material, profiles=_profiles,
                 audio=lesson.audio, paper=lesson.paper, stage=lesson.stage,
                 board=lesson.board)

    runner = InMemoryRunner(
        # The briefing is read after bind_session, so it describes this lesson.
        agent=spoken_tutor(LIVE_MODEL, language_note(hello.language),
                           lesson_briefing()),
        app_name=APP_NAME)
    session = await runner.session_service.create_session(
        app_name=APP_NAME, user_id=hello.student_id)
    queue = LiveRequestQueue()

    await _send(websocket, {
        "type": "ready", "model": LIVE_MODEL, "voice": LIVE_VOICE,
        "language": hello.language, "paper_available": lesson.paper.is_open,
        "showing_page": lesson.paper.showing or None, "notes": notes,
    })

    # Open the hour, rather than waiting to be spoken to.
    #
    # A live model says nothing until something is said to it, and nothing ever
    # was: the socket opened, the queue sat empty, and the tutor waited for a
    # student who was waiting for the tutor. Twenty seconds later the watchdog
    # below called it a failed connection and the lesson fell back to typing —
    # so a spoken lesson that worked perfectly well never once made a sound.
    #
    # The typed lesson has always opened this way; the same words are used here
    # so a class begins the same whichever channel it is taught over.
    queue.send_content(types.Content(role="user", parts=[types.Part(
        text="The student has just joined and has not spoken yet. Open the "
             "lesson: greet them, say what the hour is for, and put the first "
             "page of the paper in front of them.")]))

    async def from_browser() -> None:
        """Microphone in. Binary frames are PCM; JSON frames are everything else."""
        while True:
            message = await websocket.receive()
            if message.get("type") == "websocket.disconnect":
                break
            chunk = message.get("bytes")
            if chunk:
                queue.send_realtime(types.Blob(data=chunk, mime_type=INPUT_MIME))
                continue
            text = message.get("text")
            if not text:
                continue
            try:
                body = json.loads(text)
            except ValueError:
                continue
            if body.get("type") == "text" and body.get("text"):
                # Typing still works during a spoken lesson: a student who
                # cannot say a word can write it.
                lesson.audio.hear(body["text"])
                queue.send_content(types.Content(
                    role="user", parts=[types.Part(text=body["text"])]))
            elif body.get("type") == "bye":
                break

    last_board: list[str] = []

    heard_from_model = asyncio.Event()
    spoke = False

    async def watchdog() -> None:
        """Say so if the model never speaks, rather than leaving a silent room."""
        try:
            await asyncio.wait_for(heard_from_model.wait(), LIVE_FIRST_EVENT_SECONDS)
        except asyncio.TimeoutError:
            _log.warning("live: %s produced nothing in %.0fs; giving up on audio",
                         LIVE_MODEL, LIVE_FIRST_EVENT_SECONDS)
            await _send(websocket, {
                "type": "error",
                "detail": "The spoken tutor could not be reached. The lesson "
                          "carries on — type to it instead.",
                "fallback": "text",
            })

    async def to_browser() -> None:
        """The tutor's voice out, and everything else it did on the way."""
        nonlocal last_board, spoke
        _log.info("live: opening model session for %s", hello.booking_id)
        async for event in runner.run_live(
            user_id=hello.student_id, session_id=session.id,
            live_request_queue=queue, run_config=live_run_config(hello.language),
        ):
            heard_from_model.set()
            _log.info("live event: author=%s parts=%s in=%s out=%s partial=%s",
                      getattr(event, "author", None),
                      [("audio" if p.inline_data else
                        "call:" + p.function_call.name if p.function_call else
                        "text") for p in ((event.content.parts if event.content else []) or [])],
                      bool(getattr(event, "input_transcription", None)),
                      bool(getattr(event, "output_transcription", None)),
                      getattr(event, "partial", None))
            for part in (event.content.parts if event.content else []) or []:
                if part.inline_data and part.inline_data.data:
                    spoke = True
                    await _send(websocket, {
                        "type": "audio",
                        "data": base64.b64encode(part.inline_data.data).decode(),
                    })
                if part.function_call:
                    await _send(websocket, {"type": "tool",
                                            "name": part.function_call.name})
                # A live model answers in text as well as audio — after a tool
                # call it often answers only in text. This branch was missing,
                # so those replies were dropped and the student was left with a
                # tutor that had answered into nowhere. Never drop the model's
                # output: if it cannot be heard it is at least read.
                if part.text and part.text.strip():
                    await _send(websocket, {"type": "transcript", "role": "TUTOR",
                                            "text": part.text, "final": True})

            # Barge-in. The student has started talking over the tutor, and the
            # browser is holding seconds of speech it has not played yet — so
            # the tutor would carry on with the old sentence and answer the new
            # question after it. That reads exactly like "I answered and it did
            # not continue": the reply is there, buried behind stale audio.
            if getattr(event, "interrupted", None):
                await _send(websocket, {"type": "interrupted"})

            # Transcriptions are what the transcript is made of; without them a
            # spoken lesson leaves nothing behind but audio nobody replays.
            # `partial` marks the running caption; the last one repeats the whole
            # turn, and the browser replaces rather than appends on that.
            if getattr(event, "input_transcription", None) and event.input_transcription.text:
                await _send(websocket, {"type": "transcript", "role": "STUDENT",
                                        "text": event.input_transcription.text,
                                        "final": not event.partial})
            if getattr(event, "output_transcription", None) and event.output_transcription.text:
                await _send(websocket, {"type": "transcript", "role": "TUTOR",
                                        "text": event.output_transcription.text,
                                        "final": not event.partial})

            if getattr(event, "turn_complete", None):
                await _send(websocket, {"type": "turn_complete"})

            # Whatever the tutor just wrote, onto the student's paper now.
            board_now = lesson.board_lines()
            if board_now != last_board:
                last_board = board_now
                await _send(websocket, {"type": "board", "lines": board_now})

            try:
                # What she is about to write, read before publishing consumes
                # it. The browser types these out a character at a time so the
                # student can follow the pen — the same thing the written
                # lesson does with its beats. Without it a spoken lesson only
                # ever reloads the paper, and a whole line appears at once on a
                # page the student was not watching.
                writing = [
                    {"text": op["text"], "on": (op.get("on") or {}).get("box", "")}
                    for op in lesson.paper.unsent()
                    if op.get("op") == "write" and op.get("text")
                ]
                if publish_marks(lesson.paper, hello.booking_id):
                    await _send(websocket, {
                        "type": "paper",
                        "showing_page": lesson.paper.showing or None,
                        "marks": lesson.paper.marks_made(),
                        "showing_material": lesson.stage.showing(),
                        "board": lesson.board_lines(),
                        "written": writing,
                    })
            except MarksNotAccepted:
                pass  # queued; the next event carries them

            if lesson.state.is_over(_now()):
                sm.enforce_schedule(lesson.state, _now())
                await _send(websocket, {"type": "closed",
                                        "detail": "The booked hour is over."})
                return

        # The model's stream ended. If it never actually spoke, the student has
        # been sitting in silence — which the live models do sometimes, ending a
        # turn after their tool calls without producing a word. Say so, so the
        # browser drops back to the typed lesson instead of waiting for a voice
        # that is not coming.
        if not spoke:
            _log.warning("live: %s ended without speaking for %s",
                         LIVE_MODEL, hello.booking_id)
            await _send(websocket, {
                "type": "error",
                "detail": "The spoken tutor stopped responding. The lesson "
                          "carries on — type to it instead.",
                "fallback": "text",
            })

    async def guarded(name, coro):
        try:
            await coro
        except asyncio.CancelledError:
            raise
        except Exception:
            _log.exception("live: %s failed for %s", name, hello.booking_id)
            raise

    incoming = asyncio.create_task(guarded("microphone", from_browser()))
    outgoing = asyncio.create_task(guarded("model", to_browser()))
    watching = asyncio.create_task(watchdog())
    try:
        # The watchdog is not raced, only cancelled in `finally`.
        #
        # It used to be one of the three, and finishing first is what ends this
        # wait — so the moment the tutor actually said something the watchdog
        # returned, and the two tasks doing the teaching were cancelled with it.
        # The lesson ended about a second and a half in: one audio frame, a
        # greeting the student never heard the end of, and a room that went
        # quiet. It was invisible for as long as the model never spoke, because
        # then the watchdog only ever finished by timing out, which was the
        # failure it was there to report. It reports; it does not decide when
        # the hour is over.
        done, pending = await asyncio.wait(
            {incoming, outgoing}, return_when=asyncio.FIRST_COMPLETED)
        for task in pending:
            task.cancel()
        for task in done:
            if task.exception():
                _log.exception("live lesson %s failed", hello.booking_id,
                               exc_info=task.exception())
                await _send(websocket, {"type": "error",
                                        "detail": str(task.exception())})
    finally:
        watching.cancel()
        queue.close()
        with contextlib.suppress(MarksNotAccepted):
            publish_marks(lesson.paper, hello.booking_id)
        with contextlib.suppress(Exception):
            await websocket.close()


@app.get("/lesson/{booking_id}")
def lesson_state(booking_id: str) -> dict:
    """Where a live lesson has got to, without taking a turn."""
    lesson = _lessons.get(booking_id)
    if lesson is None:
        raise HTTPException(status_code=404,
                            detail="This instance is not teaching that lesson.")
    state = lesson.state
    return {
        "booking_id": booking_id,
        "live_state": state.live_state,
        "status": state.status,
        "minutes_remaining": round(state.minutes_remaining(_now()), 1),
        "showing_page": lesson.paper.showing or None,
        "showing_material": lesson.stage.showing(),
        "board": lesson.board_lines(),
        "marks_made": lesson.paper.marks_made(),
        "transcript": lesson.transcript(),
        "objectives": [{"id": o.objective_id, "status": o.status}
                       for o in state.objectives],
        "observations": {
            "questions": state.interaction.questions_asked,
            "mistakes": state.interaction.mistakes,
            "successes": state.interaction.successful_answers,
            "misconceptions": state.interaction.misconceptions_observed,
        },
    }


@app.post("/lesson/{booking_id}/end")
async def end_lesson(booking_id: str) -> dict:
    """Close a lesson early — the student left the call.

    The clock closes a lesson on its own; this is for the student who leaves at
    forty minutes, so the hour is not held open waiting for turns that will not
    come. Any marks still queued go out first.
    """
    lesson = _lessons.get(booking_id)
    if lesson is None:
        raise HTTPException(status_code=404,
                            detail="This instance is not teaching that lesson.")
    notes = []
    try:
        publish_marks(lesson.paper, booking_id)
    except MarksNotAccepted as exc:
        notes.append(str(exc))

    sm.end_lesson(lesson.state, _now(), reason="the student left the call")
    _lessons.close(booking_id)
    _lessons.sweep()
    return {
        "booking_id": booking_id,
        "status": lesson.state.status,
        "minutes_taught": lesson.state.execution.actual_duration_minutes,
        "marks_made": lesson.paper.marks_made(),
        "unfinished_objectives": [o.objective_id
                                  for o in lesson.state.unfinished_objectives()],
        "notes": notes,
    }


@app.get("/debug/evidence")
def debug_evidence(student_id: str, subject: str) -> dict:
    """What the stores actually return from inside this container.

    Exists because a tool that returns an empty list and a tool that failed look
    identical in an agent's output — this separates them.
    """
    result: dict = {"project": PROJECT, "student_id": student_id, "subject": subject}
    try:
        profile = _profiles.get_student(student_id)
        result["profile_found"] = profile is not None
        if profile:
            learning = profile.for_subject(subject)
            result["subject_seen"] = learning is not None
            result["mastery_count"] = len(learning.mastery) if learning else 0
    except Exception as exc:  # surfaced deliberately, not swallowed
        result["profile_error"] = f"{type(exc).__name__}: {exc}"
    try:
        lessons = _history.completed_lessons(student_id, subject)
        result["history_count"] = len(lessons)
        result["history_ids"] = [x.lesson_id for x in lessons]
    except Exception as exc:
        result["history_error"] = f"{type(exc).__name__}: {exc}"
    return result
