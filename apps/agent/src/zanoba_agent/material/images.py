"""Producing the pictures a lesson needs.

Turns an image *specification* into an image and stores it in Cloud Storage,
returning a URL the deck can actually render — the distinction `deck_spec`
refuses to let slide past, because a deck of promises arrives at the lesson
blank.

There are two ways to obtain a picture and this module owns the choice between
them. `photos.search` finds a real photograph in a stock library; `generate`
asks Gemini's image model for one. Search wins wherever the thing exists in the
world, which is most of a language course: a table, a station, a flag, two
people at a counter. Generation wins for the staged situation with the exact
props a lesson needs, and whenever the search comes back empty — which it is
allowed to do, because falling back to generation is much better than a blank
slide.

Two things it does not do. It does not decorate: the caller decides an image
earns its place, and a grammar drill on article endings does not get one. And it
does not silently succeed — a lookup or a generation that fails returns
`provider: "failed"` with the reason, so the quality gate sees a missing picture
rather than a plausible-looking record of one.
"""

from __future__ import annotations

import hashlib
import os
from typing import Any

from . import photos

# Photographs, not clip art. The reference decks use real photography of people
# in ordinary situations, which is what makes them readable as context rather
# than as illustration.
STYLE = (
    "Clean, bright, photographic, natural daylight, realistic, shallow depth of "
    "field. Documentary style photograph for a language textbook. "
    "Not an illustration, not a cartoon, not a drawing, not clip art, not 3D "
    "render, no cute mascots, no anthropomorphic animals. "
    "No text, no letters, no words, no numbers, no captions, no labels, no "
    "watermarks anywhere in the image."
)

# One deck, one look. The first build mixed a cartoon owl, a flat vector graphic
# and three photographs across six slides, which reads as a lesson assembled from
# whatever was to hand — because it was. Every prompt gets the same style
# suffix, and a slot may only override it by saying so in its specification.
NEGATIVE = (
    "cartoon, illustration, drawing, sketch, clip art, vector art, 3D render, "
    "anime, painting, collage, text overlay, caption, watermark, logo, "
    "distorted hands, extra limbs, "
    # Asked for a flag or a landmark the model reaches for a monochrome art
    # shot, which sits on a slide between colour photographs and reads as a
    # mistake. Refused after the fact too, in `generate`.
    "black and white, greyscale, grayscale, monochrome, sepia, desaturated"
)

DEFAULT_MODEL = os.environ.get("ZANOBA_IMAGE_MODEL", "gemini-3.1-flash-image")
BUCKET = os.environ.get("ZANOBA_MATERIAL_BUCKET", "ai-tutor-zanoba-material")

_client = None
_storage = None


def _genai():
    global _client
    if _client is None:
        from google import genai

        _client = genai.Client()
    return _client


def _bucket():
    global _storage
    if _storage is None:
        from google.cloud import storage

        _storage = storage.Client(
            project=os.environ.get("GOOGLE_CLOUD_PROJECT", "ai-tutor-zanoba")
        )
    return _storage.bucket(BUCKET)


def _key(prompt: str, lesson_id: str) -> str:
    """A stable name, so the same picture for the same lesson is made once."""
    digest = hashlib.sha256(f"{lesson_id}|{prompt}".encode()).hexdigest()[:20]
    safe = "".join(c if c.isalnum() or c in "-_" else "-" for c in lesson_id)[:48]
    return f"lessons/{safe or 'lesson'}/{digest}.png"


def _store(data: bytes, mime: str, key: str) -> str:
    """Put the bytes in the bucket and return the URL the deck renders."""
    blob = _bucket().blob(key)
    blob.upload_from_string(data, content_type=mime or "image/png")
    return blob.public_url


def queries_from_spec(spec: dict[str, Any] | None,
                      fallback: str = "") -> list[str]:
    """Build the stock-library search terms from the visual specification.

    Same reasoning as `prompt_from_spec`: composed from the brief rather than
    written freehand, so what was asked for and what was looked up are the same
    document. Note this is NOT the generator prompt — a search engine handed
    "Must NOT appear: people" returns pictures of people.

    A ladder rather than one string; `VisualSpec.to_search_queries` explains why.
    """
    if not spec:
        return [fallback] if fallback else []
    from ..schemas.blueprint import VisualSpec

    try:
        return VisualSpec(**spec).to_search_queries()
    except Exception:
        return [fallback] if fallback else []


