"""The live lesson state machine.

Deterministic Python, not an agent. Whether the hour is over is a clock
comparison; whether the student is on camera is a boolean. Asking a model to
decide either would add a way to get them wrong, and one of them — the clock —
governs whether we keep charging for the room.

The tutor agent decides *what to teach* inside a state. This decides *which
state we are in*, and it is the tutor agent's authority on that: the agent
cannot declare the lesson finished, and cannot keep it running past the hour.
"""

from __future__ import annotations

from datetime import datetime

from ..schemas.lesson_state import LessonState, LiveState, Transition

# Which states may follow which. Anything not listed is refused, so a
# mis-sequenced lesson fails loudly here rather than producing a plausible
# transcript in which the tutor greeted a student who had already left.
ALLOWED: dict[LiveState, set[LiveState]] = {
    "WAITING": {"STUDENT_DETECTED", "LESSON_END"},
    "STUDENT_DETECTED": {"GREETING", "STUDENT_ABSENT", "LESSON_END"},
    "GREETING": {"LESSON_STARTED", "STUDENT_ABSENT", "LESSON_END"},
    "LESSON_STARTED": {"TEACHING", "STUDENT_ABSENT", "LESSON_END"},
    "TEACHING": {"QUESTION", "EXPLAIN", "ADAPT", "STUDENT_ABSENT", "LESSON_END"},
    "QUESTION": {"STUDENT_RESPONDS", "STUDENT_ABSENT", "LESSON_END"},
    "STUDENT_RESPONDS": {"EVALUATE", "STUDENT_ABSENT", "LESSON_END"},
    "EVALUATE": {"CONTINUE", "EXPLAIN", "ADAPT", "STUDENT_ABSENT", "LESSON_END"},
    "CONTINUE": {"TEACHING", "QUESTION", "STUDENT_ABSENT", "LESSON_END"},
    "EXPLAIN": {"TEACHING", "QUESTION", "STUDENT_ABSENT", "LESSON_END"},
    "ADAPT": {"TEACHING", "QUESTION", "STUDENT_ABSENT", "LESSON_END"},
    # Absence returns to WAITING, and the lesson resumes from there.
    "STUDENT_ABSENT": {"WAITING", "LESSON_END"},
    "LESSON_END": set(),
}

# Where a returning student picks up. Kept apart from ALLOWED because "what may
# follow" and "where we were" are different questions.
RESUME_FROM_WAITING: LiveState = "TEACHING"


class IllegalTransition(ValueError):
    """That state cannot follow this one."""


class LessonClosed(ValueError):
    """The lesson is over. Nothing further may happen in it."""


def _record(state: LessonState, to: LiveState, trigger: str, now: datetime) -> LessonState:
    state.transitions.append(
        Transition(at=now, from_state=state.live_state, to_state=to, trigger=trigger)
    )
    state.live_state = to
    return state


def transition(state: LessonState, to: LiveState, trigger: str, now: datetime) -> LessonState:
    """Move to a new state, or refuse.

    The scheduled end wins over everything. Whatever a caller asks for, once the
    hour is up the only legal move is LESSON_END — the student paid for sixty
    minutes and the lesson stops there whether or not the plan is finished.
    """
    if state.live_state == "LESSON_END":
        raise LessonClosed("the lesson has already ended")

    if state.is_over(now) and to != "LESSON_END":
        return end_lesson(state, now, reason="scheduled end reached")

    if to not in ALLOWED[state.live_state]:
        raise IllegalTransition(f"{state.live_state} -> {to} is not allowed")

    return _record(state, to, trigger, now)


def observe_presence(
    state: LessonState,
    student_present: bool,
    additional_person_detected: bool,
    now: datetime,
) -> LessonState:
    """Update presence and move the lesson if that changed things.

    Called on every presence sample, which is why it does no model work. A
    student who steps out mid-explanation should be noticed in seconds, and a
    model call per frame would be both slow and expensive.
    """
    state.presence.student_present = student_present
    state.presence.additional_person_detected = additional_person_detected
    state.presence.checked_at = now

    if state.is_over(now):
        return end_lesson(state, now, reason="scheduled end reached")

    if not student_present and state.live_state not in {"WAITING", "STUDENT_ABSENT", "LESSON_END"}:
        return _record(state, "STUDENT_ABSENT", "student left", now)

    if student_present and state.live_state == "STUDENT_ABSENT":
        _record(state, "WAITING", "student absent, waiting", now)
        return _record(state, RESUME_FROM_WAITING, "student returned", now)

    if student_present and state.live_state == "WAITING":
        return _record(state, "STUDENT_DETECTED", "student detected", now)

    return state


def start_lesson(state: LessonState, now: datetime) -> LessonState:
    """Greet, then begin. Records the actual start, which is rarely the booked one."""
    if state.live_state == "STUDENT_DETECTED":
        _record(state, "GREETING", "greeting the student", now)
    if state.live_state == "GREETING":
        _record(state, "LESSON_STARTED", "lesson started", now)
        state.status = "in_progress"
        state.execution.started_at = now
        _record(state, "TEACHING", "first activity", now)
    return state


def end_lesson(state: LessonState, now: datetime, reason: str = "lesson finished") -> LessonState:
    """Close the lesson and freeze what happened.

    Unfinished objectives are marked unfinished, not dropped and not deferred
    into some future hour. They are evidence for the next lesson's planning.
    """
    if state.live_state == "LESSON_END":
        return state
    _record(state, "LESSON_END", reason, now)
    state.status = "completed" if state.execution.started_at else "no_show"
    state.execution.ended_at = now
    if state.execution.started_at:
        elapsed = (now - state.execution.started_at).total_seconds() / 60.0
        state.execution.actual_duration_minutes = int(round(elapsed))
    for objective in state.objectives:
        if objective.status in {"not_started", "in_progress"}:
            objective.status = "unfinished"
    return state


def enforce_schedule(state: LessonState, now: datetime) -> LessonState:
    """End the lesson if its time is up. Safe to call on a timer."""
    if state.live_state != "LESSON_END" and state.is_over(now):
        return end_lesson(state, now, reason="scheduled end reached")
    return state
