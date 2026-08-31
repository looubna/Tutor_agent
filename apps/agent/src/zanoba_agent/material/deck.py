"""Rendering a lesson as a slide deck.

The reference decks are 4:3 landscape, one idea to a slide, a photograph on most
of them, and a persistent brand rail down the left. The material agents produce
items, not slides — an item is "the alphabet chart", which is three slides' worth
of content — so this module does two jobs: split items into slides that each
carry one idea, and lay those slides out.

Splitting is the interesting half. A slide the tutor has to scroll is not a
slide, so a long item becomes several, broken at its own headings first and at
paragraphs after that, with exercises pulled onto slides of their own.
"""

from __future__ import annotations

import re
import subprocess
import tempfile
from pathlib import Path
from typing import Any

import markdown as _markdown

from .brand import colour, glyph_data_uri, language_name, logo_data_uri
from .language_purity import check_text
from .layouts import render as render_component
from .deck_spec import MAX_WORDS_PER_SLIDE
from .worksheet import _find_chrome

# A picture counts as real when it has been produced, by either route. Gating on
# "generated" alone predated the photo search and quietly dropped every
# photograph the pipeline found rather than drew.
_PRODUCED = {"generated", "searched"}

# The words the deck itself puts on a slide. A German deck saying "Lernziele"
# was right by accident — every deck said it, including the English ones. There
# is no English on a German slide and no German on an English one, and that
# applies to the chrome as much as to the content.
_CHROME = {
    "german":  {"objectives": "Lernziele", "recap": "Zusammenfassung",
                "level": "Niveau", "lesson": "Lektion", "language": "Sprache"},
    "english": {"objectives": "Learning outcomes", "recap": "Summary",
                "level": "Level", "lesson": "Lesson", "language": "Language"},
    "french":  {"objectives": "Objectifs", "recap": "Résumé",
                "level": "Niveau", "lesson": "Leçon", "language": "Langue"},
    "spanish": {"objectives": "Objetivos", "recap": "Resumen",
                "level": "Nivel", "lesson": "Lección", "language": "Idioma"},
    "italian": {"objectives": "Obiettivi", "recap": "Riepilogo",
                "level": "Livello", "lesson": "Lezione", "language": "Lingua"},
}
_CHROME_DEFAULT = _CHROME["english"]


def chrome(package: dict) -> dict[str, str]:
    """The deck's own words, in the language the lesson is taught in."""
    key = str(package.get("target_language") or package.get("subject") or "").lower()
    return _CHROME.get(key, _CHROME_DEFAULT)

# 4:3 at a size that prints crisply.
SLIDE_W, SLIDE_H = 1000, 750

# The palette is the web app's, read from its own stylesheet rather than
# restated here — see `brand`. The deck a student downloads is the product, and
# it should look like the product rather than like the reference lessons it was
# modelled on.
_C = {name: colour(name) for name in (
    "primary", "primary-hover", "primary-tint", "foreground", "background",
    "surface", "border", "muted", "accent", "accent-ink", "accent-tint",
    "board", "board-foreground")}
_LOGO = logo_data_uri()
_GLYPH = glyph_data_uri()

