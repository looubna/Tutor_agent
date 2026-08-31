"""The surfaces a live lesson needs, as interfaces.

None of these are wired to real infrastructure yet. That is deliberate: the
brief says to build a clean abstraction rather than pretend an integration
exists, and a fake whiteboard that silently drops strokes would be worse than
an obvious stub.

Each is a Protocol plus an in-memory implementation that records what it was
asked to do. The recordings are what the tests assert on, and what the existing
CallScreen will replay when it is connected.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Literal, Protocol

from pydantic import BaseModel, Field

from ..schemas.lesson_state import Presence

WhiteboardOp = Literal["write", "draw", "erase", "highlight", "equation", "image", "clear"]


class WhiteboardAction(BaseModel):
    """One mark on the shared board."""

    op: WhiteboardOp
    content: str = Field(default="", description="Text, LaTeX, or an image reference.")
    region: str = Field(default="", description="Where on the board, loosely.")
    at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class Whiteboard(Protocol):
    """The shared board. The tutor writes; the student sees."""

    def apply(self, action: WhiteboardAction) -> None: ...

    def snapshot(self) -> list[WhiteboardAction]: ...


class InMemoryWhiteboard:
    """Records every action in order. Replayable into a real board later."""

    def __init__(self) -> None:
        self._actions: list[WhiteboardAction] = []

    def apply(self, action: WhiteboardAction) -> None:
        if action.op == "clear":
            self._actions = []
            return
        self._actions.append(action)

    def snapshot(self) -> list[WhiteboardAction]:
        return list(self._actions)


class Stage(Protocol):
    """What the student is looking at, when it is not the paper."""

    def show(self, item: dict) -> None: ...

    def showing(self) -> dict | None: ...


class LiveStage:
    """The one thing on the student's screen besides their own paper.

    One at a time, deliberately. A tutor that can put four things up at once
    will, and a student looking at four things is looking at none of them.
    Showing something replaces whatever was there.
    """

    def __init__(self) -> None:
        self._showing: dict | None = None

    def show(self, item: dict) -> None:
        self._showing = item

    def showing(self) -> dict | None:
        return self._showing

    def clear(self) -> None:
        self._showing = None


class PresenceDetector(Protocol):
    """Who is in front of the camera."""

    def sample(self) -> Presence: ...


class ScriptedPresence:
    """A presence detector driven by a list, for tests and demos.

    Real detection belongs in a lightweight vision model running on frames, not
    an LLM call per sample — the brief is explicit, and a per-frame model call
    would cost more than the lesson. This stands in until that is wired.
    """

    def __init__(self, samples: list[Presence] | None = None) -> None:
        self._samples = list(samples or [])
        self._last = Presence(student_present=False)

    def push(self, presence: Presence) -> None:
        self._samples.append(presence)

    def sample(self) -> Presence:
        if self._samples:
            self._last = self._samples.pop(0)
        return self._last


class Utterance(BaseModel):
    """One thing said, by either party."""

    speaker: Literal["tutor", "student"]
    text: str
    at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class AudioChannel(Protocol):
    """Speech in and out. Text-only for now; the shape does not change when
    real audio arrives, because a transcript is what the tutor reasons over
    either way."""

    def speak(self, text: str) -> None: ...

    def transcript(self) -> list[Utterance]: ...


class InMemoryAudio:
    """Records what was said. The existing CallScreen renders this as a transcript."""

    def __init__(self) -> None:
        self._utterances: list[Utterance] = []

    def speak(self, text: str) -> None:
        self._utterances.append(Utterance(speaker="tutor", text=text))

    def hear(self, text: str) -> None:
        self._utterances.append(Utterance(speaker="student", text=text))

    def transcript(self) -> list[Utterance]:
        return list(self._utterances)
