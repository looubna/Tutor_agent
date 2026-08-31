"""
Pull the noun facts out of the free Goethe-Institut A1 word list.

    python3 scripts/extract_wortliste.py A1_SD1_Wortliste_02.pdf

Writes `data/words.de.json`: for every noun, its article, its plural and the
line of the source it came from. Deterministic and re-runnable, so a reviewer
can always check an entry against the page it was read from.

What it deliberately does NOT take: the example sentences. Those are written by
the Goethe-Institut and belong to them. The article and the plural of a German
noun are facts about the language and belong to nobody.

Translations are not in the source at all. The script leaves `en` empty on a new
word and never overwrites one that is already filled in — see `merge()`.
"""

from __future__ import annotations

import json
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "data" / "words.de.json"

# The alphabetical list starts on page 9, under a heading that pdftotext renders
# as "Alphabetische   A". Everything before it is the themed word-group pages.
ALPHA_HEADING = re.compile(r"^\s+Alphabetische\s+A\s*$")
GROUPS_START = re.compile(r"^\s+Wortgruppenliste\s*$")

ARTICLES = ("der", "die", "das")

# A plural is written as an ending to bolt on, sometimes with the umlauted vowel
# in front of it, and the source is not consistent about the dashes.
ENDINGS = r"(?:nen|en|er|se|e|n|s)"
PLURAL = (
    rf"(?:\(pl\.\)"                              # die Eltern (pl.)
    rf"|¨?[-–]\s*[äöüÄÖÜ]?\s*,?\s*{ENDINGS}?"   # der Baum, -ä, e   das Auto, -s   der Koffer, –
    rf"|[äöüÄÖÜ]\s*,\s*{ENDINGS})"               # der Ehemann, ä, er  (dash missing in the source)
)
ENTRY = re.compile(
    rf"^(\s*)(?P<art>der|die|das)\s+(?P<noun>[A-ZÄÖÜ][A-Za-zäöüßÄÖÜ]+)"
    rf"\s*(?:,?\s*(?P<pl>{PLURAL}))?(?=\s|$)"
)

UMLAUT = {"ä": "a", "ö": "o", "ü": "u", "Ä": "A", "Ö": "O", "Ü": "U"}


def pdf_lines(pdf: Path) -> list[str]:
    txt = subprocess.run(
        ["pdftotext", "-layout", str(pdf), "-"],
        capture_output=True, text=True, check=True,
    ).stdout
    return txt.split("\n")


def split_columns(line: str) -> list[str]:
    """The word-group pages run two columns; three or more spaces divide them."""
    return [p for p in re.split(r"\s{3,}", line.strip()) if p]


def apply_umlaut(noun: str, vowel: str) -> str:
    """`der Baum, -ä, e` means umlaut the last a, then add e: Bäume."""
    base = UMLAUT[vowel]
    i = noun.rfind(base)
    if i == -1:
        return noun
    return noun[:i] + vowel + noun[i + 1:]


def build_plural(noun: str, raw: str | None) -> tuple[str | None, str]:
    """Return (plural, how) — `how` records what the source actually printed."""
    if raw is None:
        return None, "not given"
    raw = raw.strip()
    if raw == "(pl.)":
        return noun, "plural only"
    core = raw.lstrip("¨–- ").strip()
    stem, umlauted = noun, False
    if core and core[0] in UMLAUT:
        umlauted = True
        stem = apply_umlaut(noun, core[0])
        core = core[1:].lstrip(", ").strip()
    elif raw.startswith("¨"):
        umlauted = True
        # `die Nacht,¨-e` — umlaut marked on its own, vowel not spelled out
        for v in "aou":
            if v in noun:
                stem = apply_umlaut(noun, {"a": "ä", "o": "ö", "u": "ü"}[v])
                break
    if not core:
        return stem, "umlaut, no ending" if umlauted else "no change"
    if stem.endswith("e") and core.startswith("e"):
        stem = stem[:-1]          # die Adresse, -en → Adressen
    return stem + core, f"umlaut +{core}" if umlauted else f"+{core}"


