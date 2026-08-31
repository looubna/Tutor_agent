"""What a lesson deck must be, and a checker that says whether it is.

Derived from the reference decks in `German/A1-1/CH-1` — professionally produced
A1 lessons. The gap between those and what this pipeline produced is not polish,
it is format: they are ~40 landscape slides carrying one idea each, with a
photograph on most of them, and the pipeline produced an 8-page A4 document of
dense tables and no pictures at all.

The requirements below are the checkable half of that difference. Anything a
model could argue about is left to the Quality checker's judgement; anything
countable is counted here, because "does this have images" should not be a
matter of opinion.

The image rule is the strict one, and deliberately so. A slide specification
that says `provider: "pending"` is a promise, not a picture. A deck of promises
looks complete in JSON and arrives at the lesson blank.
"""

from __future__ import annotations

import re
from typing import Any

# ---------------------------------------------------------------- format ----

# The reference decks run 38-41 slides for a 60-minute lesson. Below the floor
# a deck is a handout with headings; the ceiling exists because a slide the
# tutor never reaches was time spent generating nothing.
MIN_SLIDES = 20
TARGET_SLIDES = 38
MAX_SLIDES = 50

# 4:3 landscape, as every reference deck is.
ASPECT_RATIO = 4 / 3

# ------------------------------------------------------------- per slide ----

# One idea per slide is the whole design. The reference decks average well under
# this; the limit is a ceiling on the worst slide, not a target.
MAX_WORDS_PER_SLIDE = 60

# A slide with a title and nothing else is a section break, which is fine, but
# a content slide needs something to do.
MIN_WORDS_PER_CONTENT_SLIDE = 3

# ---------------------------------------------------------------- images ----

# In the reference decks a photograph appears on essentially every content
# slide. The earlier 0.55 was measured too generously and let through decks that
# were half prose; the published lessons this is derived from are visual almost
# throughout, and only the closing summary and the word list go without.
MIN_IMAGE_COVERAGE = 0.85

# Slides that never need an image: the alphabet table, an IPA drill, a summary.
# Named so the coverage rule is not applied to slides it would be wrong for.
# The few slides a published deck genuinely leaves bare: the closing summary,
# the word list, the self-assessment. Everything else carries a picture.
#
# This set used to be much larger, which is how a deck of eight prose slides
# passed the coverage rule — most of its stages were exempt from it.
TEXT_ONLY_PHASES = {
    "recap", "summary", "review", "reflection", "final-check", "assessment",
}

# ------------------------------------------------------------- structure ----

REQUIRED_OPENING = ["cover", "objectives"]
REQUIRED_CLOSING = ["recap"]

# The instruction line on an activity slide starts with an imperative, in bold:
# "Sprich nach.", "Lies den Text.", "Ergänze die Phrasen unten."
INSTRUCTION_PATTERN = re.compile(r"^\s*(\*\*)?[A-ZÄÖÜ][a-zäöüß]+\b", re.UNICODE)


class DeckViolation(dict):
    """One requirement not met. A dict so it crosses a tool boundary cleanly."""


def _words(text: str) -> int:
    return len(re.findall(r"\S+", re.sub(r"<[^>]+>", " ", text or "")))


