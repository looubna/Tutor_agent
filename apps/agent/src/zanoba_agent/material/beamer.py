"""Rendering a STEM lesson as a Beamer deck.

The language decks are HTML: they are photographs, picture grids and speech
bubbles, and CSS draws those well. A maths lesson is the other thing entirely —
it is fractions, integrals, matrices and aligned working, and HTML draws those
badly enough that a student notices. So STEM gets LaTeX.

The preamble is vendored from the Instructional Agents project (MIT, DaRL-GenAI)
rather than written again: it is a considered Beamer setup with blocks, code
listings, tikz and a footer, and rewriting it from scratch would have produced
something worse with the same shape. What is patched is the palette — its five
demo colours are replaced by the app's own tokens, so a maths deck and a German
deck are recognisably the same product.

The one real hazard here is escaping. LaTeX reads `&`, `%`, `$`, `#`, `_`, `{`
and `}` as syntax, and a fraction written `\\frac{1}{2}` must survive untouched
while a percentage sign in prose must not. So maths is carved out first and put
back afterwards, and only the prose between is escaped.
"""

from __future__ import annotations

import re
import shutil
import subprocess
import tempfile
from pathlib import Path
from typing import Any

from .brand import colour, language_name, logo_data_uri  # noqa: F401

_PREAMBLE = Path(__file__).with_name("templates") / "beamer_preamble.tex"
_LOGO = Path(__file__).with_name("brand") / "logo.png"

# The upstream template's demo palette, mapped onto the app's tokens. `myblue`
# carries the structure — frame titles, blocks, headings — so it becomes the
# brand purple, and everything reads as one product.
_PALETTE = {
    "myblue": "primary",
    "mygray": "muted",
    "mygreen": "success",
    "myorange": "accent-ink",
    "mycodebackground": "primary-tint",
}


def _rgb(token: str) -> str:
    """A brand token as the `RGB{r,g,b}` triple LaTeX wants."""
    value = colour(token).lstrip("#")
    if len(value) == 3:
        value = "".join(c * 2 for c in value)
    return f"{int(value[0:2], 16)}, {int(value[2:4], 16)}, {int(value[4:6], 16)}"


# Maths, carved out before escaping and put back after. Display first so that
# `$$...$$` is not mistaken for two inline spans.
_MATH = re.compile(
    r"(\$\$.+?\$\$|\\\[.+?\\\]|\$[^$\n]+?\$|\\\(.+?\\\))", re.S)

_ESCAPES = {
    "\\": r"\textbackslash{}", "&": r"\&", "%": r"\%", "$": r"\$",
    "#": r"\#", "_": r"\_", "{": r"\{", "}": r"\}",
    "~": r"\textasciitilde{}", "^": r"\textasciicircum{}",
}


def escape(text: str) -> str:
    """Escape prose for LaTeX while leaving maths alone.

    `\\frac{a}{b}` inside `$...$` must survive verbatim; a stray `%` in a
    sentence must not, because it silently comments out the rest of the line and
    the slide loses half its content with no error.
    """
    parts = _MATH.split(str(text or ""))
    for index, part in enumerate(parts):
        if index % 2:  # the captured maths
            continue
        parts[index] = "".join(_ESCAPES.get(c, c) for c in part)
    return "".join(parts)


def _inline(text: str) -> str:
    """Escape, then restore the light markdown the material agents use."""
    out = escape(text)
    out = re.sub(r"\*\*(.+?)\*\*", r"\\concept{\1}", out)
    out = re.sub(r"(?<!\*)\*(?!\*)(.+?)(?<!\*)\*(?!\*)", r"\\textit{\1}", out)
    return out


def _body(content: str) -> str:
    """Turn an item's markdown into Beamer body text.

    Deliberately small: headings, bullets, numbered lists and paragraphs. The
    material agents emit little else, and a fuller markdown engine would mostly
    be an opportunity to mangle equations.
    """
    lines, out, bullets = (content or "").splitlines(), [], None

    def close():
        nonlocal bullets
        if bullets:
            out.append(f"\\end{{{bullets}}}")
            bullets = None

    for line in lines:
        stripped = line.strip()
        if not stripped:
            close()
            continue
        heading = re.match(r"^#{1,6}\s*(.+)$", stripped)
        if heading:
            close()
            out.append(f"\\textbf{{{_inline(heading.group(1))}}}\\par\\smallskip")
            continue
        bullet = re.match(r"^[-*+]\s+(.+)$", stripped)
        numbered = re.match(r"^\d+[.)]\s+(.+)$", stripped)
        if bullet or numbered:
            want = "itemize" if bullet else "enumerate"
            if bullets != want:
                close()
                out.append(f"\\begin{{{want}}}")
                bullets = want
            out.append(f"  \\item {_inline((bullet or numbered).group(1))}")
            continue
        close()
        out.append(_inline(stripped) + r"\par")
    close()
    return "\n".join(out)


