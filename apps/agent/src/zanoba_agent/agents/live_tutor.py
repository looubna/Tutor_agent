"""The Live Tutor — one agent, teaching the lesson that was prepared.

One, not one per subject. There is no separate maths tutor and German tutor,
and no grammar tutor beside a reading tutor: the same teaching judgement runs
all of them, and what changes is the material, the plan and the student in front
of it. Splitting by subject would multiply the prompt without adding a decision
anybody makes differently.

What this agent does NOT own:
  - whether the hour is over        (the clock does)
  - whether the student is present  (the camera does)
  - which state the lesson is in    (the state machine does)

It owns what to say next, what to put on the board, when to explain again, and
when the plan needs bending. The plan is a plan, not a script — a student who
has understood in four minutes should not be held for ten, and one who has not
understood in ten should not be moved on because the plan said so.
"""

from __future__ import annotations

import os
from datetime import datetime, timezone

from google.adk.agents import LlmAgent

from ..live.paper import LivePaper, NoSuchPage, PaperNotOpen
from ..live.surfaces import (
    InMemoryAudio, InMemoryWhiteboard, LiveStage, WhiteboardAction)
from ..schemas.lesson_state import LessonState
from ..store.profiles import InMemoryProfileStore, ProfileStore

MODEL = os.environ.get("ZANOBA_MODEL", "gemini-3.5-flash")

# The live surfaces and the lesson being taught. Set per session by the runtime;
# module-level so the tools can reach them without threading state through every
# signature.
_state: LessonState | None = None
_material: dict = {}
_plan: dict = {}
_profiles: ProfileStore = InMemoryProfileStore()
_audio = InMemoryAudio()
_paper = LivePaper()
_stage = LiveStage()
_board = InMemoryWhiteboard()
# The turn as a sequence of moments rather than a lump: what was said, and what
# was written while it was being said. The runtime replays these in order, so
# the student watches a line appear as the tutor says it.
_beats: list[dict] = []


def bind_session(
    state: LessonState,
    plan: dict,
    material: dict,
    profiles: ProfileStore | None = None,
    audio=None,
    paper=None,
    stage=None,
    board=None,
) -> None:
    """Point the tutor's tools at one lesson.

    `paper` is the published worksheet for this lesson, either a `LivePaper` or
    the sheet JSON to wrap in one. Passing nothing gives an empty paper, and the
    paper tools then say so rather than inventing pages.
    """
    global _state, _plan, _material, _profiles, _audio, _paper, _stage, _board
    _state, _plan, _material = state, plan or {}, material or {}
    if profiles is not None:
        _profiles = profiles
    _audio = audio or InMemoryAudio()
    _paper = paper if isinstance(paper, LivePaper) else LivePaper(paper)
    _stage = stage or LiveStage()
    _board = board or InMemoryWhiteboard()
    _beats.clear()


def session_surfaces():
    """Transcript, paper and stage for the bound lesson, for the runtime to render.

    Everything the tutor can act on is here, and everything here reaches the
    student. The board is on that list again: it was removed when nothing
    rendered it, because a tutor telling a student to look at a board that does
    not exist is worse than a tutor with no board. It is drawn now, so it is
    back.
    """
    return _audio, _paper, _stage, _board


def turn_beats() -> list[dict]:
    """This turn's moments, in order, for the runtime to replay."""
    return list(_beats)


def clear_beats() -> None:
    _beats.clear()


def _now() -> datetime:
    return datetime.now(timezone.utc)


def get_lesson_material(activity_id: str = "") -> dict:
    """Return the material prepared for this lesson.

    Args:
      activity_id: Return only the material for one activity. Empty returns a
        summary of everything available.

    Returns:
      The material items, with their content and answer keys. This is the
      material that was written and quality-checked before the lesson; use it
      rather than inventing content live.
    """
    items = _material.get("items", [])
    if activity_id:
        matching = [i for i in items if i.get("activity_id") == activity_id]
        if not matching:
            return {"error": f"No material for activity {activity_id!r}.",
                    "available": [i.get("activity_id") for i in items]}
        return {"activity_id": activity_id, "items": matching}
    return {
        "item_count": len(items),
        "items": [{"id": i.get("id"), "activity_id": i.get("activity_id"),
                   "kind": i.get("kind"), "title": i.get("title")} for i in items],
    }


def get_student_profile() -> dict:
    """Return who you are teaching and how they like to be taught.

    Returns:
      Preferences, strengths, weaknesses and known misconceptions. Follow the
      stated preferences: they are what the student said, not an inference.
    """
    if _state is None:
        return {"error": "No lesson is bound."}
    profile = _profiles.get_student(_state.student_id)
    if profile is None:
        return {"student_id": _state.student_id, "profile_exists": False}
    learning = profile.for_subject(_state.subject)
    prefs = profile.learning_preferences
    return {
        "student_id": _state.student_id,
        "profile_exists": True,
        "preferences": prefs.model_dump(),
        "strengths": learning.strengths if learning else [],
        "weaknesses": learning.weaknesses if learning else [],
        "misconceptions": [m.model_dump() for m in (learning.misconceptions if learning else [])],
    }


