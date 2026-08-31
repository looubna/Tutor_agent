"""Prepared lessons, cached — so "Start now" starts now.

Building a lesson from scratch takes eight and a half minutes: a lesson plan, a
material blueprint, the material written against it, and a dozen images. That is
fine to pay once and impossible to make a student watch.

The fix is not a faster pipeline, it is noticing that most of that work is not
about the student at all. "der, die, das" at A1 is the same grammar point, the
same three genders, the same rule table and the same photograph of a garden for
every learner who reaches it. What differs is which practice they need, how much
review, how hard to pitch it and which of their weaknesses to aim at.

So the work splits in two:

  BASELINE       keyed by (subject, item_id, band). Student-independent. Built
                 once, ahead of time, and served instantly to anyone.
  PERSONALISATION keyed additionally by the student. Regenerates only the slots
                 the diagnosis actually changes, and reuses everything else —
                 crucially including every image, which is where the minutes and
                 most of the money go.

The blueprint is what makes the second half possible. Because every item names
the slot it was written against, "this learner needs more controlled practice
and no context dialogue" is a statement about two slot ids, not a reason to
re-improvise a lesson. That is the same targeted-regeneration machinery the
quality loop uses, pointed at a different question.

Images are content-addressed by prompt in `material.images`, so a picture whose
brief did not change is not merely reused across students — it is never
regenerated at all, for anyone, ever again.
"""

from __future__ import annotations

import hashlib
import json
import os
import time
from pathlib import Path
from typing import Any, Protocol

# Bumped when a change to the rubric, the schemas or the generators would make
# previously cached material wrong rather than merely older. Baselines built
# under an earlier version are ignored rather than served.
CACHE_VERSION = "3"


def baseline_key(subject: str, item_id: str, band: str) -> str:
    """The identity of a student-independent prepared lesson."""
    return f"v{CACHE_VERSION}:{subject}:{item_id}:{(band or '').upper()}"


def personalised_key(subject: str, item_id: str, band: str, student_id: str,
                     fingerprint: str) -> str:
    """The identity of one student's version of a lesson.

    The fingerprint is what the personalisation was computed FROM. When a
    student's mastery moves, the fingerprint changes and the old version is
    superseded — rather than being served stale to someone who has since learnt
    the thing it was compensating for.
    """
    return f"{baseline_key(subject, item_id, band)}:{student_id}:{fingerprint}"


def fingerprint(diagnosis: dict | None, profile: dict | None = None) -> str:
    """A short stable hash of everything personalisation depends on.

    Deliberately narrow. It covers what actually changes the material — how
    ready the learner is, what to review, how to pitch it, what they get wrong,
    and the preferences the planner is told to follow — and nothing else. A
    fingerprint that moved every time any field on the profile was touched would
    invalidate the cache constantly and buy nothing.
    """
    diagnosis = diagnosis or {}
    profile = profile or {}
    preferences = profile.get("preferences", {}) or {}
    relevant = {
        "readiness": diagnosis.get("readiness", ""),
        "difficulty": diagnosis.get("recommended_difficulty", ""),
        "review_first": sorted(diagnosis.get("review_first", []) or []),
        "misconceptions": sorted(
            m.get("concept", "") for m in diagnosis.get("misconceptions", []) or []),
        "recurring_errors": sorted(
            e.get("tag", "") for e in diagnosis.get("recurring_errors", []) or []),
        "weak": sorted(
            i.get("item_id", "")
            for i in diagnosis.get("partially_mastered", []) or []),
        "visual": preferences.get("likes_visual_material"),
        "conversation": preferences.get("likes_conversation"),
        "correction": preferences.get("correction_style", ""),
        "topics": sorted(preferences.get("preferred_topics", []) or []),
    }
    blob = json.dumps(relevant, sort_keys=True, ensure_ascii=False)
    return hashlib.sha256(blob.encode()).hexdigest()[:16]


# --------------------------------------------------------------- the store ----

class LessonCache(Protocol):
    """Where prepared lessons live between the build and the lesson."""

    def get(self, key: str) -> dict | None: ...

    def put(self, key: str, entry: dict) -> None: ...

    def keys(self, prefix: str = "") -> list[str]: ...