def _frame(title: str, body: str) -> str:
    return (f"\\begin{{frame}}[fragile]{{{escape(title)}}}\n{body}\n"
            f"\\end{{frame}}\n")


def _item_frame(item: dict[str, Any]) -> str:
    """One material item as one frame — or, for a typed cours, several.

    A *cours* is a numbered argument with its own sections, so it does not fit
    one frame and should not be squeezed into one.
    """
    cours = item.get("cours")
    if cours:
        return render_cours(cours)

    title = item.get("title", "")
    parts: list[str] = []

    instruction = str(item.get("instruction", "")).strip()
    if instruction:
        parts.append(f"\\textit{{{_inline(instruction)}}}\\par\\medskip")

    content = str(item.get("content", "")).strip()
    if content:
        kind = item.get("kind", "")
        if kind in {"worked_example", "explanation"}:
            heading = "Beispiel" if kind == "worked_example" else "Erklärung"
            parts.append(f"\\begin{{block}}{{{escape(item.get('title') or heading)}}}\n"
                         f"{_body(content)}\n\\end{{block}}")
        else:
            parts.append(_body(content))

    exercises = item.get("exercises") or []
    if exercises:
        rows = []
        for exercise in exercises:
            prompt = _inline(exercise.get("prompt", ""))
            expression = str(exercise.get("expression", "")).strip()
            if expression:
                prompt += f"\\quad $\\displaystyle {expression}$"
            rows.append(f"  \\item {prompt}")
        parts.append("\\begin{enumerate}\n" + "\n".join(rows) + "\n\\end{enumerate}")

    note = str(item.get("answer_key", "")).strip()
    if note:
        parts.append(f"\\source{{{escape(note)[:180]}}}")

    return _frame(title, "\n\n".join(parts) or r"\ ")


# ------------------------------------------------- the French cours ----

def _video(video: dict | None) -> str:
    if not video or not video.get("url"):
        return ""
    url = video["url"]
    return (f"\\par\\smallskip{{\\small\\textcolor{{mygray}}{{"
            f"{escape(video.get('label') or 'Vidéo')} }}"
            f"\\url{{{url}}}}}")


def _block(block: dict) -> str:
    """One labelled block — Définition, Propriété, Méthode.

    The label is the interface. A French student reads "Propriété" as something
    to use and "Méthode" as something to follow, so each keeps its own heading
    rather than becoming an unlabelled paragraph.
    """
    from ..schemas.maths import BLOCK_LABELS

    label = BLOCK_LABELS.get(block.get("kind", ""), "")
    heading = label + (f" : {escape(block['title'])}" if block.get("title") else "")
    parts = []
    if block.get("body"):
        parts.append(_body(block["body"]))
    if block.get("steps"):
        steps = "\n".join(f"  \\item {_inline(s)}" for s in block["steps"])
        parts.append("\\begin{enumerate}\n" + steps + "\n\\end{enumerate}")
    parts.append(_video(block.get("video")))
    inner = "\n".join(x for x in parts if x)
    # A Méthode is the one a student comes back to, so it gets the alert style.
    env = "alertblock" if block.get("kind") == "methode" else "block"
    return f"\\begin{{{env}}}{{{heading}}}\n{inner}\n\\end{{{env}}}"


def _subsection(sub: dict) -> str:
    head = (f"\\textbf{{{sub.get('number')}) "
            f"{_inline(sub.get('title'))}}}\\par\\smallskip")
    parts = [head]
    if sub.get("body"):
        parts.append(_body(sub["body"]))
    parts.append(_video(sub.get("video")))
    parts += [_block(b) for b in sub.get("blocks") or []]
    return "\n".join(x for x in parts if x)


def _section_frames(section: dict, chapter: str) -> list[str]:
    """One frame per section. The roman numeral goes in the frame title, which
    is how the class refers to it out loud."""
    title = f"{section.get('numeral')}. {section.get('title')}"
    parts = []
    if section.get("intro"):
        parts.append(_body(section["intro"]))
    parts.append(_video(section.get("video")))
    parts += [_subsection(s) for s in section.get("subsections") or []]
    parts += [_block(b) for b in section.get("blocks") or []]
    return [_frame(title, "\n\n".join(x for x in parts if x) or r"\ ")]