def get_lesson_status() -> dict:
    """Return where the lesson is: state, current activity, time left.

    Returns:
      The live state, the current activity, objective progress and minutes
      remaining. Minutes remaining is authoritative — when it reaches zero the
      lesson ends, finished or not.
    """
    if _state is None:
        return {"error": "No lesson is bound."}
    now = _now()
    return {
        "live_state": _state.live_state,
        "current_activity_id": _state.current_activity_id,
        "minutes_remaining": round(_state.minutes_remaining(now), 1),
        "student_present": _state.presence.student_present,
        "additional_person_detected": _state.presence.additional_person_detected,
        "objectives": [
            {"id": o.objective_id, "statement": o.statement, "status": o.status}
            for o in _state.objectives
        ],
        "activities": [
            {"id": a.get("id"), "phase": a.get("phase"), "title": a.get("title"),
             "minutes": a.get("minutes"), "optional": a.get("is_optional", False)}
            for a in _plan.get("activities", [])
        ],
    }


def update_lesson_state(activity_id: str = "", objective_id: str = "", status: str = "") -> dict:
    """Record progress through the lesson.

    Args:
      activity_id: The activity now in progress.
      objective_id: An objective whose status changed.
      status: The new status: in_progress, completed or partial.

    Returns:
      The updated progress. Only completed objectives count as completed, and
      only when the student demonstrated them — not when you finished explaining.
    """
    if _state is None:
        return {"error": "No lesson is bound."}
    if activity_id:
        _state.current_activity_id = activity_id
        if activity_id not in _state.execution.activities_completed:
            pass  # completion is recorded when the next activity starts
    if objective_id and status:
        for objective in _state.objectives:
            if objective.objective_id == objective_id:
                objective.status = status  # type: ignore[assignment]
    return {"current_activity_id": _state.current_activity_id,
            "objectives": [{"id": o.objective_id, "status": o.status} for o in _state.objectives]}


def record_observation(kind: str, detail: str) -> dict:
    """Note something worth remembering after the lesson.

    Args:
      kind: "question", "mistake", "success", "misconception" or "note".
      detail: What happened, in your own words, specifically.

    Returns:
      Confirmation. These become the evidence the post-lesson stage uses to
      update the student's profile, so record what you saw, not what you infer
      it means about their ability.
    """
    if _state is None:
        return {"error": "No lesson is bound."}
    bucket = {
        "question": _state.interaction.questions_asked,
        "mistake": _state.interaction.mistakes,
        "success": _state.interaction.successful_answers,
        "misconception": _state.interaction.misconceptions_observed,
    }.get(kind)
    if bucket is None:
        bucket = _state.interaction.questions_asked if kind == "note" else None
    if bucket is None:
        return {"error": f"Unknown observation kind {kind!r}."}
    bucket.append(detail)
    return {"recorded": kind, "count": len(bucket)}


def explain_on_paper(say: str, write: str, highlight: int = -1,
                     gap: int = -1, where: str = "below",
                     page_id: str = "") -> dict:
    """Say one line of your explanation and write it down in the same moment.

    This is how you explain. Not a paragraph and then some marks: one step,
    spoken and written together, so the student hears the words as the line
    appears in front of them.

    Args:
      say: What you say aloud for this step. One sentence.
      write: What appears on the paper as you say it. Short — a line of
        working, a rule, a correction. It should be the thing the sentence is
        about, not a summary of it.
      highlight: Which printed thing on the page this step is ABOUT, numbered
        as show_page's `circleable` reported it. It is ringed in blue while you
        say the sentence, so the student's eye is on the thing you are talking
        about. Leave it out only when the step is about nothing on the page.
      gap: Which numbered gap this step fills, from show_page's `gaps`. When
        given, `write` goes INTO that blank instead of at the foot of the page
        — which is where the answer belongs, and where the student will look
        for it afterwards.
      where: Where the line goes when it is not filling a gap: "below" the
        page's work, "beside" it in the margin, or "over" it.
      page_id: Which page. Defaults to the one showing.

    Returns:
      The mark. Call it once per step and in order: three calls make three
      moments the student can follow, one call with everything in it makes a
      wall of text that appears at once.
    """
    if _state is None:
        return {"error": "No lesson is bound."}
    if not _paper.is_open:
        return {"error": "No worksheet was published for this lesson."}
    try:
        # An answer belongs in its blank, not in a list at the foot of the
        # page. Everything else is working, and working goes below.
        if gap >= 0:
            mark = _paper.fill(gap, write, page_id=page_id)
        else:
            # Anchored to whatever this step is about, so the line is drawn
            # against that thing rather than added to a pile at the bottom.
            mark = _paper.write(write, page_id=page_id, where=where,  # type: ignore[arg-type]
                                at=highlight if highlight >= 0 else None)
    except (PaperNotOpen, NoSuchPage, ValueError) as exc:
        return {"error": str(exc)}

    ringed = None
    if highlight >= 0:
        try:
            # Blue: the thing being talked about, as opposed to red for a
            # mistake and green for something got right.
            ringed = _paper.circle([highlight], page_id=page_id, colour="blue")
        except (PaperNotOpen, NoSuchPage, ValueError):
            ringed = None

    _audio.speak(say)
    _state.tutor_actions.paper_marks += 1
    _state.tutor_actions.explanations_given += 1
    _beats.append({"say": say, "write": write, "on": mark.on.box,
                   "where": where, "mark_id": mark.id,
                   "highlight": highlight if ringed else -1})
    return {"said": say, "wrote": write, "on": mark.on.box,
            "mark_id": mark.id,
            "highlighted": highlight if ringed else None,
            "filled_gap": gap if gap >= 0 else None}


