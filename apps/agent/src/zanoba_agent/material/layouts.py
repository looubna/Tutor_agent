"""Drawing each typed slide component.

One function per layout, each producing the inside of a slide's pane. They exist
because the renderer used to receive a paragraph of markdown and have to guess:
it could guess about five shapes, so everything else became text in a box, and
the CSS written for vocabulary cards and sorting grids was never once reached.

Now the agent names the layout and this module draws it. The mapping is total —
every component has a function, and adding a component without one fails the
tests rather than silently rendering blank.

Nothing here decides anything pedagogical. It is a renderer: it takes what the
blueprint specified and the generator wrote, and puts it on the page the way the
reference lessons put it on the page.
"""

from __future__ import annotations

import html
import re
from typing import Any

from .brand import colour


def esc(text: Any) -> str:
    return html.escape(str(text or ""), quote=False)


# The only markup a cell may carry. The agent writes "wohn-<b>e</b>" to bold the
# ending it is teaching — which `Cell.emphasis` cannot express, because that
# bolds the whole cell. Everything else is escaped, so a stray angle bracket in
# a learner's word still prints as an angle bracket rather than as a tag.
_INLINE = ("b", "i", "strong", "em", "u")


def rich(text: Any) -> str:
    """Escape a string, keep a little emphasis, and honour its line breaks.

    A multiple-choice item arrives as one string with its options on separate
    lines. HTML collapses a real newline to a space, so the three options ran
    together into a paragraph; and where the newline had been escaped along the
    way it printed as a literal backslash-n in the middle of the sentence. Both
    forms are line breaks the agent meant, so both become one.
    """
    out = esc(text)
    for tag in _INLINE:
        out = out.replace(f"&lt;{tag}&gt;", f"<{tag}>")
        out = out.replace(f"&lt;/{tag}&gt;", f"</{tag}>")
    # The escaped literal first, or its backslash would survive the real one.
    out = out.replace("\\r\\n", "<br>").replace("\\n", "<br>")
    out = out.replace("\r\n", "<br>").replace("\n", "<br>")
    return out


def _rule(width: int = 110) -> str:
    """A line to write on. A blank must look like a blank on paper."""
    return f'<span class="rule" style="min-width:{width}px"></span>'


def _cell(cell: dict) -> str:
    text = str(cell.get("text", "")).strip()
    blank = not text or text in {"___", "_", "__"}
    inner = _rule(90) if blank else rich(text)
    klass = "c em" if cell.get("emphasis") else "c"
    return f'<div class="{klass}">{inner}</div>'


def _photo(picture: dict | None, height: int = 210) -> str:
    """One picture. No source line — the slide is the lesson, not the paperwork.

    Where the photograph came from is still recorded on the picture and kept in
    the material JSON, so the question is answerable. It is simply not printed:
    a credit under every image is clutter on a teaching slide, and the search is
    restricted to a library whose licence does not require one, so nothing is
    being taken without permission. See `photos.PROVIDERS`.
    """
    if not picture or not picture.get("url"):
        return ""
    return (f'<div class="shot" style="height:{height}px;background-image:'
            f'url(\'{esc(picture["url"])}\')"></div>')


def _unnumbered(text: Any) -> str:
    """Drop a leading "1." or "3)" the agent wrote into an item's own text.

    The renderer numbers every row itself, so an item that arrives already
    numbered prints "1  1. Sarah and Alex are old friends." Stripping it here
    rather than forbidding it in the prompt keeps the fix where it can be tested
    — and the agent will keep writing them, because a numbered list is what a
    numbered list looks like.
    """
    return re.sub(r"^\s*\(?\d{1,2}\s*[.)\]]\s+", "", str(text or ""))


# ------------------------------------------------------------- layouts ----

# How tall each thumbnail may be, by how many are on the slide. Eight pictures
# at the four-picture height made a grid taller than the pane, which overflowed
# upward and printed the first row on top of the instruction line.
_TILE_HEIGHT = ((4, 150), (6, 128), (8, 104))


def _tile_height(count: int) -> int:
    for limit, height in _TILE_HEIGHT:
        if count <= limit:
            return height
    return 96