_CSS = f"""
@page {{ size: {SLIDE_W}px {SLIDE_H}px; margin: 0; }}
* {{ box-sizing: border-box; margin: 0; padding: 0; }}
body {{ font-family: "Helvetica Neue", Inter, Arial, sans-serif;
       color: {_C['foreground']}; }}
.slide {{ width: {SLIDE_W}px; height: {SLIDE_H}px; position: relative;
         overflow: hidden; page-break-after: always;
         background: {_C['surface']}; }}
.rail {{ position: absolute; left: 0; top: 0; bottom: 0; width: 60px;
        background: linear-gradient(170deg, {_C['primary']} 0%,
                    {_C['primary-hover']} 100%); }}
/* The supplied lockup, not a redrawn mark. White-on-brand down the rail. */
.mark {{ position: absolute; left: 13px; top: 18px; width: 34px; height: 50px;
        z-index: 3; background: center/contain no-repeat url('{_GLYPH}');
        filter: brightness(0) invert(1); opacity: .96; }}
.band {{ position: absolute; left: 60px; right: 0; bottom: 0; height: 118px;
        background: {_C['primary-tint']}; }}
.num {{ position: absolute; left: 24px; bottom: 14px; color: #fff;
       font-size: 13px; z-index: 4; }}
.pane {{ position: absolute; left: 60px; right: 0; top: 0; bottom: 0;
        padding: 36px 34px 132px 38px; z-index: 2;
        display: flex; flex-direction: column; }}
/* Everything after the title and the instruction shares the remaining height.
   Without this the content sat against the top and left the lower half of every
   slide empty, which reads as an unfinished deck however good the content is. */
.pane > h1, .pane > .instr {{ flex: none; }}
/* `justify-content: center` on a block taller than its box spills BOTH ways, so
   a nine-picture grid printed its first row over the instruction line. Clip it,
   and start from the top once the content no longer fits. */
.fill {{ flex: 1; display: flex; flex-direction: column; justify-content: center;
        gap: 16px; min-height: 0; overflow: hidden; }}
.fill > * {{ flex-shrink: 0; }}
h1 {{ font-size: 33px; font-weight: 700; letter-spacing: -.4px; line-height: 1.14;
     color: {_C['foreground']}; }}
.instr {{ font-size: 17px; margin-top: 8px; color: {_C['muted']}; }}
.instr b, .instr strong {{ font-weight: 700; color: {_C['foreground']}; }}
.grid {{ display: flex; gap: 26px; margin-top: 26px; height: 400px; }}
.col {{ flex: 1; min-width: 0; display: flex; flex-direction: column; gap: 16px; }}
.photo {{ flex: 1; border-radius: 6px; min-height: 200px;
         background: {_C['primary-tint']} center/contain no-repeat; }}
.body {{ font-size: 19px; line-height: 1.5; }}
.body p {{ margin: 0 0 10px; }}
.body ul, .body ol {{ margin: 0 0 10px 22px; }}
.body li {{ margin: 5px 0; }}
.body strong {{ color: {_C['primary']}; }}
.body table {{ border-collapse: separate; border-spacing: 0 6px; width: 100%;
              font-size: 17px; }}
.body td, .body th {{ background: {_C['primary-tint']}; padding: 7px 12px;
                     text-align: left; }}
.body th {{ background: {_C['primary']}; color: #fff; font-weight: 700; }}
.bubble {{ background: {_C['surface']}; border-radius: 8px; padding: 20px 24px;
          font-size: 21px; font-weight: 700; text-align: center;
          border: 1px solid {_C['border']};
          box-shadow: 0 3px 14px rgba(23,21,29,.10); position: relative; }}
.bubble.l::after {{ content:""; position:absolute; left:-14px; top:34px;
                   border:14px solid transparent;
                   border-right-color:{_C['surface']}; border-left:0; }}
.bubble.r::after {{ content:""; position:absolute; right:-14px; top:34px;
                   border:14px solid transparent;
                   border-left-color:{_C['surface']}; border-right:0; }}
.prompt {{ background: {_C['primary-tint']}; border-radius: 6px; padding: 20px 24px;
          font-size: 19px; text-align: center; line-height: 1.45; }}
.gaps {{ display: flex; gap: 16px; margin-top: 20px; }}
.gap {{ flex: 1; background: {_C['primary-tint']}; border-radius: 6px;
       padding: 16px 12px; font-size: 17px; text-align: center; line-height: 1.7; }}
.gap:nth-child(even) {{ background: {_C['accent-tint']}; }}
.rule {{ display: inline-block; min-width: 92px;
        border-bottom: 1.5px solid {_C['muted']}; }}
.cover {{ position: absolute; inset: 0; display: flex; }}
.cover .art {{ width: 42%; background: {_C['board']} center/cover no-repeat; }}
.cover .side {{ flex: 1; background: linear-gradient(150deg, {_C['primary']},
               {_C['primary-hover']}); padding: 150px 60px 0; color: #fff;
               position: relative; }}
/* The cover carries the lockup in full, in white, above the title. */
.cover .logo {{ position: absolute; left: 60px; top: 62px; width: 190px;
               height: 56px; background: left center/contain no-repeat
               url('{_LOGO}'); filter: brightness(0) invert(1); }}
.cover .kicker {{ font-size: 17px; font-weight: 700; letter-spacing: 1.6px;
                 text-transform: uppercase; opacity: .85; }}
.cover h1 {{ font-size: 58px; line-height: 1.06; margin-top: 14px; color: #fff; }}
.cover .meta {{ position: absolute; left: 60px; bottom: 74px; display: flex;
               gap: 52px; color: #fff; }}
.cover .meta b {{ display: block; font-size: 13px; letter-spacing: 1.1px;
                 text-transform: uppercase; opacity: .8; }}
.cover .meta span {{ font-size: 17px; }}
.obj {{ background: {_C['surface']}; border-radius: 8px; padding: 22px 26px;
       font-size: 21px; border: 1px solid {_C['border']};
       box-shadow: 0 3px 14px rgba(23,21,29,.08); display: flex; gap: 15px;
       align-items: flex-start; }}
.obj em {{ width: 11px; height: 11px; border-radius: 50%;
          background: {_C['primary']}; flex: none; margin-top: 9px; }}
.ipa {{ font-size: 16px; color: {_C['muted']}; text-align: center; margin-top: 8px; }}
.tile {{ background: {_C['primary-tint']}; border-radius: 6px; padding: 20px 8px;
        font-size: 24px; text-align: center; }}
.tilewrap {{ flex: 1; }}
.tilenum {{ text-align: center; font-weight: 700; margin-bottom: 8px;
           font-size: 17px; color: {_C['primary']}; }}
.picgrid {{ display: flex; flex-wrap: wrap; gap: 18px; margin-top: 22px; }}
.pic {{ width: calc(33.333% - 12px); }}
.pic.two {{ width: calc(50% - 9px); }}
/* Every photograph, wherever it sits. Only `.pic .shot` was styled before, so a
   dialogue's scene and a rule table's illustration were placed with no
   background-size at all and rendered as a corner of themselves. */
/* `cover` fills the box by cropping, which on a fixed-height slot cut the top
   off every portrait — a dialogue's scene became a shoulder and a doorframe.
   `contain` shows the whole photograph; the tint behind it reads as a mount
   rather than as a gap. */
.shot {{ width: 100%; border-radius: 6px;
        background: {_C['primary-tint']} center/contain no-repeat; }}
/* A picture-set thumbnail is a small square of one object, where a crop is
   fine and letterboxing wastes most of the tile. The big scene photos keep
   `contain`, which is where cutting a face off actually mattered. */
.pic .shot {{ height: 150px; }}
/* The attribution a CC licence requires. Small and grey on purpose: an
   obligation, not part of the lesson. */
.credit {{ font-size: 9px; color: {_C['muted']}; margin-top: 3px;
          line-height: 1.3; }}
.pic .cap {{ display: flex; align-items: baseline; gap: 8px; margin-top: 7px; }}
.pic .n {{ font-weight: 700; font-size: 16px; color: {_C['primary']}; }}
.pic .w {{ font-size: 16px; }}
.pic .blank {{ flex: 1; border-bottom: 1.5px solid {_C['muted']}; height: 15px; }}
/* A dialogue is a list of turns, never a paragraph. One line per turn, the
   speaker set apart, the way every reference lesson prints one. */
.dialog {{ display: flex; flex-direction: column; gap: 11px; margin-top: 6px; }}
.turn {{ display: flex; gap: 10px; align-items: baseline; font-size: 19px;
        line-height: 1.4; background: {_C['primary-tint']}; border-radius: 8px;
        padding: 11px 16px; }}
.turn:nth-child(even) {{ background: {_C['accent-tint']}; }}
.turn .who {{ font-weight: 700; color: {_C['primary']}; white-space: nowrap;
             flex: none; }}
.turn .said {{ flex: 1; }}
/* ---- typed layouts. Each of these was written once and never reached while
   the agent emitted prose; they are the difference between courseware and a
   document with photographs in it. ---- */
/* A conjugation table has more columns than a photograph needs room, so the
   table's column takes what it needs and the picture takes the remainder —
   rather than the two overlapping, which is what equal flex gave. */
.grid:has(.rules) > .col:first-child {{ flex: 2 1 0; }}
.grid:has(.rules) > .col:last-child {{ flex: 1 1 0; }}
.rules {{ width: 100%; table-layout: fixed; border-collapse: separate;
         border-spacing: 6px;
         margin-top: 18px; font-size: 19px; }}
.rules th {{ background: {_C['primary']}; color: #fff; font-weight: 700;
            padding: 10px 14px; text-align: left; border-radius: 5px; }}
.rules td {{ background: {_C['primary-tint']}; padding: 12px 14px;
             word-break: break-word;
            border-radius: 5px; }}
.c {{ min-height: 22px; }}
.c.em {{ color: {_C['primary']}; font-weight: 700; }}
.note {{ margin-top: 16px; background: {_C['accent-tint']};
        border-left: 4px solid {_C['accent-ink']}; border-radius: 5px;
        padding: 13px 16px; font-size: 18px; font-weight: 600; }}
.vcard {{ background: {_C['primary-tint']}; border-radius: 10px;
         padding: 26px 28px; margin-top: 16px; }}
.vword {{ font-size: 40px; font-weight: 700; color: {_C['primary']};
         line-height: 1.1; }}
.vpos {{ font-size: 17px; color: {_C['muted']}; margin-top: 7px; }}
.vex {{ font-size: 20px; margin-top: 15px; }}
.tiles {{ display: flex; flex-wrap: wrap; gap: 12px; margin-top: 16px; }}
.tiles .tilewrap {{ flex: none; width: calc(20% - 10px); }}
.tilerows {{ display: flex; flex-direction: column; gap: 12px; margin-top: 18px; }}
.trow {{ display: flex; gap: 10px; }}
.trow .tile {{ flex: 1; font-size: 19px; padding: 14px 6px; }}
.cats {{ display: flex; gap: 14px; margin-top: 20px; }}
.cat {{ flex: 1; }}
.cathead {{ background: {_C['primary']}; color: #fff; font-weight: 700;
           font-size: 16px; padding: 8px 12px; border-radius: 5px 5px 0 0;
           text-align: center; }}
.catbox {{ height: 96px; background: {_C['primary-tint']};
          border-radius: 0 0 5px 5px; }}
.choices {{ display: flex; gap: 16px; margin-top: 22px; }}
.choice {{ flex: 1; background: {_C['primary-tint']}; border-radius: 8px;
          padding: 20px 18px; font-size: 21px; display: flex; gap: 10px;
          align-items: baseline; }}
.choice .n {{ font-weight: 700; color: {_C['primary']}; }}
.qlist {{ display: flex; flex-direction: column; gap: 11px; margin-top: 16px; }}
.qrow {{ display: flex; gap: 11px; align-items: baseline; font-size: 19px;
        background: {_C['primary-tint']}; border-radius: 6px; padding: 11px 16px; }}
.qrow .n {{ font-weight: 700; color: {_C['primary']}; flex: none; }}
.qrow .q {{ flex: 1; }}
.worked {{ font-size: 17px; color: {_C['muted']}; margin-top: 10px; }}
.bank {{ display: flex; flex-wrap: wrap; gap: 9px; margin-top: 18px; }}
.chip {{ background: {_C['accent-tint']}; border-radius: 20px; padding: 7px 15px;
        font-size: 17px; }}
.roles {{ display: flex; gap: 20px; margin-top: 20px; }}
.role {{ flex: 1; background: {_C['primary-tint']}; border-radius: 10px;
        padding: 20px; }}
.rolename {{ font-weight: 700; font-size: 21px; color: {_C['primary']}; }}
.roletask {{ font-size: 18px; margin-top: 8px; }}
.rolephrases {{ margin: 12px 0 0 18px; font-size: 17px; }}
.rolephrases li {{ margin: 5px 0; }}
.summary {{ display: flex; flex-direction: column; gap: 15px; margin-top: 16px; }}
.sgroup ul {{ margin: 6px 0 0 20px; font-size: 19px; }}
.sgroup li {{ margin: 4px 0; }}
.shead {{ font-weight: 700; font-size: 19px; color: {_C['primary']}; }}
.wordlist {{ display: flex; gap: 34px; margin-top: 16px; }}
.wordlist ul {{ flex: 1; margin-left: 20px; font-size: 18px; }}
.wordlist li {{ margin: 6px 0; }}
"""