def write_on_board(text: str) -> dict:
    """Write a line on the shared whiteboard, beside the paper.

    Args:
      text: One line — a step of working, an equation, a word being spelled
        out. Write the steps one call at a time so the student watches it
        appear rather than meeting a finished block.

    Returns:
      The board as it now stands. The board is for working that does not belong
      on the paper: scratch arithmetic, a calculation posed and carried, a
      diagram in words. What belongs on the paper goes on the paper — the board
      is wiped at the end of the hour and the paper is kept.
    """
    if _state is None:
        return {"error": "No lesson is bound."}
    _board.apply(WhiteboardAction(op="write", content=text))
    _state.tutor_actions.whiteboard_actions += 1
    return {"wrote": text, "lines_on_board": len(_board.snapshot())}


def clear_board() -> dict:
    """Wipe the whiteboard.

    Returns:
      Confirmation. Clear it between activities so the student is not reading
      the last exercise's working under this one's.
    """
    _board.apply(WhiteboardAction(op="clear"))
    return {"lines_on_board": 0}


def show_material(item_id: str) -> dict:
    """Put a piece of this lesson's material on the student's screen.

    Args:
      item_id: The item's id, from get_lesson_material.

    Returns:
      What is now on their screen. Use this for the things the paper does not
      carry — a rule table, a dialogue to read aloud, a worked example written
      for this lesson. Say what you are showing and why; a panel that appears
      in silence is a panel nobody reads.

      One thing at a time: showing something replaces what was there.
    """
    items = _material.get("items", [])
    match = next((i for i in items if i.get("id") == item_id), None)
    if match is None:
        return {"error": f"No material item {item_id!r} in this lesson.",
                "available": [i.get("id") for i in items]}

    # The answer key is the tutor's, not the student's. It is in `_material`
    # for the tutor to read; it does not go on the screen the student is
    # looking at.
    _stage.show({
        "id": match.get("id", ""),
        "kind": match.get("kind", ""),
        "title": match.get("title", ""),
        "instruction": match.get("instruction", ""),
        "content": match.get("content", ""),
        "exercises": [
            {"id": e.get("id"), "prompt": e.get("prompt", ""),
             "instructions": e.get("instructions", ""),
             "options": e.get("options") or []}
            for e in (match.get("exercises") or [])
        ],
    })
    return {"showing": match.get("id"), "title": match.get("title", ""),
            "kind": match.get("kind", "")}


def stop_showing_material() -> dict:
    """Take the material off the screen, leaving the student's paper.

    Returns:
      Confirmation. Do this when you move on, so the student is not reading
      last activity's dialogue while you talk about the next one.
    """
    _stage.clear()
    return {"showing": None}


def say(text: str) -> dict:
    """Say something to the student.

    Args:
      text: What to say, in the language of the lesson.

    Returns:
      Confirmation. This is the tutor's voice; the runtime renders it as speech
      or as text depending on what the session supports.
    """
    _audio.speak(text)
    return {"said": text[:80], "turns": len(_audio.transcript())}


def evaluate_student_answer(question: str, expected: str, given: str) -> dict:
    """Judge one answer and record the outcome.

    Args:
      question: What was asked.
      expected: The expected answer, from the material's answer key.
      given: What the student actually said.

    Returns:
      Whether it was correct, and what to do next. Arithmetic is checked exactly
      rather than by eye; anything else is compared as text and left to your
      judgement when it is close but not identical.
    """
    if _state is None:
        return {"error": "No lesson is bound."}
    from ..material.arithmetic import check as _check

    verdict = _check(expected, given) if any(c.isdigit() for c in expected) else {
        "verdict": "unverifiable", "reason": "not arithmetic"
    }
    exact = given.strip().lower() == expected.strip().lower()
    correct = verdict["verdict"] == "correct" or exact

    if correct:
        _state.interaction.successful_answers.append(f"{question} -> {given}")
    else:
        _state.interaction.mistakes.append(f"{question} -> {given} (expected {expected})")

    return {
        "correct": correct,
        "checked_exactly": verdict["verdict"] in {"correct", "incorrect"},
        "expected": expected,
        "given": given,
        "suggestion": "continue" if correct else "explain",
    }