class FileLessonCache:
    """A directory of JSON files. What development and the demo run on."""

    def __init__(self, root: str | Path = "out/cache") -> None:
        self._root = Path(root)
        self._root.mkdir(parents=True, exist_ok=True)

    def _path(self, key: str) -> Path:
        safe = "".join(c if c.isalnum() or c in "-_." else "-" for c in key)
        return self._root / f"{safe}.json"

    def get(self, key: str) -> dict | None:
        path = self._path(key)
        if not path.exists():
            return None
        try:
            return json.loads(path.read_text(encoding="utf-8"))
        except ValueError:
            # A half-written file is not worth crashing a lesson over; treat it
            # as a miss and let the caller rebuild.
            return None

    def put(self, key: str, entry: dict) -> None:
        # Written to a temporary name and moved, so a reader never sees a
        # partial file — a student opening a lesson mid-write would otherwise
        # get a parse error instead of a lesson.
        path = self._path(key)
        temporary = path.with_suffix(".tmp")
        temporary.write_text(json.dumps(entry, ensure_ascii=False, indent=1),
                             encoding="utf-8")
        temporary.replace(path)

    def keys(self, prefix: str = "") -> list[str]:
        return sorted(p.stem for p in self._root.glob("*.json")
                      if p.stem.startswith(prefix.replace(":", "-")))


class FirestoreLessonCache:
    """The production store. One document per prepared lesson."""

    def __init__(self, project: str | None = None,
                 collection: str = "prepared_lessons") -> None:
        self._project = project or os.environ.get("GOOGLE_CLOUD_PROJECT")
        self._collection = collection
        self._client = None

    @property
    def client(self):
        if self._client is None:
            from google.cloud import firestore

            self._client = firestore.Client(project=self._project)
        return self._client

    def _doc(self, key: str):
        return self.client.collection(self._collection).document(
            key.replace("/", "_"))

    def get(self, key: str) -> dict | None:
        snapshot = self._doc(key).get()
        return snapshot.to_dict() if snapshot.exists else None

    def put(self, key: str, entry: dict) -> None:
        self._doc(key).set(entry)

    def keys(self, prefix: str = "") -> list[str]:
        return [d.id for d in self.client.collection(self._collection)
                .stream() if d.id.startswith(prefix.replace("/", "_"))]


_cache: LessonCache = FileLessonCache()


def set_cache(cache: LessonCache) -> None:
    """Swap the backend. Firestore in production, files in development."""
    global _cache
    _cache = cache


def store(key: str, blueprint: dict, package: dict, plan: dict,
          objectives: dict, quality: dict | None = None, **extra) -> dict:
    """Save one prepared lesson."""
    entry = {
        "key": key, "version": CACHE_VERSION, "built_at": time.time(),
        "blueprint": blueprint, "material": package, "plan": plan,
        "objectives": objectives, "quality": quality or {}, **extra,
    }
    _cache.put(key, entry)
    return entry


def load(key: str) -> dict | None:
    """Load a prepared lesson, or None. Wrong-version entries are a miss."""
    entry = _cache.get(key)
    if entry is None:
        return None
    if str(entry.get("version")) != CACHE_VERSION:
        return None
    return entry


def load_baseline(subject: str, item_id: str, band: str) -> dict | None:
    return load(baseline_key(subject, item_id, band))


# ------------------------------------------------------- what to redo -------

# Which stages a given kind of diagnostic finding actually touches. This table
# is the whole saving: it is what turns "personalise this lesson" from a rebuild
# into two or three slots.
#
# The reasoning behind each row is the same — what would a tutor actually change
# for this learner? A learner who needs review needs more practice, not a
# different rule table. A learner pitched below level needs gentler production,
# not a different context dialogue.
_STAGES_FOR = {
    "needs_review": {"warm-up", "controlled-practice", "recognition",
                     "vocabulary-preparation", "encounter"},
    "below": {"controlled-practice", "guided-practice", "guided-interaction",
              "contextual-use", "detail"},
    "above": {"communicative-practice", "communicative-task", "communicative-use",
              "independent-communication", "post-reading", "inference"},
    "misconception": {"noticing", "explanation", "controlled-practice", "meaning"},
    "topics": {"context", "situation", "encounter", "communicative-practice",
               "communicative-task", "communicative-use", "post-reading"},
}