def _md(text: str) -> str:
    return _markdown.markdown(text or "", extensions=["tables", "sane_lists"])


# "Lisa:", "Herr Müller:", "Person A:" — a speaker label opening a turn.
#
# Anchored to a sentence boundary, which is the whole difficulty. A pattern that
# merely looks for capitalised words before a colon reads
#
#     ... Hier ist das Buch. Herr Müller: Und wo ist die Schere?
#
# as a speaker called "Buch. Herr Müller", because the previous sentence's last
# word is capitalised too. So a turn may begin only at the start of the text,
# after a newline, or after sentence-ending punctuation — and a speaker's name
# may not contain a full stop.
_SPEAKER = re.compile(
    r"(?:\A|(?<=[.!?\u201c\u201d])\s+|\n\s*)"
    r"([A-ZÄÖÜ][\wÄÖÜäöüß\-]*(?:\s+[A-ZÄÖÜ][\wÄÖÜäöüß\-]*){0,2})"
    r"\s*:\s+(?=[A-ZÄÖÜ0-9\u201e\u201c\"'(])",
    re.UNICODE)


def is_dialogue(text: str) -> bool:
    """Does this read as an exchange between speakers rather than as prose?"""
    return len(_SPEAKER.findall(text or "")) >= 2


def _dialogue_turns(text: str) -> list[tuple[str, str]]:
    """Split a dialogue into (speaker, line) pairs.

    Split on the speaker labels rather than on newlines, because the thing that
    actually goes wrong is a model writing every turn into one paragraph:

        Herr Müller: Hallo Tim! Wo ist das Buch? Tim: Hallo Herr Müller! ...

    Markdown collapses single newlines anyway, so even a correctly line-broken
    dialogue arrives here as one run of text. Splitting on the labels handles
    both, and a dialogue on the slide is one turn per line either way.
    """
    plain = re.sub(r"[*_`]", "", text or "").strip()
    matches = list(_SPEAKER.finditer(plain))
    if len(matches) < 2:
        return []
    turns: list[tuple[str, str]] = []
    for index, match in enumerate(matches):
        end = matches[index + 1].start() if index + 1 < len(matches) else len(plain)
        line = plain[match.end():end].strip()
        if line:
            turns.append((match.group(1).strip(), line))
    return turns


