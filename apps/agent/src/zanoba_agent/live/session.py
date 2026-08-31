"""One live lesson, held open between turns.

A turn arrives as an HTTP request and has to find the lesson it belongs to: the
state machine's record of the hour, the plan being taught, the material, the
paper being written on, and the conversation so far. That is what a `LiveLesson`
is, and this module is where they live while the class is running.

**They live in memory, in this process.** That is a deliberate limit and worth
saying plainly rather than discovering. Two consequences:

  - Run the service with session affinity, or with one instance, so a student's
    turns keep reaching the instance holding their lesson. Cloud Run supports
    affinity (`--session-affinity`); without it a second instance would greet a
    student who is twenty minutes in.
  - A turn carries everything needed to *rebuild* a lesson, so an instance that
    has never seen a booking starts it rather than refusing. What is lost in
    that case is the conversation so far, not the lesson: the marks are already
    on the paper in the database, and a rebuilt `LivePaper` starts empty, so
    nothing is drawn twice.

Persisting the conversation properly means an ADK session service backed by a
database rather than memory. That is the right fix and it is not this one.
"""

from __future__ import annotations

import time
from dataclasses import dataclass, field

from ..schemas.lesson_state import LessonState
from .paper import LivePaper
from .surfaces import InMemoryAudio, InMemoryWhiteboard, LiveStage

# How long a finished lesson stays around before it is swept. Long enough for a
# client to ask what happened at the end of the hour, short enough that a
# long-lived instance does not accumulate every class it ever taught.
KEEP_ENDED_SECONDS = 15 * 60


@dataclass
class LiveLesson:
    """Everything one class needs, between one turn and the next."""

    booking_id: str
    state: LessonState
    plan: dict = field(default_factory=dict)
    material: dict = field(default_factory=dict)
    paper: LivePaper = field(default_factory=LivePaper)
    audio: InMemoryAudio = field(default_factory=InMemoryAudio)
    # What the tutor has put on the student's screen beside their own paper.
    stage: LiveStage = field(default_factory=LiveStage)
    # The shared whiteboard: working that does not belong on the paper. Wiped
    # with the lesson, unlike the paper, which the student keeps.
    board: InMemoryWhiteboard = field(default_factory=InMemoryWhiteboard)

    def board_lines(self) -> list[str]:
        return [a.content for a in self.board.snapshot() if a.content]
    # The ADK session holding the tutor's side of the conversation, and the
    # runner that owns it. The runner carries this lesson's briefing, so it
    # belongs to the lesson rather than to the process.
    adk_session_id: str = ""
    runner: object | None = None
    started_at: float = field(default_factory=time.monotonic)
    ended_at: float | None = None

    @property
    def is_over(self) -> bool:
        return self.state.live_state == "LESSON_END"

    def transcript(self) -> list[dict]:
        """The conversation so far, as the web app renders it."""
        return [{"speaker": u.speaker, "text": u.text, "at": u.at.isoformat()}
                for u in self.audio.transcript()]


class LessonRegistry:
    """The lessons this process is currently teaching."""

    def __init__(self, keep_ended_seconds: float = KEEP_ENDED_SECONDS) -> None:
        self._lessons: dict[str, LiveLesson] = {}
        self._keep = keep_ended_seconds

    def get(self, booking_id: str) -> LiveLesson | None:
        return self._lessons.get(booking_id)

    def put(self, lesson: LiveLesson) -> LiveLesson:
        self._lessons[lesson.booking_id] = lesson
        return lesson

    def drop(self, booking_id: str) -> None:
        self._lessons.pop(booking_id, None)

    def sweep(self, now: float | None = None) -> int:
        """Forget lessons that ended a while ago. Returns how many went."""
        moment = now if now is not None else time.monotonic()
        stale = [
            booking_id for booking_id, lesson in self._lessons.items()
            if lesson.ended_at is not None and moment - lesson.ended_at > self._keep
        ]
        for booking_id in stale:
            del self._lessons[booking_id]
        return len(stale)

    def close(self, booking_id: str, now: float | None = None) -> None:
        """Mark a lesson finished so the sweeper can collect it later."""
        lesson = self._lessons.get(booking_id)
        if lesson and lesson.ended_at is None:
            lesson.ended_at = now if now is not None else time.monotonic()

    def __len__(self) -> int:
        return len(self._lessons)

    @property
    def booking_ids(self) -> list[str]:
        return sorted(self._lessons)