def looks_wrong(noun: str, plural: str | None, printed: str) -> str | None:
    """The source is not error-free. `die Woche, -e` expands to *Wochee*, and a
    reviewer should see that before a student does."""
    if plural is None:
        return None
    if plural == noun and printed.startswith("+"):
        return "the source printed an ending but it changes nothing; likely a typo for -n"
    if re.search(r"([aeiouäöü])\1", plural) and not re.search(r"([aeiouäöü])\1", noun):
        return "the ending doubles a vowel"
    return None


def join_hyphens(lines: list[str]) -> list[str]:
    """`der Anruf-` / `beantworter` is one word broken over two lines."""
    out: list[str] = []
    for line in lines:
        if out and re.search(r"[A-Za-zäöüß]-\s*$", out[-1]):
            head = re.sub(r"-\s*$", "", out[-1])
            out[-1] = head + line.strip()
        else:
            out.append(line)
    return out


def harvest(lines: list[str]) -> dict[str, dict]:
    start_groups = next(i for i, l in enumerate(lines) if GROUPS_START.match(l))
    start_alpha = next(i for i, l in enumerate(lines) if ALPHA_HEADING.match(l))

    found: dict[str, dict] = {}

    def take(text: str, lineno: int, section: str) -> None:
        m = ENTRY.match(text)
        if not m:
            return
        noun = m.group("noun")
        if noun in found:          # first sighting wins; the list is alphabetical
            return
        plural, how = build_plural(noun, m.group("pl"))
        suspect = looks_wrong(noun, plural, how)
        found[noun] = {
            "article": m.group("art"),
            "plural": plural,
            "en": "",
            "checked": False,
            "src": {"list": section, "line": lineno, "printed": how},
        }
        if suspect:
            found[noun]["suspect"] = suspect

    # themed pages: two columns, so split before matching
    for i, line in enumerate(lines[start_groups:start_alpha], start=start_groups + 1):
        for part in split_columns(line):
            take(" " + part, i, "word groups")

    # alphabetical pages: one column, entry then example sentence
    for i, line in enumerate(join_hyphens(lines[start_alpha:]), start=start_alpha + 1):
        take(line, i, "alphabetical")

    return dict(sorted(found.items()))


def merge(fresh: dict[str, dict]) -> dict[str, dict]:
    """Never clobber a translation or a tick a human already put in the file."""
    if not OUT.exists():
        return fresh
    old = json.loads(OUT.read_text())["words"]
    for noun, entry in fresh.items():
        if noun in old:
            entry["en"] = old[noun].get("en", "")
            entry["checked"] = old[noun].get("checked", False)
    return fresh


def main() -> None:
    if len(sys.argv) != 2:
        sys.exit("usage: extract_wortliste.py <A1_SD1_Wortliste.pdf>")
    words = merge(harvest(pdf_lines(Path(sys.argv[1]))))
    OUT.parent.mkdir(exist_ok=True)
    OUT.write_text(json.dumps({
        "source": {
            "list": "Goethe-Institut · Goethe-Zertifikat A1 · Start Deutsch 1 · Wortliste",
            "edition": "VS_02_280312",
            "url": "https://www.goethe.de/pro/relaunch/prf/de/A1_SD1_Wortliste_02.pdf",
            "taken": "articles and plurals only — no example sentences",
        },
        "words": words,
    }, ensure_ascii=False, indent=2) + "\n")
    todo = sum(1 for w in words.values() if not w["en"])
    print(f"{len(words)} nouns → {OUT.relative_to(ROOT)}")
    suspect = {n: w["suspect"] for n, w in words.items() if "suspect" in w}
    print(f"{sum(1 for w in words.values() if w['plural'])} have a plural, "
          f"{todo} still need an English translation")
    if suspect:
        print(f"\n{len(suspect)} need a human eye before use:")
        for noun, why in suspect.items():
            print(f"  {words[noun]['article']} {noun} → {words[noun]['plural']}  ({why})")


if __name__ == "__main__":
    main()