def generate_adaptive_exercise(objective_id: str, easier: bool = True) -> dict:
    """Ask for one more practice item, pitched up or down.

    Args:
      objective_id: The objective it should practise.
      easier: True for a gentler item after a mistake, False to stretch.

    Returns:
      A specification for the item. Write the item yourself against it, using
      the same content the lesson has already used where you can — a familiar
      context with one thing changed is easier to learn from than a new one.
    """
    if _state is None:
        return {"error": "No lesson is bound."}
    _state.tutor_actions.additional_examples += 1
    return {"objective_id": objective_id, "pitch": "easier" if easier else "harder",
            "requirement": "One item, same objective, familiar context."}


# ── the lesson paper ────────────────────────────────────────────────────────
#
# The paper is the lesson made visible. It was written for this student before
# the class and handed to them blank; teaching on it — turning to a page,
# filling a gap, ringing the word that was wrong — is what leaves them a
# document at the end that shows the hour happened. Everything below names a
# page, never a position, so a mark survives a phone, a laptop and a printer.


def lesson_paper() -> dict:
    """Return the paper for this lesson: its title, its pages, which one is showing.

    Returns:
      Each page with its id, its title, how many gaps it has to fill and how
      many things on it can be circled. Read this before teaching so you know
      what the student is holding; use show_page to look at one properly.
    """
    if not _paper.is_open:
        return {"paper_available": False,
                "reason": "No worksheet was published for this lesson."}
    return {"paper_available": True, "title": _paper.title,
            "showing": _paper.showing or None, "pages": _paper.pages(),
            "marks_made": _paper.marks_made()}


def show_page(page_id: str) -> dict:
    """Put one page of the paper in front of the student, and read it yourself.

    Args:
      page_id: The page's id, from lesson_paper().

    Returns:
      Everything printed on that page, the answer key, and the numbering the
      other paper tools use: `gaps` are numbered for fill_in_gap, `circleable`
      for circle_on_paper. The student now sees this page, so say what you are
      turning to rather than letting the page change under them in silence.
    """
    if not _paper.is_open:
        return {"error": "No worksheet was published for this lesson."}
    try:
        _paper.show(page_id)
    except NoSuchPage:
        return {"error": f"There is no page {page_id!r} on this paper.",
                "pages": [p["id"] for p in _paper.pages()]}
    # Turning the page is a beat too.
    #
    # The tutor's page turns all happen the instant it decides them, while the
    # explanation they belong to plays out over the next ten seconds in the
    # browser. So the paper would already be on the last page while the student
    # was still hearing about the first — which looks exactly like a timer
    # yanking the page away mid-sentence. Recorded here, the browser turns to it
    # at the point in the sequence where the tutor actually said so.
    _beats.append({"turn_to": page_id})
    return {"showing": page_id, **_paper.describe_page(page_id)}


def write_on_paper(text: str, where: str = "below", page_id: str = "") -> dict:
    """Write on the paper in your own hand: a worked line, a note, a correction.

    Args:
      text: What to write. One line — a step of working, a rule in six words, a
        correction. A paragraph belongs in speech, not on a page margin.
      where: "below" the page's work, "beside" it in the margin, or "over" it.
      page_id: Which page. Defaults to the one showing.

    Returns:
      The mark, with the id you would pass to erase_paper_mark. Say the words
      while you write them: a line appearing in silence teaches nothing.
    """
    if not _paper.is_open:
        return {"error": "No worksheet was published for this lesson."}
    try:
        mark = _paper.write(text, page_id=page_id, where=where)  # type: ignore[arg-type]
    except (PaperNotOpen, NoSuchPage) as exc:
        return {"error": str(exc)}
    if _state is not None:
        _state.tutor_actions.paper_marks += 1
    return {"wrote": text, "on": mark.on.box, "mark_id": mark.id}


def fill_in_gap(row: int, text: str, page_id: str = "") -> dict:
    """Write the missing word into the blank it belongs in.

    Args:
      row: Which gap, numbered as show_page reported it.
      text: What goes in the blank.
      page_id: Which page. Defaults to the one showing.

    Returns:
      The mark. Fill a gap once the student has produced the answer, or once
      you have worked it out together — filling it for them the moment it is
      asked turns the paper into a handout.
    """
    if not _paper.is_open:
        return {"error": "No worksheet was published for this lesson."}
    try:
        mark = _paper.fill(row, text, page_id=page_id)
    except (PaperNotOpen, NoSuchPage, ValueError) as exc:
        return {"error": str(exc)}
    if _state is not None:
        _state.tutor_actions.paper_marks += 1
    return {"filled": row, "with": text, "on": mark.on.box, "mark_id": mark.id}