def _dialogue_html(text: str) -> str:
    """One turn per line, the speaker in brand colour, as the references print it."""
    turns = _dialogue_turns(text)
    if not turns:
        return ""
    rows = "".join(
        f'<div class="turn"><span class="who">{who}</span>'
        f'<span class="said">{line}</span></div>'
        for who, line in turns)
    return f'<div class="dialog">{rows}</div>'


def _words(text: str) -> int:
    return len(re.findall(r"\S+", re.sub(r"<[^>]+>", " ", text or "")))


def _split_content(content: str) -> list[tuple[str, str]]:
    """Break one item's markdown into (heading, chunk) pairs of slide size.

    Headings first, because the author already decided those are the seams.
    Anything still too long is split at paragraphs — never mid-sentence, which
    would put half a rule on one slide and half on the next.
    """
    blocks = re.split(r"\n(?=#{2,4}\s)", content or "")
    out: list[tuple[str, str]] = []
    for block in blocks:
        block = block.strip()
        if not block:
            continue
        heading = ""
        match = re.match(r"^#{2,4}\s*(.+)", block)
        if match:
            heading = match.group(1).strip()
            block = block[match.end():].strip()
        if not block:
            continue
        if _words(block) <= MAX_WORDS_PER_SLIDE:
            out.append((heading, block))
            continue
        buffer: list[str] = []
        for para in re.split(r"\n\s*\n", block):
            candidate = "\n\n".join(buffer + [para])
            if buffer and _words(candidate) > MAX_WORDS_PER_SLIDE:
                out.append((heading, "\n\n".join(buffer)))
                heading = ""  # only the first slice keeps the heading
                buffer = [para]
            else:
                buffer.append(para)
        if buffer:
            out.append((heading, "\n\n".join(buffer)))
    return out