def render_cours(cours: dict) -> str:
    """A maths-et-tiques *cours* as Beamer frames."""
    frames: list[str] = []

    opening = []
    if cours.get("note_historique"):
        opening.append("\\begin{block}{Un peu d'histoire}\n"
                       + _body(cours["note_historique"]) + "\n\\end{block}")
    if cours.get("activite"):
        opening.append("\\begin{block}{Activité de groupe}\n"
                       + _inline(cours["activite"]) + "\n\\end{block}")
    if opening:
        frames.append(_frame(cours.get("chapter", ""), "\n\n".join(opening)))

    for section in cours.get("sections") or []:
        frames += _section_frames(section, cours.get("chapter", ""))

    refs = cours.get("exercices")
    if refs and (refs.get("conseilles") or refs.get("en_devoir")):
        rows = []
        longest = max(len(refs.get("conseilles") or []),
                      len(refs.get("en_devoir") or []))
        for index in range(longest):
            left = (refs.get("conseilles") or [""] * longest)
            right = (refs.get("en_devoir") or [""] * longest)
            a = escape(left[index]) if index < len(left) else ""
            b = escape(right[index]) if index < len(right) else ""
            rows.append(f"{a} & {b} \\\\")
        table = ("\\begin{tabular}{ll}\n\\toprule\n"
                 "\\textbf{Exercices conseillés} & \\textbf{En devoir} \\\\\n"
                 "\\midrule\n" + "\n".join(rows)
                 + "\n\\bottomrule\n\\end{tabular}")
        if refs.get("manuel"):
            table += f"\n\\source{{{escape(refs['manuel'])}}}"
        frames.append(_frame("Exercices", table))

    return "\n".join(frames)


def render(package: dict, plan: dict, objectives: dict) -> str:
    """The whole deck as one LaTeX document."""
    preamble = _PREAMBLE.read_text(encoding="utf-8")
    if "\\usepackage{url}" not in preamble and "hyperref" not in preamble:
        preamble += "\n\\usepackage{url}\n"
    for name, token in _PALETTE.items():
        preamble = re.sub(
            rf"\\definecolor{{{name}}}{{RGB}}{{[^}}]*}}",
            f"\\\\definecolor{{{name}}}{{RGB}}{{{_rgb(token)}}}",
            preamble)

    title = (plan.get("target_item_title") or package.get("target_item_title")
             or package.get("target_item_id", ""))
    subject = (package.get("subject") or "").title()
    logo = ""
    if _LOGO.exists():
        logo = (f"\\titlegraphic{{\\includegraphics[height=1.1cm]"
                f"{{{_LOGO.as_posix()}}}}}\n")

    head = (preamble
            + f"\n\\title{{{escape(title)}}}\n"
            + f"\\subtitle{{{escape(subject)} · {escape(plan.get('level_id',''))}}}\n"
            + "\\author{Zanoba}\n\\date{}\n" + logo
            + "\n\\begin{document}\n\n"
            + "\\begin{frame}[plain]\n  \\titlepage\n\\end{frame}\n\n")

    frames = []
    goals = objectives.get("objectives") or []
    if goals:
        items = "\n".join(f"  \\item {_inline(o.get('statement',''))}" for o in goals)
        frames.append(_frame(
            "Lernziele",
            "\\begin{itemize}\n" + items + "\n\\end{itemize}"))

    for item in package.get("items", []):
        frames.append(_item_frame(item))

    return head + "\n".join(frames) + "\n\\end{document}\n"


def compile_pdf(tex: str, out_path: Path, timeout: int = 240) -> Path:
    """Compile with tectonic, which fetches what it needs and needs no install.

    Raises with the compiler's own message rather than a generic failure: a
    LaTeX error names the line, and hiding that would make a broken equation
    impossible to find.
    """
    engine = shutil.which("tectonic")
    if engine is None:
        raise RuntimeError(
            "No LaTeX engine found. Install tectonic (brew install tectonic) "
            "to build STEM decks; language decks do not need it.")
    out_path = Path(out_path).resolve()
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory() as tmp:
        source = Path(tmp) / "deck.tex"
        source.write_text(tex, encoding="utf-8")
        result = subprocess.run(
            [engine, "-X", "compile", str(source), "--outdir", tmp,
             "--keep-logs", "--print"],
            capture_output=True, text=True, timeout=timeout)
        produced = Path(tmp) / "deck.pdf"
        if not produced.exists():
            message = (result.stderr or result.stdout or "").strip()
            raise RuntimeError(f"LaTeX did not produce a PDF:\n{message[-1500:]}")
        shutil.copyfile(produced, out_path)
    return out_path


def build(package: dict, plan: dict, objectives: dict, out_dir: Path) -> dict:
    """LaTeX and PDF for one STEM lesson."""
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    tex = render(package, plan, objectives)
    (out_dir / "deck.tex").write_text(tex, encoding="utf-8")
    return {"tex": tex, "pdf": compile_pdf(tex, out_dir / "deck.pdf")}