def circle_on_paper(words: list[int], colour: str = "red", page_id: str = "") -> dict:
    """Ring something already printed on the page.

    Args:
      words: Which things, numbered as show_page's `circleable` reported them.
        An empty list rings the whole page.
      colour: "red" for a mistake, "green" for a right answer, "blue" to mark the thing
        being talked about.
      page_id: Which page. Defaults to the one showing.

    Returns:
      The mark. A ring is for the one word the lesson turns on; ringing six
      things rings nothing.
    """
    if not _paper.is_open:
        return {"error": "No worksheet was published for this lesson."}
    try:
        mark = _paper.circle(words, page_id=page_id, colour=colour)  # type: ignore[arg-type]
    except (PaperNotOpen, NoSuchPage, ValueError) as exc:
        return {"error": str(exc)}
    if _state is not None:
        _state.tutor_actions.paper_marks += 1
    return {"circled": words, "colour": colour, "on": mark.on.box, "mark_id": mark.id}


def point_at_paper(page_id: str = "") -> dict:
    """Put a dot on the page for the student to follow while you talk.

    Args:
      page_id: Which page. Defaults to the one showing.

    Returns:
      Confirmation. A pointer is a gesture, not a mark: it is not kept on the
      copy the student takes away, so use it freely.
    """
    if not _paper.is_open:
        return {"error": "No worksheet was published for this lesson."}
    try:
        mark = _paper.point(page_id=page_id)
    except (PaperNotOpen, NoSuchPage) as exc:
        return {"error": str(exc)}
    return {"pointing_at": mark.on.box}


def erase_paper_mark(mark_id: str) -> dict:
    """Take back a mark you made.

    Args:
      mark_id: The id returned when the mark was made.

    Returns:
      What is left on the paper. Erase your own mistakes; do not erase the
      student's working to make the page tidy.
    """
    if not _paper.is_open:
        return {"error": "No worksheet was published for this lesson."}
    _paper.erase(mark_id)
    return {"erased": mark_id, "marks_remaining": _paper.marks_made()}


def explain(idea: str, in_plain_words: str, worked_example: str,
            check_question: str) -> dict:
    """Explain one idea properly: say it, show it, then check it.

    This is the only way to explain. It exists because the three parts have to
    happen together — an explanation with no example is a definition, and one
    with no check is a guess about whether it landed.

    Args:
      idea: The one thing being explained. One thing, not three.
      in_plain_words: The idea in language the student already has. No term
        introduced here may itself need explaining.
      worked_example: The idea done once, concretely, in the fewest steps that
        still show every step. This is written onto the paper.
      check_question: A question the student can only answer if they followed.
        Not "does that make sense" — that measures politeness.

    Returns:
      What was said and what was written. The check question has been asked;
      wait for the answer and put it through evaluate_student_answer.
    """
    if _state is None:
        return {"error": "No lesson is bound."}
    _audio.speak(in_plain_words)
    written = None
    if _paper.is_open and _paper.showing:
        written = _paper.write(worked_example, where="below")
        _state.tutor_actions.paper_marks += 1
    else:
        # There is nowhere to write it, so the example is spoken instead and
        # the tutor is told so. It used to go onto an in-memory whiteboard the
        # student could not see, which is worse than not writing it: the tutor
        # then says "look at the board" and the student looks at nothing.
        _audio.speak(worked_example)
    _audio.speak(check_question)
    _state.tutor_actions.explanations_given += 1
    return {
        "explained": idea,
        "shown_on": "paper" if written else "nothing — spoken only",
        "mark_id": written.id if written else None,
        "asked": check_question,
        "next": "Wait for the answer, then call evaluate_student_answer."
        if written else
        "No page is showing, so the example could only be spoken. Call show_page "
        "first if you want it written down. Then wait for the answer.",
    }



LIVE_TUTOR_TOOLS = [
    get_lesson_material,
    get_student_profile,
    get_lesson_status,
    lesson_paper,
    show_page,
    write_on_paper,
    fill_in_gap,
    circle_on_paper,
    point_at_paper,
    erase_paper_mark,
    explain,
    update_lesson_state,
    record_observation,
    show_material,
    stop_showing_material,
    write_on_board,
    clear_board,
    say,
    evaluate_student_answer,
    generate_adaptive_exercise,
]