def search_photo(query: str | list[str], alt_text: str, purpose: str,
                 lesson_id: str = "",
                 orientation: str = "landscape") -> dict[str, Any]:
    """Find a real photograph, download it, store it, return an image record.

    Tries the candidates in the order the library ranked them and takes the
    first that downloads as a printable image — a result whose URL 404s or comes
    back as an SVG is common enough that stopping at the first candidate loses
    roughly one picture in six for no reason.

    On success `provider` is "searched", `url` points at the stored copy and
    `credit` carries the attribution the licence asks for. On failure `provider`
    is "failed" with a reason, which is the caller's signal to generate instead.
    """
    rungs = [query] if isinstance(query, str) else list(query)
    rungs = [r.strip() for r in rungs if r and r.strip()]
    record: dict[str, Any] = {
        "prompt": rungs[0] if rungs else "", "alt_text": alt_text,
        "purpose": purpose, "provider": "pending", "url": "", "credit": "",
        "source_page": "",
    }
    if not rungs:
        return record | {"provider": "failed", "reason": "empty search query"}

    found = photos.search(rungs, count=6, orientation=orientation)
    if not found["candidates"]:
        return record | {"provider": "failed",
                         "reason": f"no photo found: {found.get('reason', '')}"
                                   f" {found.get('attempted', '')}".strip()}

    rejected_monochrome = 0
    for candidate in found["candidates"]:
        key = _key(f"photo|{candidate['url']}", lesson_id)
        try:
            blob = _bucket().blob(key)
            if blob.exists():
                url = blob.public_url
            else:
                data, mime = photos.fetch(candidate)
                # A black-and-white shot between four colour ones reads as a
                # mistake. Judged after downloading because no library will say
                # in advance, and skipped rather than failed — the next
                # candidate is usually in colour.
                if photos.is_monochrome(data):
                    rejected_monochrome += 1
                    continue
                url = _store(data, mime, key)
        except Exception:
            continue  # next candidate; a dead link is not a failed lesson
        return record | {
            "provider": "searched", "url": url,
            "search_query": found["query"],
            "credit": photos.credit(candidate),
            "source_page": candidate.get("source_page", ""),
            "found_as": candidate.get("title", ""),
            "library": candidate.get("provider", ""),
        }

    return record | {"provider": "failed",
                     "reason": f"{len(found['candidates'])} candidates from "
                               f"{found['provider']}, none usable "
                               f"({rejected_monochrome} were black-and-white)"}


def prompt_from_spec(spec: dict[str, Any] | None, fallback: str = "") -> str:
    """Build the generator's prompt from the visual specification.

    Built from the brief rather than written freehand so that what was asked for
    and what gets checked are the same document. A prompt composed by hand can
    quietly drop the exclusions, which is how a picture of a Garten came back
    containing a house.
    """
    if not spec:
        return fallback
    from ..schemas.blueprint import VisualSpec

    try:
        return VisualSpec(**spec).to_prompt()
    except Exception:
        # A malformed spec is not worth failing the whole lesson over; fall back
        # to the prompt the generator wrote and let the checker judge it.
        return fallback


def generate(prompt: str, alt_text: str, purpose: str, lesson_id: str = "",
             model: str | None = None, spec: dict[str, Any] | None = None,
             avoid: list[str] | None = None) -> dict[str, Any]:
    """Generate one image and store it. Returns an image record for the deck.

    `spec` is the visual specification; when present it is what the prompt is
    built from, so the exclusions the planner wrote actually reach the model.
    `avoid` carries the reasons previous attempts were rejected, which is what
    makes a regeneration a different request rather than the same one again.

    On success `provider` is "generated" and `url` points at the stored file. On
    failure `provider` is "failed" with a reason — never "generated" with no
    file behind it, which is the failure mode that would defeat the point of
    checking at all.
    """
    prompt = prompt_from_spec(spec, prompt)
    record: dict[str, Any] = {
        "prompt": prompt, "alt_text": alt_text, "purpose": purpose,
        "provider": "pending", "url": "",
    }
    if not prompt.strip():
        return record | {"provider": "failed", "reason": "empty prompt"}
    if avoid:
        prompt = (prompt + " Avoid what made previous attempts unusable: "
                  + "; ".join(avoid[:3]) + ".")
        record["prompt"] = prompt

    key = _key(prompt, lesson_id)
    try:
        blob = _bucket().blob(key)
        # Already made for this lesson: reuse rather than pay twice.
        if blob.exists():
            return record | {"provider": "generated", "url": blob.public_url,
                             "reused": True}

        response = _genai().models.generate_content(
            model=model or DEFAULT_MODEL,
            contents=f"{prompt}\n\n{STYLE}\n\nAvoid entirely: {NEGATIVE}.",
        )
        parts = response.candidates[0].content.parts if response.candidates else []
        images = [p for p in parts if getattr(p, "inline_data", None)]
        if not images:
            return record | {"provider": "failed", "reason": "model returned no image"}

        data = images[0].inline_data
        # The colour rule applies to both routes. It was written for the search
        # half only, and the very next build came back with six generated
        # pictures on one slide, three of them colourless — the rule had been
        # enforced where it was easy rather than where it was needed.
        if photos.is_monochrome(data.data):
            return record | {"provider": "failed",
                             "reason": "the model returned a black-and-white "
                                       "image; ask again in colour"}
        url = _store(data.data, data.mime_type or "image/png", key)
        return record | {"provider": "generated", "url": url,
                         "bytes": len(data.data)}
    except Exception as exc:  # surfaced, never swallowed into a fake success
        return record | {"provider": "failed", "reason": f"{type(exc).__name__}: {exc}"}