def picture_set(s: dict) -> str:
    pictures = s.get("pictures") or []
    wide = "pic two" if len(pictures) <= 4 else "pic"
    height = _tile_height(len(pictures))
    cells = []
    for number, picture in enumerate(pictures, 1):
        caption = _unnumbered(str(picture.get("caption", "")).strip())
        # A caption that is only the item's number is not a caption; the
        # renderer already prints the number, and "1  1" is what came out.
        if caption.isdigit():
            caption = ""
        label = rich(caption) if caption else _rule(80)
        cells.append(
            f'<div class="{wide}">{_photo(picture, height)}'
            f'<div class="cap"><span class="n">{number}</span>'
            f'<span class="w">{label}</span></div></div>')
    bank = ""
    if s.get("word_bank"):
        chips = "".join(f'<span class="chip">{esc(w)}</span>'
                        for w in s["word_bank"])
        bank = f'<div class="bank">{chips}</div>'
    return f'<div class="picgrid">{"".join(cells)}</div>{bank}'


def dialogue(s: dict) -> str:
    turns = "".join(
        f'<div class="turn"><span class="who">{esc(t.get("speaker"))}</span>'
        f'<span class="said">{rich(t.get("line"))}</span></div>'
        for t in s.get("turns") or [])
    fills = ""
    if s.get("fill_ins"):
        fills = ('<div class="gaps">'
                 + "".join(f'<div class="gap">{_cell(c)}</div>'
                           for c in s["fill_ins"]) + "</div>")
    scene = _photo(s.get("scene"), 240)
    if scene:
        return (f'<div class="grid"><div class="col"><div class="dialog">{turns}</div>'
                f'</div><div class="col">{scene}</div></div>{fills}')
    return f'<div class="dialog">{turns}</div>{fills}'


def rule_table(s: dict) -> str:
    heads = "".join(f"<th>{esc(h)}</th>" for h in s.get("headers") or [])
    rows = "".join(
        "<tr>" + "".join(f"<td>{_cell(c)}</td>" for c in row) + "</tr>"
        for row in s.get("rows") or [])
    table = f'<table class="rules"><tr>{heads}</tr>{rows}</table>'
    note = f'<div class="note">{rich(s.get("note"))}</div>' if s.get("note") else ""
    art = _photo(s.get("illustration"), 190)
    if art:
        return (f'<div class="grid"><div class="col">{table}{note}</div>'
                f'<div class="col">{art}</div></div>')
    return table + note


def vocab_card(s: dict) -> str:
    lines = [f'<div class="vword">{esc(s.get("word"))}</div>']
    if s.get("part_of_speech"):
        lines.append(f'<div class="vpos">{esc(s["part_of_speech"])}</div>')
    if s.get("plural"):
        lines.append(f'<div class="vpos">{esc(s["plural"])}</div>')
    if s.get("example"):
        lines.append(f'<div class="vex">{rich(s["example"])}</div>')
    card = f'<div class="vcard">{"".join(lines)}</div>'
    note = f'<div class="note">{rich(s.get("note"))}</div>' if s.get("note") else ""
    art = _photo(s.get("picture"), 250)
    if art:
        return (f'<div class="grid"><div class="col">{card}{note}</div>'
                f'<div class="col">{art}</div></div>')
    return card + note


def sorting_grid(s: dict) -> str:
    tiles = "".join(
        f'<div class="tilewrap"><div class="tilenum">{n}</div>'
        f'<div class="tile">{rich(t)}</div></div>'
        for n, t in enumerate(s.get("tiles") or [], 1))
    columns = "".join(f'<div class="cat"><div class="cathead">{esc(c)}</div>'
                      f'<div class="catbox"></div></div>'
                      for c in s.get("categories") or [])
    return (f'<div class="tiles">{tiles}</div>'
            f'<div class="cats">{columns}</div>')


def tile_grid(s: dict) -> str:
    rows = "".join(
        '<div class="trow">'
        + "".join(f'<div class="tile">{rich(w)}</div>' for w in row)
        + "</div>"
        for row in s.get("rows") or [])
    return f'<div class="tilerows">{rows}</div>'