INSTRUCTION = """\
You are the tutor, teaching one student for one booked hour. You are the same
tutor for every subject: what changes is the plan, the material and the student.

Start every turn by calling get_lesson_status. It tells you the state, the
current activity and how many minutes remain. Minutes remaining is
authoritative and it is not yours to extend.

TEACH ON THE PAPER
The student has a worksheet in front of them, written for this lesson. It is
the lesson made visible, and teaching happens on it.

- Call lesson_paper at the start to see what pages exist, then show_page to
  turn to the one the current activity uses. Say what you are turning to. A
  page that changes in silence loses the student.
- show_page gives you what is printed there, the answer key, and the numbering
  the marking tools take. Never guess a gap number — read it.
- Mark the paper as you talk, not afterwards:
    write_on_paper   a worked line, a rule in six words, a correction
    fill_in_gap      the missing word, once it has been worked out
    circle_on_paper  the one word the lesson turns on — red wrong, green right
    point_at_paper   "look here" while you say the next sentence
- Speak every mark as you make it. A line that appears in silence teaches
  nothing, and the student cannot see your cursor move.
- Do not fill the answers in ahead of the student. A gap filled the moment it
  is asked turns the paper into a handout. Fill it when they have produced the
  answer, or when the two of you have worked it out.
- The paper is the marked record the student keeps. By the end of the hour it
  should show where the class went: worked lines under the pages you taught,
  answers in the gaps you covered, rings on what was hard. A class that ends
  with a blank sheet was a lecture.

THE BOARD
write_on_board puts a line on the whiteboard beside the paper; clear_board
wipes it. It is for working that does not belong on the paper — scratch
arithmetic, a calculation posed and carried, a sum tried two ways.
- One line per call, in the order you would write them, so the student watches
  the working appear rather than meeting a finished block.
- Clear it between activities.
- The board is wiped at the end of the hour; the paper is kept. Anything the
  student should still have next week goes on the paper.

THE MATERIAL
get_lesson_material lists what was written for this lesson beyond the paper —
rule tables, dialogues, worked examples, exercise sets. show_material puts one
on the student's screen; stop_showing_material takes it off again.

- Show it, then talk about it. Say what you are putting up and why.
- One thing at a time. Showing something replaces what was there.
- Take it down when you move on, or the student reads the last activity while
  you talk about the next one.
- What you can show the student is the paper, the material and the board.
  Nothing else. Never tell a student to look at something you have not put in
  front of them with one of those three.

SPEAKING
Everything you say to the student goes through say or explain. Those are your
voice; your own reply text is not spoken to anybody, so anything you leave
there is lost. Say it with the tool.

Write only your own words. Never write the student's turn for them, never
continue the conversation past what they have actually said, and never invent a
question they did not ask. Say your part, then stop and wait.

EXPLAINING
Use the explain tool. It is the only way to explain, because its four parts
have to happen together:
  idea            one thing, not three
  in_plain_words  language the student already has; no term that itself needs
                  explaining, and no restating of the definition louder
  worked_example  the idea done once, concretely, every step shown — this is
                  written onto the paper
  check_question  a question they can only answer if they followed
"Does that make sense?" is not a check question. It measures politeness. Ask
something with a right answer: "so which one goes in front of Tisch?"

If the check answer is wrong, that is information about your explanation, not
about the student. Explain the same idea a different way — a different example,
a different angle, something they already know — and never the same words
slower. Two failed explanations of one idea means the idea is too big: break it
into the smaller thing they are actually missing and teach that.

EVERY EXPLANATION LEAVES A MARK
If you explain something, write it down — write_on_paper for the worked line,
fill_in_gap for an answer the student produced, circle_on_paper in red for the
step that went wrong and green for one they got right. A short turn is not an
excuse to write nothing: the student keeps the paper, not the conversation, and
a class that ends with a blank sheet was a lecture.

KEEP YOUR TURNS SHORT
Two or three sentences, then stop. The student may be hearing you read aloud
rather than reading you, and a paragraph delivered at them is a broadcast: by
the end they have forgotten the question and cannot find the place to answer.
- Open a lesson in three sentences: hello, what the hour is for, first question.
  Not a tour of the objectives.
- Give one step, then check it. Not all four steps and then a check.
- Ask your question last and stop there. Do not add a second question after it,
  and do not answer it yourself.

TEACHING
- Follow the plan's activities in order, but the plan is a plan, not a script.
  A student who has understood in four minutes should move on; one who has not
  understood in ten needs explaining differently.
- Ask one question at a time and wait. Do not stack three questions and take
  whichever gets answered.
- Silence after a question is thinking. Leave it. Do not answer your own
  question — a hint is better than the answer, and the answer taken back from
  them is a turn of the lesson wasted.
- Call evaluate_student_answer for every answer. Do not judge arithmetic by
  eye — the tool checks it exactly.
- After a wrong answer: find out what they did, not just that it was wrong.
  Circle the step where it went wrong in red, explain that step, then use
  generate_adaptive_exercise for an easier item on the same objective. Do not
  simply repeat the question.
- After a right answer given easily: move on, or stretch. Do not fill time and
  do not praise a trivial answer lavishly — a student who is praised for
  everything learns nothing from being praised.
- Praise the work, not the person: "that step is exactly right" teaches where
  to repeat; "you're so clever" does not.
- Call record_observation as things happen — a question asked, a mistake, a
  misconception, something done well. This is the evidence the profile is
  updated from later, so record what you SAW, not what you conclude it means.
- Call update_lesson_state when an activity starts and when an objective is
  genuinely demonstrated. Finishing your explanation is not the student
  demonstrating the objective.

PRESENCE
- If student_present is false, stop teaching and wait. Do not carry on to an
  empty room.
- If additional_person_detected is true, you may acknowledge that someone else
  is there. You may NOT say who they are. You do not know, and guessing about
  a real person is not something to do out loud.

TIME
- When minutes_remaining is low, close properly: turn to the summary page,
  recap what was covered on the paper in front of you, and name what was not.
  An hour that ends mid-sentence teaches nothing at the end.
- Never promise to finish something in a future lesson. You do not book those.

Never invent material. If get_lesson_material has nothing for an activity, say
so and work with what exists.
"""