def resolve(image: dict[str, Any], lesson_id: str = "") -> dict[str, Any]:
    """Obtain one picture, by whichever route its specification asks for.

    `spec.source` decides:

      photo_search   look it up; if nothing usable comes back, generate, because
                     a picture from the wrong route beats a blank slide
      generate       generate, and do not search — this is the staged scene
      auto (default) search first, generate on an empty result

    The record that comes back always says which route actually produced it, so
    "we asked for a photograph and got a rendering" is visible in the material
    rather than inferred from looking at it.
    """
    spec = image.get("spec")
    source = "auto"
    if isinstance(spec, dict):
        source = str(spec.get("source") or "auto")

    prompt = prompt_from_spec(spec, image.get("prompt", ""))
    alt_text, purpose = image.get("alt_text", ""), image.get("purpose", "")

    if source != "generate":
        queries = queries_from_spec(spec, image.get("search_query") or prompt)
        found = search_photo(queries, alt_text, purpose, lesson_id)
        if found["provider"] == "searched":
            return found | {"prompt": prompt}
        # Keep why the search failed: it is the evidence for whether the search
        # route is worth having, and it is invisible once a generated picture
        # sits in the same field.
        fallback_reason = found.get("reason", "")
    else:
        fallback_reason = ""

    made = generate(prompt=prompt, alt_text=alt_text, purpose=purpose,
                    lesson_id=lesson_id, spec=spec,
                    avoid=image.get("rejected_reasons"))
    if fallback_reason:
        made["search_fallback"] = fallback_reason
    return made


# Words that are a description of a picture rather than the thing in it. A
# search for "a photograph of an open book" ranks photographs of the words.
_NOISE = {
    "a", "an", "the", "photo", "photograph", "picture", "image", "of", "on",
    "with", "showing", "shows", "against", "isolated", "close-up", "closeup",
    "view", "ein", "eine", "einer", "einem", "auf", "mit", "und",
}


def backfill_specs(package: dict) -> int:
    """Give every picture that lacks a brief something to look up.

    The typed slide components carry their own pictures, and the material agent
    is told to copy the blueprint's VisualSpec onto each one. When it does not —
    and on a long lesson it sometimes does not — the picture has an `alt_text`
    and an `answer` and nothing to generate or search from, so it is skipped and
    the slide renders as a caption with a hole above it. That is the single most
    visible defect in the decks built so far.

    A picture that knows what word it is the picture OF does not need a model to
    tell it what to look for. So the query is composed from what is already
    there: the answer, then the caption, then the alt text with its
    picture-describing words stripped out.

    Returns how many were filled in, which is a number worth watching: if it is
    large, the material agent is not carrying specifications through and the
    prompt is what needs fixing.
    """
    def query_for(picture: dict) -> str:
        for field in ("answer", "caption"):
            value = str(picture.get(field) or "").strip()
            if value:
                # An article is part of what a German vocabulary card teaches
                # and no help at all to a photo library.
                words = [w for w in value.split()
                         if w.lower() not in {"der", "die", "das", "ein", "eine"}]
                if words:
                    return " ".join(words)
        alt = str(picture.get("alt_text") or "")
        words = [w.strip(".,;:") for w in alt.split()]
        kept = [w for w in words if w.lower().strip(".,;:") not in _NOISE]
        return " ".join(kept[:8])

    filled = 0
    for picture in _every_image(package):
        has_brief = bool(picture.get("spec")) or bool(str(picture.get("prompt") or "").strip())
        if has_brief or str(picture.get("provider", "pending")).lower() != "pending":
            continue
        query = query_for(picture)
        if not query:
            continue
        picture["prompt"] = query
        picture["search_query"] = query
        picture["backfilled"] = True
        filled += 1
    return filled