def target_language_objectives(package: dict, objectives: dict) -> list[str]:
    """The Lernziele lines, but only if they are actually in the lesson's language.

    The agent is asked to write these in the target language. When it does not —
    and it does not reliably — the fallback used to be the curriculum's own
    objectives, which are authored in English for the teacher. That put two
    English slides in the middle of a German deck.

    So the fallback is checked rather than trusted, with the same purity test the
    material itself is held to. English that fails the test is dropped, and the
    slide renders with its heading and no list. An empty Lernziele slide is a
    visible gap; an English one on a German deck is a defect that looks
    deliberate, and the deck is the thing a student sees.
    """
    written = [o.strip() for o in package.get("learner_objectives", []) or []
               if str(o).strip()]
    if written:
        return written

    language = str(package.get("target_language") or package.get("subject") or "")
    fallback = [o.get("statement", "") for o in objectives.get("objectives", [])
                if str(o.get("statement", "")).strip()]
    if not fallback or language.lower() in {"", "english"}:
        return fallback
    return [line for line in fallback
            if check_text(line, language).get("is_target_language")]


def build_slides(package: dict, plan: dict, objectives: dict) -> list[dict[str, Any]]:
    """Turn a material package into slides, one idea each."""
    activities = {a.get("id"): a for a in plan.get("activities", [])}
    subject = (package.get("subject") or "").title()
    title = (plan.get("target_item_title") or package.get("target_item_title")
             or package.get("target_item_id", ""))

    # The cover's left panel is a photograph from the lesson itself. Left empty
    # it printed as a dark void down 42% of the first page, which is the first
    # thing a student sees.
    def first_photo() -> list[dict]:
        """The photograph for the cover panel — a SCENE, not the first picture.

        The panel is 42% of the width and the full height, so whatever goes in
        it is cropped to a tall strip. A vocabulary lesson's first picture is a
        close-up of one object on a plain ground, and cropped that way a
        photograph of a waving hand became an unrecognisable brown shape down
        the side of the cover — the first thing a student sees.

        A scene survives that crop: it has a person, a room, a horizon, and a
        vertical slice of it still reads as a place. So the dialogue's scene and
        the role-play's picture are preferred, and an isolated object is the
        last resort rather than the first.
        """
        def usable(image) -> bool:
            return (isinstance(image, dict)
                    and str(image.get("provider", "")).lower() in _PRODUCED
                    and bool(image.get("url")))

        scenes, objects = [], []
        for item in package.get("items", []):
            component = item.get("slide") or {}
            # A situation, with people in a place. Crops well.
            for field in ("scene", "picture", "illustration"):
                if usable(component.get(field)):
                    scenes.append(component[field])
            # One thing on a plain ground. Crops badly.
            for picture in component.get("pictures") or []:
                if usable(picture):
                    objects.append(picture)
            for image in item.get("images") or []:
                if usable(image):
                    objects.append(image)
            for exercise in item.get("exercises") or []:
                if usable(exercise.get("image")):
                    objects.append(exercise["image"])

        chosen = scenes or objects
        return [chosen[0]] if chosen else []

    words = chrome(package)
    learner_objectives = target_language_objectives(package, objectives)

    slides: list[dict[str, Any]] = [{
        "kind": "cover", "title": title, "subject": subject, "words": words,
        "language": language_name(package.get("subject", "")),
        "level": plan.get("level_id", ""), "focus": plan.get("focus") or "",
        "lesson_id": package.get("target_item_id", ""),
        "images": first_photo(), "body": "",
    }, {
        "kind": "objectives", "title": words["objectives"],
        "objectives": learner_objectives,
        "images": [], "body": "",
    }]

    for item in package.get("items", []):
        activity = activities.get(item.get("activity_id"), {})
        phase = item.get("stage") or activity.get("phase") or item.get("kind", "")
        component = item.get("slide")

        # A typed component IS the slide. One item, one designed layout — the
        # renderer no longer manufactures an intro slide out of a seven-word
        # sentence and then two more for the exercises, which is how a lesson
        # came out as three consecutive slides with the same title on them.
        if component:
            slides.append({
                "kind": "component",
                "layout": component.get("kind", ""),
                "phase": phase,
                "title": component.get("title") or item.get("title", ""),
                "instruction": component.get("instruction") or item.get("instruction", ""),
                "component": component,
                "images": [], "body": "",
            })
            continue

        # Fallback for an item written as prose. Kept because a lesson with one
        # unusual item should still render, but this is the path that produces
        # text in a box and the layouts exist to avoid it.
        pictures = [i for i in (item.get("images") or [])
                    if str(i.get("provider", "")).lower() in _PRODUCED]
        chunks = _split_content(item.get("content", "")) or [("", "")]
        for index, (heading, chunk) in enumerate(chunks):
            if not chunk.strip():
                continue
            slides.append({
                "kind": item.get("kind", "explanation"),
                "phase": phase,
                "title": heading or item.get("title", ""),
                "instruction": item.get("instruction", ""),
                "images": ([pictures[index]] if index < len(pictures)
                           else ([pictures[index % len(pictures)]] if pictures else [])),
                "body": chunk,
            })

        exercises = item.get("exercises") or []
        per_slide = 6 if any((e.get("image") or {}).get("url")
                             for e in exercises) else 4
        for start_at in range(0, len(exercises), per_slide):
            slides.append({
                "kind": "practice", "phase": phase,
                "title": item.get("title", "Übung"),
                "instruction": item.get("instruction", ""),
                "images": [], "body": "",
                "exercises": exercises[start_at:start_at + per_slide],
            })

    slides.append({
        "kind": "recap", "phase": "recap", "title": words["recap"],
        "instruction": "", "images": [], "body": "",
        "objectives": learner_objectives,
    })

    for number, slide in enumerate(slides, 1):
        slide["number"] = number
    return slides