live_tutor_agent = LlmAgent(
    name="live_tutor",
    model=MODEL,
    description="Teaches one prepared 60-minute lesson, adapting to the student.",
    instruction=INSTRUCTION,
    tools=LIVE_TUTOR_TOOLS,
)


# What a spoken tutor may do, as opposed to look up.
#
# The read tools are gone. In a text lesson "start every turn by calling
# get_lesson_status" costs one round trip per turn and buys accuracy; in a
# spoken one the model was calling four of them before every single utterance —
# status, paper, profile, material — and the turn frequently died in the middle
# of that without ever producing a word. What those tools return does not change
# between one sentence and the next, so it is put in the briefing instead and
# the tutor is left with the things that actually DO something.
SPOKEN_TUTOR_TOOLS = [
    explain_on_paper,
    show_page,
    write_on_paper,
    fill_in_gap,
    circle_on_paper,
    write_on_board,
    clear_board,
    show_material,
    stop_showing_material,
    evaluate_student_answer,
    record_observation,
    update_lesson_state,
]


SPOKEN_INSTRUCTION = """\
You are the tutor, teaching one student for one booked hour, out loud.

You are speaking and listening. Your voice is your voice: say what you want to
say, do not route it through a tool, and do not narrate what you are about to
do instead of doing it.

SPEAK FIRST, ACT SECOND.
Every turn is a spoken reply. Answer the student, then — if the lesson needs it
— touch the paper or the board. A turn that only calls tools is a turn where
the student heard nothing and thinks you have gone away.

TAKE TURNS.
Two or three sentences, then stop and let them answer. Ask one question and
wait for it. Do not deliver a paragraph; this is a conversation.

TEACHING
- Follow the lesson in the briefing below. It tells you the objectives, the
  plan, the pages of the paper and the material — you do not need to ask for
  any of it.
- When a student is wrong, find out what they did before correcting it. Explain
  the step that went wrong, not the whole topic again.
- When they are right, say so and move on. Do not fill time.
- Praise the work, not the person: "that step is exactly right" teaches where
  to repeat it.
- Never invent an exercise that is not on the paper or in the material.

WHAT YOU CAN DO WHILE YOU TALK
  show_page             turn the student's paper to a page — say what you are
                        turning to; it also gives you that page's answer key
  write_on_paper        a worked line under the page, in your hand
  fill_in_gap           the missing word, once it has been worked out
  circle_on_paper       red for a mistake, green for something got right
  write_on_board        working that does not belong on the paper; one line per
                        call, and clear_board between activities
  show_material         put a rule table or an exercise set on their screen;
                        stop_showing_material takes it off
  evaluate_student_answer  for an answer with a right answer — it checks
                        arithmetic exactly rather than by eye
  record_observation    a mistake, a question, a misconception, something done
                        well: evidence for the next lesson
  update_lesson_state   when an objective is genuinely demonstrated

EXPLAIN BY WRITING, ONE STEP AT A TIME.
explain_on_paper is how you teach. It says a sentence and writes a line on the
paper in the same moment, so the student hears the words as the line appears.

Use it for every step of every explanation, one call per step, and POINT AT
WHAT YOU ARE TALKING ABOUT. show_page numbers everything printed on the page;
pass that number as `highlight` and it is ringed while you speak, so the
student's eye is on the thing your sentence is about. An explanation that
points at nothing is the thing they mean by "explaining in the air".

    explain_on_paper(say="Regarde ce nombre : les parties entières sont les mêmes.",
                     write="3,5 et 3,45 → 3 = 3", highlight=0)
    explain_on_paper(say="Alors on compare les dixièmes : 5 contre 4.",
                     write="0,5 > 0,45", highlight=1)

When the step is the ANSWER to a numbered question, pass `gap` as well and the
answer is written into that blank instead of at the foot of the page:

    explain_on_paper(say="Donc ici on met 'der'.", write="der", gap=2, highlight=2)

Three steps is three calls. One call with the whole explanation in it is a wall
of text that lands at once, which is the thing you are trying not to do.
Do not stack every line at the bottom of the page: an answer goes in its blank,
and what you are discussing gets ringed where it is printed.

An explanation with nothing written beside it is talking into the air. If you
find yourself explaining without calling explain_on_paper, you are lecturing.

Do not then repeat it. The student has heard every step as you wrote it, so
"je viens de t'écrire que..." is the same explanation twice. After the steps,
say only what comes next — the question you want them to answer.

ONLY EVER YOUR OWN WORDS.
Say your part and stop. Never write the student's turn for them, never put a
name and a colon in front of anything, and never carry the conversation past
what they have actually said. If you ask a question, the next thing that
happens is them answering it — not you answering it as them.

ALWAYS SAY SOMETHING. IN WORDS.
Your reply is what the student hears — it is read aloud to them. A reply that
is empty, or a single character, or a placeholder like "_" or "ok", is silence
as far as they are concerned, however many tools you called. Calling a tool is
not talking. Say the sentence, then make the mark.

THE PAPER IS THE DEFAULT SURFACE.
write_on_paper is where working goes. It is the document the student keeps,
it is in front of them, and it is what they revise from.
THE BOARD IS FOR WHAT THE STUDENT BRINGS.
The whiteboard is not your second notepad. It is where something the student
has brought to the lesson gets worked through — a problem from their homework,
an exercise from another book, a question they turned up with. That is the only
thing it is for.
Nothing from this lesson goes on the board. The lesson is on the paper.

THE STUDENT WRITES ON THE PAPER TOO.
They may answer by writing rather than speaking, and you will be shown what
they wrote. Read it and respond to it as an answer: mark it right or wrong,
say what you can see, and never ask them to repeat aloud something they have
already written down in front of you.

LEAVE SOMETHING WRITTEN. EVERY TIME.
Marking the paper is not optional and it is not decoration. A lesson where you
only talked is a lesson the student cannot revise from — they keep the paper,
not the conversation.

- Explained a step? write_on_paper the worked line for it, as you say it.
- Student got it right? fill_in_gap with their answer, or circle_on_paper it in
  green. The gap they filled in front of you is the one they should see filled.
- Student got it wrong? circle_on_paper the step in red, then write the correct
  line under it.
- Working that does not belong on the paper — a calculation posed, a sum tried
  two ways — goes on the board with write_on_board.

If you finish a turn having explained something and written nothing, you have
left the student with a blank sheet and a memory. Write it down.

Say the mark as you make it — the student cannot see your cursor. Speak, then
mark, then wait.

TALK LIKE A PERSON, NOT AN INTERFACE.
Do not read out page titles, headings or the names of things on the screen.
"Regarde la page 3, « Structure des grands nombres »" is a menu being read
aloud. A teacher says "bon, regarde ce tableau" and carries straight on with
the thing itself. Turn the page and keep talking about the maths.
Never narrate what you are doing — no "je vais maintenant écrire", no "laisse-
moi ouvrir". Do it, and say the thing it is for.

PRESENCE AND TIME
If the student has gone quiet, ask; do not lecture an empty room. When the hour
is nearly up, close properly: recap what was covered and name what was not.
Never promise to finish something in a future lesson — you do not book those.
"""


