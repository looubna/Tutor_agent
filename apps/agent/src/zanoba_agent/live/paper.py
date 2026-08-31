"""The lesson paper, as a surface the tutor shares, points at and writes on.

The paper is the lesson. It is written before the class by the material agents,
published as a `LessonDoc`, and handed to the student blank; what the tutor does
during the hour is *mark it up* — write a worked line under a page, circle the
word that was wrong, fill an answer into the gap it belongs in. Afterwards the
student keeps one document that shows the class happened, not a blank sheet and
a separate transcript.

Two rules shape every type in here.

**A mark names a box, never a position.** `write on s7` is still on s7 on a
phone, in the PDF a parent prints, and after the deck is re-typeset. There are
no coordinates in this file, and there is no screenshot: a picture of a board is
a picture, while this knows which page each mark belongs to.

**The vocabulary is the web app's, exactly.** These models serialise to the JSON
that `apps/web/src/lib/worksheet/ops.ts` parses — same op names, same field
names, same defaults. The runtime POSTs `ops()` straight to
`/api/lesson/{booking}/marks` and the student's browser replays them onto the
same paper. Change one side and you must change the other.

The answers stay here. `describe_page` gives the tutor the answer key because
the tutor needs it to teach; nothing in `ops()` carries an answer the student
has not been shown, because ops are only what was actually written down.
"""

from __future__ import annotations

from itertools import count
from typing import Iterable, Literal

from pydantic import BaseModel, Field

Where = Literal["below", "beside", "over"]
Colour = Literal["red", "green", "blue"]
Style = Literal["hand", "print"]


class At(BaseModel):
    """Which box a mark is on, and what on it the mark belongs to."""

    box: str
    where: Where = "below"
    at: int | None = Field(
        default=None,
        description="Which numbered thing on the page this mark is about, in "
        "the reading order `circle` counts in. Drawn against that thing "
        "instead of at the foot of the page, which is where an explanation "
        "turns into a list nobody reads.")


class Write(BaseModel):
    """A line in the tutor's hand: a worked step, a note, a correction."""

    id: str
    op: Literal["write"] = "write"
    on: At
    text: str
    style: Style = "hand"


class Circle(BaseModel):
    """A ring round something already printed on the page.

    `words` indexes the page's circleable things in reading order — the same
    numbering `describe_page` reports. Empty rings the whole page.
    """

    id: str
    op: Literal["circle"] = "circle"
    on: At
    words: list[int] = Field(default_factory=list)
    colour: Colour = "red"


class Point(BaseModel):
    """A dot to follow while the tutor talks. Live only: never kept."""

    id: str
    op: Literal["point"] = "point"
    on: At


class Fill(BaseModel):
    """The missing word, written into the gap it belongs in.

    `row` indexes the page's gaps in reading order, as `describe_page` numbers
    them. This is the mark that makes the kept paper worth keeping: the answer
    is in the blank, not in a list at the bottom.
    """

    id: str
    op: Literal["fill"] = "fill"
    on: At
    row: int
    text: str


class Erase(BaseModel):
    """Take a mark back. Names the mark's id, not the box it was on."""

    id: str
    op: Literal["erase"] = "erase"
    target: str


Op = Write | Circle | Point | Fill | Erase


class PaperNotOpen(RuntimeError):
    """No paper has been put in front of the student yet."""


class NoSuchPage(ValueError):
    """That page id is not on this paper."""


# ── reading the paper ───────────────────────────────────────────────────────
#
# Both enumerations below are duplicated in the web renderer, and they have to
# agree: the tutor says "fill gap 3" and the browser must write into the gap the
# tutor was looking at. They are defined here in reading order — blocks down the
# page, rows down each block — because that is the order a person reads a page
# in, and it is the only order two implementations can independently agree on.


