"""Turning a material package into a worksheet the student can hold.

Two documents come out of one package, and the difference between them is the
point: the **student** copy carries the exercises with blanks, and the **tutor**
copy carries the same thing plus the answer key. Answers are never in the
student's file at all — not hidden by styling, not in a comment, not off the
bottom of the page. A worksheet with the answers on it is not a worksheet, and
CSS is not a security boundary.

Rendered as HTML and printed by headless Chrome. That keeps the typography
decent without a LaTeX toolchain, and the HTML is worth having on its own — it
is what a web view of the lesson would show.
"""

from __future__ import annotations

import shutil
import subprocess
import tempfile
from datetime import datetime, timezone
from pathlib import Path

import markdown as _markdown

_CHROME_CANDIDATES = [
    "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
    "/Applications/Chromium.app/Contents/MacOS/Chromium",
    "google-chrome",
    "chromium",
]

_CSS = """
@page { size: A4; margin: 16mm 15mm 18mm; }
* { box-sizing: border-box; }
body { font: 11pt/1.55 "Iowan Old Style", Georgia, serif; color: #17181c; margin: 0; }
h1 { font: 700 21pt/1.2 "Helvetica Neue", Arial, sans-serif; margin: 0 0 2mm; letter-spacing: -.3px; }
.sub { font: 10pt/1.4 "Helvetica Neue", Arial, sans-serif; color: #6b6f76; margin: 0 0 6mm; }
.meta { font: 9pt/1.5 "Helvetica Neue", Arial, sans-serif; color: #6b6f76;
        border-top: 1.5px solid #17181c; border-bottom: .5px solid #d5d7dc;
        padding: 2.5mm 0; margin-bottom: 7mm; display: flex; gap: 7mm; flex-wrap: wrap; }
.meta b { color: #17181c; font-weight: 600; }
.objectives { background: #f6f7f9; border-left: 3px solid #5b5bd6; padding: 4mm 5mm; margin: 0 0 7mm; }
.objectives h2 { font: 600 10pt "Helvetica Neue", Arial, sans-serif; text-transform: uppercase;
                 letter-spacing: .8px; color: #5b5bd6; margin: 0 0 2mm; }
.objectives ol { margin: 0; padding-left: 5mm; }
.objectives li { margin: 1mm 0; }
section { page-break-inside: avoid; margin: 0 0 7mm; }
section > h2 { font: 600 13pt "Helvetica Neue", Arial, sans-serif; margin: 0 0 1mm;
               padding-bottom: 1.5mm; border-bottom: .5px solid #d5d7dc; }
.tag { font: 600 8pt "Helvetica Neue", Arial, sans-serif; text-transform: uppercase;
       letter-spacing: .7px; color: #6b6f76; }
.body h3, .body h4 { font: 600 11pt "Helvetica Neue", Arial, sans-serif; margin: 3mm 0 1mm; }
.body table { border-collapse: collapse; width: 100%; margin: 2mm 0; font-size: 10pt; }
.body th, .body td { border: .5px solid #d5d7dc; padding: 1.5mm 2mm; text-align: left; }
.body th { background: #f6f7f9; font: 600 9.5pt "Helvetica Neue", Arial, sans-serif; }
.body ul, .body ol { padding-left: 5mm; margin: 2mm 0; }
.body code { background: #f0f1f4; padding: .3mm 1mm; border-radius: 2px; font-size: 9.5pt; }
.ex { margin: 2mm 0 0; padding: 0; list-style: none; counter-reset: q; }
.ex li { counter-increment: q; margin: 0 0 3mm; padding-left: 8mm; position: relative; }
.ex li::before { content: counter(q) "."; position: absolute; left: 0; font-weight: 600; color: #6b6f76; }
.rule { display: inline-block; min-width: 34mm; border-bottom: .6px solid #9aa0a6;
        margin-left: 2mm; height: 4.4mm; vertical-align: bottom; }
.answer { color: #0a7d3f; font-weight: 600; }
.imgspec { border: .5px dashed #9aa0a6; border-radius: 3px; padding: 3mm 4mm; margin: 2.5mm 0;
           background: #fbfbfc; font: 9.5pt/1.45 "Helvetica Neue", Arial, sans-serif; color: #4a4e55; }
.imgspec b { color: #17181c; }
.key { background: #f0f8f3; border-left: 3px solid #0a7d3f; padding: 3mm 4mm; margin: 3mm 0 0;
       font: 10pt/1.5 "Helvetica Neue", Arial, sans-serif; white-space: pre-wrap; }
.key b { color: #0a7d3f; text-transform: uppercase; font-size: 8.5pt; letter-spacing: .7px; }
footer { position: fixed; bottom: 6mm; left: 0; right: 0; font: 8pt "Helvetica Neue", Arial, sans-serif;
         color: #9aa0a6; display: flex; justify-content: space-between; }
"""


def _md(text: str) -> str:
    return _markdown.markdown(text or "", extensions=["tables", "fenced_code", "sane_lists"])


def _find_chrome() -> str | None:
    for candidate in _CHROME_CANDIDATES:
        if Path(candidate).exists():
            return candidate
        found = shutil.which(candidate)
        if found:
            return found
    return None