def _slide_html(slide: dict) -> str:
    n = slide.get("number", "")
    kind = slide.get("kind")
    images = slide.get("images") or []
    art = images[0].get("url") if images else ""

    if kind == "cover":
        _w = slide.get("words") or _CHROME_DEFAULT
        return f"""<div class="slide"><div class="cover">
  <div class="art" style="background-image:url('{art}')"></div>
  <div class="side">
    <div class="logo"></div>
    <div class="kicker">{slide.get('focus') or slide.get('subject','')}</div>
    <h1>{slide.get('title','')}</h1>
    <div class="meta">
      <div><b>{_w['level']}</b><span>{slide.get('level','')}</span></div>
      <div><b>{_w['lesson']}</b><span>{slide.get('lesson_id','')}</span></div>
      <div><b>{_w['language']}</b><span>{slide.get('language') or slide.get('subject','')}</span></div>
    </div>
  </div></div></div>"""

    head = (f'<div class="rail"></div><div class="mark"></div>'
            f'<div class="band"></div><div class="num">{n}</div>')

    if kind in {"objectives", "recap"}:
        cards = "".join(
            f'<div class="obj"><em></em><div>{o}</div></div>'
            for o in slide.get("objectives", []))
        return (f'<div class="slide">{head}<div class="pane"><h1>{slide.get("title","")}</h1>'
                f'<div class="col" style="margin-top:34px;gap:18px">{cards}</div></div></div>')

    if kind == "component":
        inner = render_component(slide.get("component") or {})
        instr = (f'<div class="instr">{_md(slide.get("instruction",""))}</div>'
                 if slide.get("instruction") else "")
        return (f'<div class="slide">{head}<div class="pane">'
                f'<h1>{slide.get("title","")}</h1>{instr}'
                f'<div class="fill">{inner}</div></div></div>')

    if kind == "practice":
        exercises = slide.get("exercises", [])
        # A picture-matching or picture-naming task is a grid of numbered
        # photographs, one per item, with a blank beside each for the word —
        # the shape the reference decks use. Without this branch the pictures
        # would be generated and then never appear on the slide.
        pictures = [e for e in exercises
                    if (e.get("image") or {}).get("url")]
        if pictures:
            width = "pic two" if len(pictures) <= 4 else "pic"
            cells = []
            for number, exercise in enumerate(pictures, 1):
                url = exercise["image"]["url"]
                # The word goes on the slide only when it is given; when the
                # learner has to supply it, the caption is a blank.
                given = str(exercise.get("prompt", "")).strip()
                shows_word = bool(given) and "_" not in given
                caption = (f'<span class="w">{given}</span>' if shows_word
                           else '<span class="blank"></span>')
                cells.append(
                    f'<div class="{width}">'
                    f'<div class="shot" style="background-image:url(\'{url}\')"></div>'
                    f'<div class="cap"><span class="n">{number}</span>{caption}</div>'
                    f'</div>')
            return (f'<div class="slide">{head}<div class="pane">'
                    f'<h1>{slide.get("title","")}</h1>'
                    f'<div class="instr">{_md(slide.get("instruction",""))}</div>'
                    f'<div class="picgrid">{"".join(cells)}</div></div></div>')

        gaps = "".join(
            f'<div class="gap">{e.get("prompt","")}<br><span class="rule"></span></div>'
            for e in exercises)
        return (f'<div class="slide">{head}<div class="pane"><h1>{slide.get("title","")}</h1>'
                f'<div class="instr">{_md(slide.get("instruction",""))}</div>'
                f'<div class="gaps">{gaps}</div></div></div>')

    # A dialogue renders as turns, one per line. Markdown would set the whole
    # exchange as a single paragraph, which is how a conversation ended up
    # printed as a wall of run-together speech.
    raw = slide.get("body", "")
    body = (f'<div class="body">{_dialogue_html(raw)}</div>' if is_dialogue(raw)
            else f'<div class="body">{_md(raw)}</div>')
    if art:
        inner = (f'<div class="grid"><div class="col">{body}</div>'
                 f'<div class="col"><div class="photo" style="background-image:url(\'{art}\')"></div></div></div>')
    else:
        inner = f'<div class="grid"><div class="col">{body}</div></div>'
    instr = (f'<div class="instr">{_md(slide.get("instruction",""))}</div>'
             if slide.get("instruction") else "")
    return (f'<div class="slide">{head}<div class="pane"><h1>{slide.get("title","")}</h1>'
            f'{instr}{inner}</div></div>')