def _gaps_in(block: dict) -> list[dict]:
    """Every place on this block a word is missing, in reading order.

    A gap is defined by what is *visibly* blank, never by the presence of an
    answer field. The student's copy has every `answer` deleted from it, so a
    renderer working from that copy cannot see them — and if the two sides
    counted gaps differently, "fill gap 3" would land in the wrong blank. A
    numbered row is always a gap; anything else is a gap when its text carries
    the `___` marker, which survives stripping because it is part of the prompt.
    """
    kind = block.get("kind")
    if kind in {"exercise", "choose", "build"}:
        rows = block.get("rows") or []
        return [
            {
                "prompt": r.get("prompt") or " ".join(r.get("parts") or []),
                "answer": r.get("answer", ""),
                "hint": r.get("hint", ""),
                "options": r.get("options") or [],
            }
            for r in rows
        ]
    if kind == "dialogue":
        return [
            {"prompt": f"{line.get('who', '')}: {line.get('says', '')}",
             "answer": line.get("answer", ""), "hint": "", "options": []}
            for line in (block.get("lines") or [])
            if "___" in (line.get("says") or "")
        ]
    if kind == "cards":
        return [
            {"prompt": item.get("label") or "",
             "answer": item.get("answer", ""), "hint": "", "options": []}
            for item in (block.get("items") or [])
            if "___" in (item.get("label") or "")
        ]
    if kind == "bubbles":
        return [
            {"prompt": turn.get("text", ""), "answer": turn.get("answer", ""),
             "hint": "", "options": []}
            for turn in (block.get("turns") or [])
            if "___" in (turn.get("text") or "")
        ]
    return []


def _targets_in(block: dict) -> list[str]:
    """Every printed thing on this block a ring can go round, in reading order.

    Every block kind that puts something separable on the page is here. It used
    to be the four language shapes only — cards, choices, word lists, speech
    bubbles — which meant a maths worksheet, made of rules, tables and numbered
    exercises, had nothing on it a tutor could point at. It would explain a step
    with no way to show which step, which is what "explaining in the air" is.

    Order is reading order, and it is a contract: the web renderer numbers the
    same things the same way, so `highlight=2` rings the third thing on the page
    in both places.
    """
    kind = block.get("kind")
    if kind == "cards":
        return [i.get("label") or i.get("lead") or "" for i in (block.get("items") or [])]
    if kind == "choose":
        return [opt for row in (block.get("rows") or []) for opt in (row.get("options") or [])]
    if kind == "list":
        return [i.get("term", "") for i in (block.get("items") or [])]
    if kind == "bubbles":
        return [t.get("text", "") for t in (block.get("turns") or [])]
    if kind == "rows":
        return [r.get("head", "") for r in (block.get("items") or [])]
    if kind == "hero":
        return [block.get("label", "")]
    if kind == "goals":
        return list(block.get("items") or [])
    if kind == "exercise":
        return [r.get("prompt", "") for r in (block.get("rows") or [])]
    if kind == "build":
        return [" ".join(r.get("parts") or []) for r in (block.get("rows") or [])]
    if kind == "table":
        return [(row[0] if row else "") for row in (block.get("rows") or [])]
    if kind == "dialogue":
        return [f"{l.get('who', '')}: {l.get('says', '')}"
                for l in (block.get("lines") or [])]
    return []


def gaps_on(slide: dict) -> list[dict]:
    return [g for block in (slide.get("blocks") or []) for g in _gaps_in(block)]


def targets_on(slide: dict) -> list[str]:
    return [t for block in (slide.get("blocks") or []) for t in _targets_in(block)]


