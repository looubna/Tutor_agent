# -*- coding: utf-8 -*-
"""Write the authored French maths lessons into mathematics.json.

Idempotent: run it again after editing a lesson list and the file is rebuilt
from the source rather than appended to. The lesson ids are derived from the
unit id and the lesson's position, so re-running does not renumber anything a
student's mastery record points at.

Prerequisites are chained inside a unit — lesson 2 needs lesson 1 — because that
is true and because the Diagnostic agent uses prerequisites to decide what to
review. Across units they are left empty: the ordering of chapters is a teacher's
choice, and asserting a dependency that the programme does not require would
make the planner insist on review nobody asked for.
"""
from __future__ import annotations

import json
import re
import sys
import unicodedata
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from fr_maths_lessons_college import COLLEGE          # noqa: E402
from fr_maths_lessons_lycee import LYCEE              # noqa: E402

LESSONS = {**COLLEGE, **LYCEE}
TARGET = Path(__file__).resolve().parents[1] / "mathematics.json"


def slug(title: str) -> str:
    """A stable, ascii id fragment from a French title."""
    folded = unicodedata.normalize("NFKD", title.lower())
    folded = "".join(c for c in folded if not unicodedata.combining(c))
    folded = folded.replace("'", " ").replace("’", " ")
    return re.sub(r"[^a-z0-9]+", "-", folded).strip("-")[:44]


def main() -> int:
    data = json.loads(TARGET.read_text(encoding="utf-8"))
    written = units_touched = 0
    missing: list[str] = []

    for program in data["programs"]:
        if not program["id"].startswith("fr."):
            continue
        for unit in program.get("units", []):
            authored = LESSONS.get(unit["id"])
            if not authored:
                missing.append(unit["id"])
                continue
            lessons = []
            for order, (title, outcomes) in enumerate(authored, 1):
                lesson_id = f"{unit['id']}.l{order}"
                lessons.append({
                    "id": lesson_id,
                    "title": title,
                    "order": order,
                    "prerequisites": ([f"{unit['id']}.l{order - 1}"]
                                      if order > 1 else []),
                    "concepts": [{"id": f"{lesson_id}.c{n}", "title": outcome}
                                 for n, outcome in enumerate(outcomes, 1)],
                    "learning_outcomes": list(outcomes),
                })
            unit["lessons"] = lessons
            units_touched += 1
            written += len(lessons)

    TARGET.write_text(
        json.dumps(data, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    print(f"wrote {written} lessons across {units_touched} units")
    if missing:
        print(f"NO LESSONS AUTHORED for {len(missing)} units: {missing}")
    return 1 if missing else 0


if __name__ == "__main__":
    raise SystemExit(main())