def spoken_tutor(model: str, language_note: str = "", briefing: str = "") -> LlmAgent:
    """The same tutor, on a model that can hear and speak.

    Same judgement and the same acting tools; what differs is that it is told
    where the lesson stands rather than asked to look it up, and that it has a
    voice — see `SPOKEN_TUTOR_TOOLS` and `live/audio.py` for why both matter.
    """
    return LlmAgent(
        name="live_tutor",
        model=model,
        description="Teaches one prepared lesson aloud, adapting to the student.",
        # Its OWN instruction, not the text tutor's. The text instruction
        # opens with "start every turn by calling get_lesson_status" and goes
        # on to require `say` and `explain` — three tools a spoken tutor does
        # not have. Given it, the model spent its turn calling for things that
        # were not there and ended without speaking: the student heard silence.
        instruction=SPOKEN_INSTRUCTION + language_note + briefing,
        tools=SPOKEN_TUTOR_TOOLS,
    )


def lesson_briefing() -> str:
    """Where this lesson stands, for a tutor that should not stop to ask.

    Everything the read tools would have returned, as one block: the plan, the
    pages of the paper with their numbering, and the material that can be put on
    screen. Built once when the spoken session opens.
    """
    lines: list[str] = ["\n\nTHIS LESSON, AS IT STANDS RIGHT NOW\n"]

    if _state is not None:
        lines.append(f"Subject {_state.subject}, level {_state.level_id}. "
                     f"Objectives for the hour:")
        for objective in _state.objectives:
            lines.append(f"  - [{objective.objective_id}] {objective.statement}")

    activities = _plan.get("activities") or []
    if activities:
        lines.append("\nThe plan:")
        for activity in activities:
            lines.append(f"  - {activity.get('id')}: {activity.get('title')} "
                         f"({activity.get('minutes')} min)")

    if _paper.is_open:
        lines.append(f"\nThe paper — \"{_paper.title}\" — has these pages. "
                     "Turn to one with show_page, which also gives you its "
                     "answer key and how its gaps are numbered:")
        for page in _paper.pages():
            lines.append(f"  - {page['id']}: {page['title']}"
                         + (f" ({page['gaps']} gaps)" if page["gaps"] else ""))
    else:
        lines.append("\nThere is NO paper for this lesson. Do not tell the "
                     "student to look at one.")

    items = _material.get("items") or []
    if items:
        lines.append("\nMaterial you can put on their screen with show_material:")
        for item in items:
            lines.append(f"  - {item.get('id')}: {item.get('title')} "
                         f"({item.get('kind')})")

    return "\n".join(lines)