class LivePaper:
    """One student's copy of one paper, during the hour it is being taught on.

    Holds the full sheet — answers included, because the tutor is server-side
    and needs the key — and the ordered list of marks made on it. The marks are
    the only thing that leaves: `ops()` is what the student's browser replays.
    """

    def __init__(self, sheet: dict | None = None, *, lesson_id: str = "") -> None:
        self._sheet: dict = sheet or {}
        self.lesson_id = lesson_id or self._sheet.get("lessonId", "")
        self._ops: list[Op] = []
        self._showing: str = ""
        self._ids = count(1)
        # How many marks have reached the student's browser. The web app appends
        # what it is sent, so sending a mark twice would draw it twice.
        self._sent = 0

    # -- what exists ---------------------------------------------------------

    @property
    def is_open(self) -> bool:
        return bool(self._sheet.get("slides"))

    @property
    def showing(self) -> str:
        """The page the student is looking at. Empty before the paper is shared."""
        return self._showing

    @property
    def title(self) -> str:
        return self._sheet.get("title", "")

    def pages(self) -> list[dict]:
        """Every page, in order: enough to choose one, not enough to teach from."""
        return [
            {"id": s.get("id", ""), "title": s.get("title", ""),
             "subtitle": s.get("subtitle", ""),
             "gaps": len(gaps_on(s)), "targets": len(targets_on(s))}
            for s in self._sheet.get("slides") or []
        ]

    def _slide(self, page_id: str) -> dict:
        for slide in self._sheet.get("slides") or []:
            if slide.get("id") == page_id:
                return slide
        raise NoSuchPage(page_id)

    def describe_page(self, page_id: str) -> dict:
        """One page as the tutor needs to see it: what is printed, what is
        missing, what the answers are, and how everything is numbered."""
        slide = self._slide(page_id)
        return {
            "id": slide.get("id"),
            "title": slide.get("title", ""),
            "subtitle": slide.get("subtitle", ""),
            "note": (slide.get("note") or {}).get("text", ""),
            "blocks": [
                {"kind": b.get("kind"), "content": _summarise(b)}
                for b in slide.get("blocks") or []
            ],
            # Numbered exactly as `fill_gap(row=…)` and `circle(words=[…])` take
            # them, so the tutor never has to guess which blank it is aiming at.
            "gaps": [{"row": i, **g} for i, g in enumerate(gaps_on(slide))],
            "circleable": [{"index": i, "text": t}
                           for i, t in enumerate(targets_on(slide))],
            "marks_so_far": [o.model_dump(mode="json") for o in self.marks_on(page_id)],
        }

    # -- marking it ----------------------------------------------------------

    def show(self, page_id: str) -> str:
        """Put one page in front of the student. Raises if there is no such page.

        Turning the page is recorded as a pointer on it. That is what carries
        the page change to the student's browser — which follows the last mark
        made — and a pointer is the right shape for it: it is a gesture during
        the class, so it moves the view without leaving anything on the copy
        the student takes away.
        """
        self._slide(page_id)
        self._showing = page_id
        self._add(Point(id=self._next_id(), on=At(box=page_id, where="over")))
        return page_id

    def _next_id(self) -> str:
        return f"m{next(self._ids)}"

    def _add(self, op: Op) -> Op:
        self._ops.append(op)
        return op

    def _at(self, page_id: str, where: Where, at: int | None = None) -> At:
        page = page_id or self._showing
        if not page:
            raise PaperNotOpen("No page is showing; call show() first.")
        self._slide(page)
        return At(box=page, where=where, at=at)

    def write(self, text: str, page_id: str = "", where: Where = "below",
              style: Style = "hand", at: int | None = None) -> Op:
        return self._add(Write(id=self._next_id(), on=self._at(page_id, where, at),
                               text=text, style=style))

    def circle(self, words: Iterable[int] = (), page_id: str = "",
               colour: Colour = "red") -> Op:
        page = page_id or self._showing
        chosen = [int(w) for w in words]
        if chosen:
            available = len(targets_on(self._slide(page or self._showing)))
            out_of_range = [w for w in chosen if w < 0 or w >= available]
            if out_of_range:
                raise ValueError(
                    f"Page {page!r} has {available} things to circle, numbered 0-"
                    f"{available - 1}; asked for {out_of_range}."
                )
        return self._add(Circle(id=self._next_id(), on=self._at(page, "over"),
                                words=chosen, colour=colour))

    def point(self, page_id: str = "", where: Where = "over") -> Op:
        return self._add(Point(id=self._next_id(), on=self._at(page_id, where)))

    def fill(self, row: int, text: str, page_id: str = "") -> Op:
        page = page_id or self._showing
        available = len(gaps_on(self._slide(page or self._showing)))
        if row < 0 or row >= available:
            raise ValueError(
                f"Page {page!r} has {available} gaps, numbered 0-{available - 1}; "
                f"asked for {row}."
            )
        return self._add(Fill(id=self._next_id(), on=self._at(page, "over"),
                              row=row, text=text))

    def erase(self, mark_id: str) -> Op:
        return self._add(Erase(id=self._next_id(), target=mark_id))

    # -- what came of it -----------------------------------------------------

    def ops(self) -> list[dict]:
        """Every mark in order, as the JSON the web app's `Ops` schema parses."""
        return [o.model_dump(mode="json") for o in self._ops]

    def settled(self) -> list[Op]:
        """What is actually on the paper: erases applied, pointers dropped.

        Mirrors `settled()` in ops.ts. A pointer is a gesture during the class,
        not a mark — keeping them would leave a scatter of dots on the copy a
        parent opens.
        """
        erased = {o.target for o in self._ops if isinstance(o, Erase)}
        return [o for o in self._ops
                if not isinstance(o, (Point, Erase)) and o.id not in erased]

    def marks_on(self, page_id: str) -> list[Op]:
        return [o for o in self.settled() if getattr(o, "on", None) and o.on.box == page_id]

    def marks_made(self) -> int:
        """How much the tutor actually wrote. A lesson with none was a lecture."""
        return len(self.settled())

    # -- getting it onto the student's screen --------------------------------

    def unsent(self) -> list[dict]:
        """Marks made since the last successful send, oldest first."""
        return [o.model_dump(mode="json") for o in self._ops[self._sent:]]

    def sent(self, count: int) -> None:
        """Record that the first `count` unsent marks arrived.

        Called only after the POST succeeds. A failed send leaves the cursor
        where it was, so the next one carries the marks that did not land rather
        than skipping past them — a lost mark is a hole in the middle of the
        lesson the student keeps.
        """
        self._sent = min(self._sent + max(count, 0), len(self._ops))