def named_images(item: dict):
    """Every picture on one item, wherever it lives, with a name for it.

    The name is what the checker reports and what `regenerate` resolves, so the
    two have to agree — and they only agree by being the same function. They
    were not, which is how a picture set could be rejected for five missing
    photographs that no regeneration target could name.
    """
    iid = item.get("id", "?")
    for index, image in enumerate(item.get("images") or []):
        yield f"{iid}#img{index}", image
    for index, exercise in enumerate(item.get("exercises") or []):
        if isinstance(exercise.get("image"), dict):
            yield f"{iid}#ex{index}", exercise["image"]
    component = item.get("slide") or {}
    for index, picture in enumerate(component.get("pictures") or []):
        yield f"{iid}#pic{index}", picture
    for field in ("scene", "illustration", "picture"):
        if isinstance(component.get(field), dict):
            yield f"{iid}#{field}", component[field]


def _every_image(package: dict):
    """Every picture in the package, wherever it lives.

    Three places, and missing any one of them produces a lesson that is
    billed for images and renders without them:

      item["images"]              the item-level pictures
      exercise["image"]           one per item in a picture-matching task
      item["slide"][...]          the typed component's own pictures

    The third is the one that went wrong: the components were added and the
    walk was not extended, so every slide rendered bare while the images
    were generated against a field nothing read.
    """
    picture_fields = ("scene", "illustration", "picture")
    for item in package.get("items", []):
        for image in item.get("images") or []:
            yield image
        for exercise in item.get("exercises") or []:
            if exercise.get("image"):
                yield exercise["image"]
        component = item.get("slide") or {}
        for picture in component.get("pictures") or []:
            yield picture
        for field in picture_fields:
            if isinstance(component.get(field), dict):
                yield component[field]


def produce_for_package(package: dict, lesson_id: str = "", limit: int = 12) -> dict:
    """Obtain every pending picture in a material package, in place.

    `limit` caps how many pictures one lesson may cost. Beyond it the remaining
    specifications stay pending, which the quality gate will report — a visible
    shortfall is better than an invisible bill. A searched photograph counts
    against it too, even though it is free, because a fifty-picture lesson is a
    planning defect whatever the pictures cost.
    """
    backfilled = backfill_specs(package)
    lesson_id = lesson_id or package.get("target_item_id", "")

    searched = made = failed = skipped = 0
    for image in _every_image(package):
        if str(image.get("provider", "pending")).lower() != "pending":
            continue
        if searched + made >= limit:
            skipped += 1
            continue
        result = resolve(image, lesson_id)
        image.update(result)
        if result["provider"] == "searched":
            searched += 1
        elif result["provider"] == "generated":
            made += 1
        else:
            failed += 1
    return {"searched": searched, "generated": made, "failed": failed,
            "skipped_over_limit": skipped, "backfilled_briefs": backfilled}


def regenerate(package: dict, targets: list[dict], lesson_id: str = "") -> dict:
    """Remake only the pictures the checker rejected.

    `targets` are the checker's regeneration targets whose scope is "image",
    each naming a picture by the name `named_images` gave it and carrying the
    reason it failed. The reason is written onto the record and folded into the
    next attempt, so the second try is a different request — asking for the same
    picture again reliably returns the same picture.

    A rejected picture is REMADE, not re-searched: whatever the search returned
    was judged wrong, and the library will return it again. So the retry goes
    straight to the generator, where the rejection reasons can actually change
    what comes back.

    Everything not named is left exactly as it is. That is the whole point: a
    lesson with one bad photograph should cost one photograph.
    """
    wanted: dict[str, list[str]] = {}
    for target in targets or []:
        if target.get("scope") != "image":
            continue
        ref = str(target.get("target", ""))
        if "#" in ref:
            wanted[ref] = list(target.get("reasons") or [])

    remade = failed = untouched = 0
    for item in package.get("items", []):
        for name, image in named_images(item):
            reasons = wanted.get(name)
            if reasons is None:
                untouched += 1
                continue
            previous = list(image.get("rejected_reasons") or []) + reasons
            result = generate(
                prompt=prompt_from_spec(image.get("spec"), image.get("prompt", "")),
                alt_text=image.get("alt_text", ""),
                purpose=image.get("purpose", ""),
                lesson_id=lesson_id or package.get("target_item_id", ""),
                spec=image.get("spec"),
                avoid=previous,
            )
            image.update(result)
            image["attempts"] = int(image.get("attempts", 0)) + 1
            image["rejected_reasons"] = previous
            if result["provider"] == "generated":
                remade += 1
            else:
                failed += 1
    return {"requested": len(wanted), "regenerated": remade, "failed": failed,
            "untouched": untouched}