def render_html(slides: list[dict]) -> str:
    return ("<!doctype html><meta charset='utf-8'><style>" + _CSS + "</style>"
            + "".join(_slide_html(s) for s in slides))


def render_pdf(html: str, out_path: Path, timeout: int = 90) -> Path:
    """Print the deck. Chrome writes the file then may not exit; the file wins."""
    chrome = _find_chrome()
    if chrome is None:
        raise RuntimeError("No Chrome or Chromium found to print the deck.")
    out_path = Path(out_path).resolve()
    out_path.parent.mkdir(parents=True, exist_ok=True)
    if out_path.exists():
        out_path.unlink()
    with tempfile.TemporaryDirectory() as tmp:
        source = Path(tmp) / "deck.html"
        source.write_text(html, encoding="utf-8")
        process = subprocess.Popen(
            [chrome, "--headless=new", "--disable-gpu", "--no-sandbox",
             "--no-first-run", "--disable-extensions", "--disable-dev-shm-usage",
             f"--user-data-dir={tmp}/profile", "--no-pdf-header-footer",
             "--virtual-time-budget=15000",
             f"--print-to-pdf={out_path}", source.as_uri()],
            stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        try:
            process.wait(timeout=timeout)
        except subprocess.TimeoutExpired:
            process.kill()
            process.wait(timeout=10)
    if not out_path.exists() or out_path.stat().st_size == 0:
        raise RuntimeError(f"Chrome produced no deck at {out_path}")
    return out_path


def build(package: dict, plan: dict, objectives: dict, out_dir: Path) -> dict:
    """Slides, HTML and PDF for one lesson."""
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    slides = build_slides(package, plan, objectives)
    html = render_html(slides)
    (out_dir / "deck.html").write_text(html, encoding="utf-8")
    return {"slides": slides, "pdf": render_pdf(html, out_dir / "deck.pdf")}