def _summarise(block: dict) -> str:
    """One line saying what is printed on a block, for the tutor to read."""
    kind = block.get("kind")
    if kind == "cards":
        return " · ".join(
            (i.get("lead") or "") + (f" {i.get('label')}" if i.get("label") else "")
            for i in (block.get("items") or [])
        ).strip()
    if kind == "bubbles":
        return " / ".join(t.get("text", "") for t in (block.get("turns") or []))
    if kind == "rows":
        return " · ".join(f"{r.get('head')}: {r.get('body')}"
                          for r in (block.get("items") or []))
    if kind == "hero":
        return f"{block.get('glyph', '')} {block.get('label', '')}".strip()
    if kind == "list":
        return " · ".join(f"{i.get('term')} = {i.get('gloss', '')}".strip(" =")
                          for i in (block.get("items") or []))
    if kind == "lines":
        return f"{block.get('count', 0)} ruled lines to write on"
    if kind == "bins":
        return "sort into: " + " · ".join(b.get("label", "")
                                          for b in (block.get("items") or []))
    if kind == "dialogue":
        return " / ".join(f"{line.get('who')}: {line.get('says')}"
                          for line in (block.get("lines") or []))
    if kind == "table":
        return " | ".join(block.get("head") or [])
    if kind in {"exercise", "choose", "build"}:
        rows = block.get("rows") or []
        return f"{len(rows)} numbered items"
    if kind == "goals":
        return " · ".join(block.get("items") or [])
    if kind == "photo":
        return f"photograph: {block.get('alt', '')}"
    return kind or ""
