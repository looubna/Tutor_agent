"""Reading the curriculum off disk.

Deterministic infrastructure, deliberately not an agent. Looking up "which
lesson follows this one" is an index lookup with one right answer, and asking a
model to do it would buy nothing but a chance to be wrong.

The two domains are stored in different shapes — see `schemas.curriculum` — so
this module also does the one job that shape difference creates: presenting
both as a flat ordered list of teachable items, which is all the agents above
actually need.
"""

from __future__ import annotations

import json
import os
from functools import lru_cache
from pathlib import Path
from typing import Literal

from pydantic import BaseModel, Field

from ..schemas.curriculum import (
    LanguageCurriculum,
    LanguageFocus,
    StemCurriculum,
)

Domain = Literal["language", "stem"]

# Repo layout and container layout happen to agree — `src/zanoba_agent/curriculum`
# under a root that also holds `data/`. The override exists so that agreement is
# a convenience rather than a thing deployment depends on.
DATA_DIR = Path(
    os.environ.get(
        "ZANOBA_DATA_DIR",
        Path(__file__).resolve().parents[3] / "data" / "curriculum",
    )
)


class CurriculumNotFound(LookupError):
    """No curriculum file for that subject."""


class TeachableItem(BaseModel):
    """One bookable hour, normalised across both domains.

    For a language this is a lesson. For STEM it is currently a unit, because
    no lessons have been authored beneath the units yet — when they are, this
    starts resolving to them and nothing above has to change. `granularity`
    says which you are looking at, so a caller is never silently misled about
    how big the thing is.
    """

    id: str
    title: str
    order: int
    granularity: Literal["lesson", "unit"]
    parent_id: str = Field(default="", description="Chapter id, or unit id.")
    parent_title: str = ""
    focus: LanguageFocus | None = None
    objectives: list[str] = Field(default_factory=list)
    prerequisites: list[str] = Field(default_factory=list)


def _subject_file(subject: str) -> Path:
    path = DATA_DIR / f"{subject}.json"
    if not path.exists():
        raise CurriculumNotFound(
            f"No curriculum for {subject!r}. Available: {', '.join(available_subjects())}"
        )
    return path


def available_subjects() -> list[str]:
    """Every subject with a curriculum file, sorted."""
    return sorted(p.stem for p in DATA_DIR.glob("*.json"))


@lru_cache(maxsize=None)
def domain_of(subject: str) -> Domain:
    """Which shape this subject's curriculum is in.

    Read from the file rather than kept in a hardcoded list, so adding physics
    is a new file and nothing else.
    """
    raw = json.loads(_subject_file(subject).read_text())
    return "language" if "levels" in raw else "stem"


@lru_cache(maxsize=None)
def load(subject: str) -> LanguageCurriculum | StemCurriculum:
    """The whole curriculum for one subject, validated and cached."""
    text = _subject_file(subject).read_text()
    if domain_of(subject) == "language":
        return LanguageCurriculum.model_validate_json(text)
    return StemCurriculum.model_validate_json(text)


def level_ids(subject: str) -> list[str]:
    """Every level or program id, in teaching order."""
    curriculum = load(subject)
    if isinstance(curriculum, LanguageCurriculum):
        return [level.id for level in sorted(curriculum.levels, key=lambda x: x.order)]
    return [p.id for p in sorted(curriculum.programs, key=lambda x: x.order)]


def items_in_order(subject: str, level_id: str) -> list[TeachableItem]:
    """Everything teachable at one level, in the order it should be taught."""
    curriculum = load(subject)
    items: list[TeachableItem] = []

    if isinstance(curriculum, LanguageCurriculum):
        level = next((x for x in curriculum.levels if x.id == level_id), None)
        if level is None:
            return []
        position = 0
        for chapter in sorted(level.chapters, key=lambda c: c.order):
            for lesson in sorted(chapter.lessons, key=lambda x: x.order):
                position += 1
                items.append(
                    TeachableItem(
                        id=lesson.id,
                        title=lesson.title,
                        order=position,
                        granularity="lesson",
                        parent_id=chapter.id,
                        parent_title=chapter.title,
                        focus=lesson.focus,
                        objectives=lesson.objectives,
                        prerequisites=lesson.prerequisites,
                    )
                )
        return items

    program = next((p for p in curriculum.programs if p.id == level_id), None)
    if program is None:
        return []
    position = 0
    for unit in sorted(program.units, key=lambda u: u.order):
        if unit.lessons:
            for lesson in sorted(unit.lessons, key=lambda x: x.order):
                position += 1
                items.append(
                    TeachableItem(
                        id=lesson.id,
                        title=lesson.title,
                        order=position,
                        granularity="lesson",
                        parent_id=unit.id,
                        parent_title=unit.title,
                        objectives=lesson.learning_outcomes,
                        prerequisites=lesson.prerequisites,
                    )
                )
        else:
            # No lessons authored under this unit yet. The unit is the most
            # specific thing that exists, so it stands in — flagged as a unit
            # rather than quietly passed off as a lesson.
            position += 1
            items.append(
                TeachableItem(
                    id=unit.id,
                    title=unit.title,
                    order=position,
                    granularity="unit",
                    parent_id=program.id,
                    parent_title=program.label,
                )
            )
    return items


def find_item(subject: str, item_id: str) -> TeachableItem | None:
    """One teachable item by id, searching every level."""
    for level in level_ids(subject):
        for item in items_in_order(subject, level):
            if item.id == item_id:
                return item
    return None


def band_of(subject: str, level_id: str) -> str:
    """The CEFR band a level sits in, e.g. "A1" for "a1-1".

    Empty for a STEM subject, which has no band and does not need one: the
    prepared-lesson cache keys on it, and an empty band is a consistent key
    rather than a missing one.
    """
    curriculum = load(subject)
    for level in getattr(curriculum, "levels", []) or []:
        if level.id == level_id:
            return getattr(level, "band", "") or ""
    return ""


def level_of(subject: str, item_id: str) -> str | None:
    """Which level an item belongs to."""
    for level in level_ids(subject):
        if any(item.id == item_id for item in items_in_order(subject, level)):
            return level
    return None


def prerequisites_of(subject: str, item_id: str) -> list[str]:
    """Declared prerequisites, plus everything ordered before it in its level.

    A syllabus encodes order as well as explicit dependencies, and the order is
    the stronger signal: lesson 7 assumes lessons 1-6 whether or not anyone
    wrote that down. Explicit `prerequisites` come first because they are the
    deliberate ones, and they can point outside the level.
    """
    item = find_item(subject, item_id)
    if item is None:
        return []
    level = level_of(subject, item_id)
    earlier = [
        other.id
        for other in items_in_order(subject, level or "")
        if other.order < item.order
    ]
    ordered = list(item.prerequisites)
    ordered += [x for x in earlier if x not in ordered]
    return ordered