def render_html(package: dict, plan: dict, objectives: dict, *, for_tutor: bool) -> str:
    """Build the worksheet HTML.

    `for_tutor` is the only switch. When it is False no answer ever reaches the
    document — the exercises render as blanks and the answer key is not emitted.
    """
    subject = (package.get("subject") or "").title()
    target = package.get("target_item_id", "")
    title = plan.get("target_item_title") or target
    audience = "Tutor copy" if for_tutor else "Student worksheet"
    minutes = sum(a.get("minutes", 0) for a in plan.get("activities", []))
    activity_titles = {a.get("id"): a for a in plan.get("activities", [])}

    parts: list[str] = [
        "<!doctype html><meta charset='utf-8'>",
        f"<style>{_CSS}</style>",
        f"<h1>{subject} — {title}</h1>",
        f"<p class='sub'>{audience}</p>",
        "<div class='meta'>",
        f"<span><b>Lesson</b> {target}</span>",
        f"<span><b>Duration</b> {minutes} min</span>",
        f"<span><b>Level</b> {plan.get('level_id','')}</span>",
    ]
    if plan.get("focus"):
        parts.append(f"<span><b>Focus</b> {plan['focus']}</span>")
    parts.append(f"<span><b>Date</b> {datetime.now(timezone.utc):%d %b %Y}</span></div>")

    objective_list = objectives.get("objectives", [])
    if objective_list:
        parts.append("<div class='objectives'><h2>By the end of this lesson</h2><ol>")
        for objective in objective_list:
            parts.append(f"<li>{objective.get('statement','')}</li>")
        parts.append("</ol></div>")

    for item in package.get("items", []):
        activity = activity_titles.get(item.get("activity_id"), {})
        phase = activity.get("phase", item.get("kind", ""))
        mins = activity.get("minutes")
        tag = f"{phase}{f' · {mins} min' if mins else ''}"
        parts.append("<section>")
        parts.append(f"<div class='tag'>{tag}</div>")
        parts.append(f"<h2>{item.get('title','')}</h2>")
        parts.append(f"<div class='body'>{_md(item.get('content',''))}</div>")

        for image in item.get("images") or []:
            parts.append(
                "<div class='imgspec'><b>Illustration to be added.</b> "
                f"{image.get('purpose','')}<br><i>{image.get('alt_text','')}</i></div>"
            )

        exercises = item.get("exercises") or []
        if exercises:
            parts.append("<ol class='ex'>")
            for exercise in exercises:
                answer = (
                    f"<span class='answer'>{exercise.get('answer','')}</span>"
                    if for_tutor
                    else "<span class='rule'></span>"
                )
                parts.append(f"<li>{exercise.get('prompt','')} {answer}</li>")
            parts.append("</ol>")

        if for_tutor and item.get("answer_key"):
            parts.append(f"<div class='key'><b>Answer key</b><br>{item['answer_key']}</div>")
        parts.append("</section>")

    parts.append(
        "<footer><span>Zanoba</span>"
        f"<span>{'Not for the student' if for_tutor else 'Your copy'}</span></footer>"
    )
    return "\n".join(parts)


def render_pdf(html: str, out_path: Path, timeout: int = 45) -> Path:
    """Print HTML to PDF with headless Chrome.

    Chrome writes the PDF and then, on some macOS builds, does not exit. So the
    process is given a bounded window and the *file* is the success condition,
    not the exit code — waiting on a process that has already done its job is
    how this hangs for two minutes and then reports failure over a finished PDF.
    """
    chrome = _find_chrome()
    if chrome is None:
        raise RuntimeError("No Chrome or Chromium found to print the PDF.")
    out_path = Path(out_path).resolve()
    out_path.parent.mkdir(parents=True, exist_ok=True)
    if out_path.exists():
        out_path.unlink()

    with tempfile.TemporaryDirectory() as tmp:
        source = Path(tmp) / "worksheet.html"
        source.write_text(html, encoding="utf-8")
        process = subprocess.Popen(
            [chrome, "--headless=new", "--disable-gpu", "--no-sandbox",
             "--no-first-run", "--disable-extensions", "--disable-dev-shm-usage",
             f"--user-data-dir={tmp}/profile", "--no-pdf-header-footer",
             "--virtual-time-budget=4000",
             f"--print-to-pdf={out_path}", source.as_uri()],
            stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
        )
        try:
            process.wait(timeout=timeout)
        except subprocess.TimeoutExpired:
            process.kill()
            process.wait(timeout=10)

    if not out_path.exists() or out_path.stat().st_size == 0:
        raise RuntimeError(f"Chrome produced no PDF at {out_path}")
    return out_path


def build(package: dict, plan: dict, objectives: dict, out_dir: Path) -> dict[str, Path]:
    """Write both copies. Returns the paths written."""
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    written: dict[str, Path] = {}
    for audience, for_tutor in (("student", False), ("tutor", True)):
        html = render_html(package, plan, objectives, for_tutor=for_tutor)
        (out_dir / f"worksheet-{audience}.html").write_text(html, encoding="utf-8")
        written[audience] = render_pdf(html, out_dir / f"worksheet-{audience}.pdf")
    return written