def personalisation_plan(blueprint: dict, diagnosis: dict | None,
                         profile: dict | None = None) -> dict[str, Any]:
    """Decide which slots this student's diagnosis actually changes.

    Returns the slot ids to regenerate, the ones to carry through untouched, and
    why — plus whether any image needs remaking, which is the expensive question.

    The default answer is "almost nothing". A learner with no diagnosed
    weaknesses, at level, gets the baseline unchanged and their lesson opens
    instantly. That is the common case and it should cost nothing.
    """
    diagnosis = diagnosis or {}
    profile = profile or {}
    preferences = profile.get("preferences", {}) or {}
    slots = blueprint.get("slots", []) or []

    targeted: dict[str, list[str]] = {}

    def mark(stages: set[str], reason: str) -> None:
        for slot in slots:
            if slot.get("stage") in stages:
                targeted.setdefault(slot["slot_id"], []).append(reason)

    readiness = str(diagnosis.get("readiness", "")).lower()
    difficulty = str(diagnosis.get("recommended_difficulty", "")).lower()
    review = diagnosis.get("review_first") or []
    misconceptions = diagnosis.get("misconceptions") or []

    if readiness == "not_ready":
        # The whole hour goes to prerequisites. Nothing about the baseline
        # survives that, and pretending otherwise would teach the wrong lesson.
        return {
            "scope": "rebuild",
            "regenerate": [s["slot_id"] for s in slots],
            "reuse": [],
            "reasons": {"*": ["readiness is not_ready: the hour goes to "
                              "prerequisites, so this is a different lesson"]},
            "reuse_images": False,
        }

    if readiness == "ready_with_review" or review:
        mark(_STAGES_FOR["needs_review"],
             f"review needed first: {', '.join(map(str, review[:3])) or 'diagnosed gaps'}")
    if difficulty in {"below", "above"}:
        mark(_STAGES_FOR[difficulty],
             f"pitch the practice {difficulty} the curriculum default")
    for misconception in misconceptions[:3]:
        concept = misconception.get("concept", "")
        if concept:
            mark(_STAGES_FOR["misconception"],
                 f"address the misconception about {concept!r}")
    topics = preferences.get("preferred_topics") or []
    if topics:
        mark(_STAGES_FOR["topics"],
             f"use a context this learner cares about: {', '.join(topics[:3])}")

    regenerate = sorted(targeted)
    reuse = [s["slot_id"] for s in slots if s["slot_id"] not in targeted]

    # Images are the expensive half and are almost never what personalisation
    # changes: a picture of a garden is a picture of a garden whoever is looking
    # at it. Only a changed CONTEXT slot can invalidate one.
    context_stages = {"context", "situation", "encounter", "pre-reading"}
    images_affected = [
        s["slot_id"] for s in slots
        if s["slot_id"] in targeted and s.get("visual")
        and s.get("stage") in context_stages
    ]

    return {
        "scope": "targeted" if regenerate else "reuse",
        "regenerate": regenerate,
        "reuse": reuse,
        "reasons": {k: v for k, v in targeted.items()},
        "reuse_images": not images_affected,
        "images_to_remake": images_affected,
    }


def apply_plan(baseline: dict, plan: dict) -> dict:
    """Build the starting point for a personalised run from the baseline.

    Everything not being regenerated is carried through exactly as it was —
    same ids, same images, same urls. The generator receives this and is asked
    to rewrite only the named slots, which is the same instruction the quality
    loop uses for a failed item.
    """
    regenerate = set(plan.get("regenerate", []))
    package = json.loads(json.dumps(baseline.get("material", {})))
    package["items"] = [
        item for item in package.get("items", [])
        if item.get("blueprint_slot_id") not in regenerate
    ]
    return {
        "carried_items": package["items"],
        "package": package,
        "regenerate_slots": sorted(regenerate),
        "instructions": [
            {"target": slot, "scope": "item", "reasons": plan["reasons"].get(slot, []),
             "instructions": plan["reasons"].get(slot, [])}
            for slot in sorted(regenerate)
        ],
    }


def savings(blueprint: dict, plan: dict) -> dict:
    """What this personalisation costs against building the lesson again.

    Reported because the whole design is an economic claim, and a claim like
    that should be measured rather than asserted.
    """
    slots = blueprint.get("slots", []) or []
    total = len(slots) or 1
    redone = len(plan.get("regenerate", []))
    total_images = sum(1 for s in slots if s.get("visual"))
    remade = len(plan.get("images_to_remake", []) or [])
    return {
        "slots_total": total,
        "slots_regenerated": redone,
        "slots_reused": total - redone,
        "images_total": total_images,
        "images_remade": remade,
        "images_reused": total_images - remade,
        "work_avoided": f"{(1 - redone / total):.0%}",
    }