def check_deck(deck: dict[str, Any]) -> dict:
    """Check a deck against the format requirements.

    Returns the violations found, each with a severity and the slide at fault.
    Only counts things: slide totals, image coverage, words per slide, missing
    alt text, unfulfilled image promises. Judgement calls — is this photograph
    relevant, is this German natural — belong to the Quality checker.
    """
    slides = deck.get("slides") or []
    violations: list[DeckViolation] = []

    def fail(rule: str, detail: str, severity: str = "high", slide: Any = "") -> None:
        violations.append(
            DeckViolation(rule=rule, detail=detail, severity=severity, slide=str(slide))
        )

    # --- length ---
    if len(slides) < MIN_SLIDES:
        fail("slide_count",
             f"{len(slides)} slides; a 60-minute lesson needs at least {MIN_SLIDES} "
             f"(the reference decks run ~{TARGET_SLIDES})")
    elif len(slides) > MAX_SLIDES:
        fail("slide_count", f"{len(slides)} slides exceeds {MAX_SLIDES}", "medium")

    # --- opening and closing ---
    kinds = [str(s.get("kind", "")).lower() for s in slides]
    for i, required in enumerate(REQUIRED_OPENING):
        if i >= len(kinds) or kinds[i] != required:
            fail("structure",
                 f"slide {i + 1} must be the {required} slide, found "
                 f"{kinds[i] if i < len(kinds) else 'nothing'!r}")
    if kinds and not any(k in REQUIRED_CLOSING for k in kinds[-3:]):
        fail("structure", "the deck does not end with a recap slide", "medium")

    # --- images ---
    needs_image = [
        s for s in slides
        if str(s.get("kind", "")).lower() not in {"cover", "objectives"}
        and str(s.get("phase", "")).lower() not in TEXT_ONLY_PHASES
    ]
    with_image = [s for s in needs_image if s.get("images")]
    coverage = len(with_image) / len(needs_image) if needs_image else 1.0
    if coverage < MIN_IMAGE_COVERAGE:
        fail("image_coverage",
             f"{len(with_image)}/{len(needs_image)} content slides carry an image "
             f"({coverage:.0%}); the reference decks carry one on at least "
             f"{MIN_IMAGE_COVERAGE:.0%}")

    for slide in slides:
        number = slide.get("number", "?")
        for image in slide.get("images") or []:
            provider = str(image.get("provider", "pending")).lower()
            url = str(image.get("url", "")).strip()
            if provider == "pending" or not url:
                fail("image_not_produced",
                     "image is specified but not produced — a deck of image "
                     "promises arrives at the lesson blank",
                     slide=number)
            if not str(image.get("alt_text", "")).strip():
                fail("image_alt_text", "image has no alt text", "medium", slide=number)

    # --- one idea per slide ---
    for slide in slides:
        number = slide.get("number", "?")
        body = " ".join(
            str(slide.get(field, "")) for field in ("body", "content", "instruction")
        )
        # Exercises and objective lists are content even though neither is prose.
        body += " ".join(str(e.get("prompt", "")) for e in slide.get("exercises") or [])
        body += " ".join(str(o) for o in slide.get("objectives") or [])
        count = _words(body)
        if count > MAX_WORDS_PER_SLIDE:
            fail("slide_density",
                 f"{count} words; one idea per slide means at most "
                 f"{MAX_WORDS_PER_SLIDE}", "medium", slide=number)
        if str(slide.get("kind", "")).lower() not in {"cover", "objectives", "section", "practice"}:
            if count < MIN_WORDS_PER_CONTENT_SLIDE:
                fail("empty_slide", "content slide has no content", slide=number)
            if not str(slide.get("title", "")).strip():
                fail("missing_title", "content slide has no title", "medium", slide=number)

    # --- instructions ---
    for slide in slides:
        if slide.get("exercises") and not str(slide.get("instruction", "")).strip():
            fail("missing_instruction",
                 "an activity slide needs an instruction line telling the student "
                 "what to do, e.g. 'Lies den Text.'",
                 "medium", slide=slide.get("number", "?"))

    blocking = [v for v in violations if v["severity"] == "high"]
    return {
        "compliant": not blocking,
        "slide_count": len(slides),
        "image_coverage": round(coverage, 2),
        "images_produced": sum(
            1 for s in slides for i in (s.get("images") or [])
            if str(i.get("provider", "pending")).lower() != "pending"
        ),
        "images_pending": sum(
            1 for s in slides for i in (s.get("images") or [])
            if str(i.get("provider", "pending")).lower() == "pending"
        ),
        "violations": violations,
        "blocking_count": len(blocking),
    }
