"""The Zanoba brand, as the deck needs it.

The deck used to be drawn in a palette nobody chose — a purple-to-magenta
gradient copied off the reference lessons, which is another company's brand. A
lesson a student downloads is the product; it should look like the product.

Two things live here. The colours, read from the web app's `globals.css` when it
is on disk so the two cannot drift apart, and falling back to a vendored copy
when it is not — the agent deploys to Cloud Run on its own, and a deck that
renders unbranded in production because the frontend was not in the image would
be a strange way to fail. And the logo, vendored beside this file and embedded
in the HTML as a data URI, because Chrome prints the deck with no network and a
remote `src` would silently produce a blank corner on every slide.
"""

from __future__ import annotations

import base64
import re
from functools import lru_cache
from pathlib import Path

# The web app's tokens, copied from apps/web/src/app/globals.css. Kept as the
# fallback rather than the source of truth: when that file is present it wins,
# so a colour changed in one place does not have to be remembered in two.
_VENDORED = {
    "background": "#fbf9f9",
    "foreground": "#17151d",
    "surface": "#ffffff",
    "border": "#e7e3e6",
    "muted": "#5d5866",
    "primary": "#743ee4",
    "primary-hover": "#5f33bb",
    "primary-tint": "#f4f0fd",
    "success": "#1f8a5f",
    "success-tint": "#e5f4ec",
    "danger": "#c23b3b",
    "board": "#0c1226",
    "board-foreground": "#eef1f7",
    "accent": "#c6f64d",
    "accent-ink": "#4d7c0f",
    "accent-tint": "#eef7d9",
    "brand": "#743ee4",
}

# Where the frontend lives relative to this file, in the monorepo.
_GLOBALS_CSS = (Path(__file__).resolve().parents[4]
                / "web" / "src" / "app" / "globals.css")

_LOGO = Path(__file__).with_name("brand") / "logo.png"
# The lockup is wide (722x347); squashed into the 60px rail it renders as an
# illegible smudge. The glyph alone is nearly square and reads at 40px, so the
# rail gets the mark and the cover gets the full lockup.
_GLYPH = Path(__file__).with_name("brand") / "glyph.png"

# What a language is called in itself. A German deck saying "SPRACHE: German"
# has an English word on its cover, which is the whole thing we are avoiding.
ENDONYM = {
    "german": "Deutsch", "french": "Français", "spanish": "Español",
    "italian": "Italiano", "english": "English", "arabic": "العربية",
    "chinese": "中文", "korean": "한국어",
}


def language_name(subject: str) -> str:
    """The language's own name for itself, for the deck cover."""
    return ENDONYM.get((subject or "").strip().lower(), (subject or "").title())

# The deck is a printed document. It takes the light palette always — the
# viewer's system theme has no bearing on a PDF, and a dark deck would burn
# through a student's printer.
_LIGHT_BLOCK = re.compile(r":root\s*\{(.*?)\}", re.S)
_TOKEN = re.compile(r"--([a-z-]+)\s*:\s*(#[0-9a-fA-F]{3,8}|[a-z-]+)\s*;")


@lru_cache(maxsize=1)
def tokens() -> dict[str, str]:
    """The brand colours, preferring the frontend's own stylesheet."""
    colours = dict(_VENDORED)
    try:
        css = _GLOBALS_CSS.read_text(encoding="utf-8")
    except OSError:
        return colours
    match = _LIGHT_BLOCK.search(css)
    if not match:
        return colours
    for name, value in _TOKEN.findall(match.group(1)):
        if value.startswith("#"):
            colours[name] = value
    return colours


def colour(name: str) -> str:
    """One token by name, e.g. colour('primary')."""
    return tokens().get(name, _VENDORED.get(name, "#000000"))


def _data_uri(path: Path) -> str:
    try:
        raw = path.read_bytes()
    except OSError:
        return ""
    return "data:image/png;base64," + base64.b64encode(raw).decode("ascii")


@lru_cache(maxsize=1)
def glyph_data_uri() -> str:
    """The mark alone, for the narrow rail down the side of every slide."""
    return _data_uri(_GLYPH) or logo_data_uri()


@lru_cache(maxsize=1)
def logo_data_uri() -> str:
    """The logo as a data URI, or "" when the file is missing.

    Embedded rather than linked because Chrome prints the deck with networking
    effectively unavailable; a remote src would leave a blank corner on every
    slide and nothing would report it.
    """
    return _data_uri(_LOGO)