def bubble_exchange(s: dict) -> str:
    bubbles = (f'<div class="bubble l">{rich(s.get("left"))}</div>'
               f'<div class="bubble r">{rich(s.get("right"))}</div>')
    prompt = (f'<div class="prompt">{rich(s.get("prompt"))}</div>'
              if s.get("prompt") else "")
    art = _photo(s.get("picture"), 200)
    if art:
        return (f'<div class="grid"><div class="col">{bubbles}{prompt}</div>'
                f'<div class="col">{art}</div></div>')
    return f'<div class="col" style="margin-top:24px">{bubbles}{prompt}</div>'


def choice_cards(s: dict) -> str:
    question = (f'<div class="prompt">{rich(s.get("question"))}</div>'
                if s.get("question") else "")
    cards = "".join(
        f'<div class="choice"><span class="n">{n}</span>{rich(o.get("text"))}</div>'
        for n, o in enumerate(s.get("options") or [], 1))
    art = _photo(s.get("picture"), 200)
    body = f'{question}<div class="choices">{cards}</div>'
    if art:
        return (f'<div class="grid"><div class="col">{body}</div>'
                f'<div class="col">{art}</div></div>')
    return body


def question_list(s: dict) -> str:
    worked = (f'<div class="worked">{rich(s.get("worked_first"))}</div>'
              if s.get("worked_first") else "")
    items = "".join(
        f'<div class="qrow"><span class="n">{n}</span>'
        f'<span class="q">{rich(_unnumbered(c.get("text")))}</span>{_rule(120)}</div>'
        for n, c in enumerate(s.get("items") or [], 1))
    bank = ""
    if s.get("word_bank"):
        chips = "".join(f'<span class="chip">{esc(w)}</span>' for w in s["word_bank"])
        bank = f'<div class="bank">{chips}</div>'
    return f'{worked}<div class="qlist">{items}</div>{bank}'


def role_play(s: dict) -> str:
    def side(name, task, phrases):
        chips = "".join(f'<li>{esc(p)}</li>' for p in phrases or [])
        return (f'<div class="role"><div class="rolename">{esc(name)}</div>'
                f'<div class="roletask">{rich(task)}</div>'
                f'<ul class="rolephrases">{chips}</ul></div>')
    roles = ('<div class="roles">'
             + side(s.get("role_a"), s.get("role_a_task"), s.get("role_a_phrases"))
             + side(s.get("role_b"), s.get("role_b_task"), s.get("role_b_phrases"))
             + "</div>")
    # The scene the role-play happens in. It was accepted on the component and
    # silently dropped here, so every role-play printed as two grey columns.
    art = _photo(s.get("picture"), 190)
    return f"{roles}{art}" if art else roles


def summary(s: dict) -> str:
    blocks = []
    for group in s.get("groups") or []:
        points = "".join(f"<li>{rich(p)}</li>" for p in group.get("points") or [])
        blocks.append(f'<div class="sgroup"><div class="shead">'
                      f'{esc(group.get("heading"))}</div><ul>{points}</ul></div>')
    return f'<div class="summary">{"".join(blocks)}</div>'


def word_list(s: dict) -> str:
    words = s.get("words") or []
    half = (len(words) + 1) // 2
    def column(items):
        return "<ul>" + "".join(f"<li>{rich(w)}</li>" for w in items) + "</ul>"
    return (f'<div class="wordlist">{column(words[:half])}'
            f'{column(words[half:])}</div>')


RENDERERS = {
    "picture_set": picture_set,
    "dialogue": dialogue,
    "rule_table": rule_table,
    "vocab_card": vocab_card,
    "sorting_grid": sorting_grid,
    "tile_grid": tile_grid,
    "bubble_exchange": bubble_exchange,
    "choice_cards": choice_cards,
    "question_list": question_list,
    "role_play": role_play,
    "summary": summary,
    "word_list": word_list,
}


def render(component: dict) -> str:
    """Draw one component. Unknown kinds render nothing rather than crashing."""
    renderer = RENDERERS.get(str(component.get("kind", "")))
    return renderer(component) if renderer else ""
