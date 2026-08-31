"""Finding a real photograph, rather than asking a model to imagine one.

The reference decks are illustrated with stock photography — a real kitchen, a
real ticket machine, two real people at a counter. That is most of why they read
as courseware rather than as generated material, and it is the one thing an
image model reliably cannot do: asked for "a wooden table on a white background"
it produces a plausible table with five legs, and asked for the German flag it
produces three stripes in roughly the right colours.

So the picture pipeline gets a second way to obtain an image. For a concrete
noun a search is better, faster and free; for a staged classroom scene with the
exact people and props a lesson needs, generation is better. `images.resolve`
chooses; this module is only the search half of it.

Three libraries, tried in order, because they fail differently:

  Pexels     professional stock photography of people and places — the Lingoda
             look. Needs PEXELS_API_KEY (free). Its licence permits commercial
             use without attribution.
  Openverse  Creative Commons aggregator, keyless. Deep on objects and places,
             thin on staged people. Attribution required, and carried.
  Wikimedia  Commons, keyless. The one that actually has flags, landmarks and
             maps, which the other two return holiday snapshots for.

Everything here returns evidence rather than raising: a lookup that fails leaves
the caller to generate instead, which is a smaller problem than no picture.
"""

from __future__ import annotations

import html
import os
import re
from typing import Any, Callable

import httpx

# Commons and Openverse both ask for a real User-Agent and rate-limit anonymous
# clients that do not send one.
USER_AGENT = "zanoba-agent/1.0 (language course material; +https://zanoba.com)"

TIMEOUT = 20.0

# Below this the picture is a thumbnail and prints badly on an A4 slide.
MIN_WIDTH = 640

# File types the deck's renderer can actually place. SVG comes back from
# Commons for flags and maps and renders as a blank box.
GOOD_TYPES = ("image/jpeg", "image/png", "image/webp")


def _pexels_key() -> str:
    return os.environ.get("PEXELS_API_KEY", "").strip()


def _plain(markup: str) -> str:
    """Strip the markup Commons puts in its metadata.

    The Artist field is a rendered HTML link, so a credit line taken from it
    verbatim printed `<a rel="nofollow" class="external text" href=...` under
    the photograph.
    """
    text = re.sub(r"<[^>]+>", " ", markup or "")
    text = html.unescape(text)
    return " ".join(text.split())


def _client() -> httpx.Client:
    return httpx.Client(timeout=TIMEOUT, follow_redirects=True,
                        headers={"User-Agent": USER_AGENT})


# ------------------------------------------------------------- providers ----

def _pexels(query: str, count: int, orientation: str) -> list[dict[str, Any]]:
    """Professional stock photography. Needs a key; returns nothing without one."""
    key = _pexels_key()
    if not key:
        return []
    with _client() as client:
        response = client.get(
            "https://api.pexels.com/v1/search",
            params={"query": query, "per_page": count,
                    "orientation": orientation, "size": "medium"},
            headers={"Authorization": key},
        )
        response.raise_for_status()
        photos = response.json().get("photos") or []
    return [
        {
            "provider": "pexels",
            "url": (photo.get("src") or {}).get("large")
                   or (photo.get("src") or {}).get("original", ""),
            "title": (photo.get("alt") or "").strip(),
            "creator": photo.get("photographer", ""),
            "license": "Pexels License",
            "license_url": "https://www.pexels.com/license/",
            "source_page": photo.get("url", ""),
            "width": int(photo.get("width") or 0),
            "height": int(photo.get("height") or 0),
        }
        for photo in photos
    ]


def _openverse(query: str, count: int, orientation: str) -> list[dict[str, Any]]:
    """Creative Commons aggregator. Keyless, commercial-use filter applied."""
    with _client() as client:
        response = client.get(
            "https://api.openverse.org/v1/images/",
            # "commercial,modification" is both filters, not one: a deck crops
            # and rescales every picture it places, so an ND photograph is not
            # usable here however freely it may be shown elsewhere.
            params={"q": query, "page_size": count,
                    "license_type": "commercial,modification",
                    "aspect_ratio": "wide" if orientation == "landscape" else "tall",
                    "mature": "false"},
        )
        response.raise_for_status()
        results = response.json().get("results") or []
    return [
        {
            "provider": "openverse",
            "url": result.get("url", ""),
            "title": (result.get("title") or "").strip(),
            "creator": _plain(result.get("creator") or "")
                       .removeprefix("Photographer:").strip(),
            "license": f"CC {(result.get('license') or '').upper()} "
                       f"{result.get('license_version') or ''}".strip(),
            "license_url": result.get("license_url") or "",
            "source_page": result.get("foreign_landing_url") or "",
            "width": int(result.get("width") or 0),
            "height": int(result.get("height") or 0),
        }
        for result in results
    ]


def _wikimedia(query: str, count: int, orientation: str) -> list[dict[str, Any]]:
    """Wikimedia Commons. The one that has flags, landmarks and real places."""
    with _client() as client:
        response = client.get(
            "https://commons.wikimedia.org/w/api.php",
            params={
                "action": "query", "format": "json", "generator": "search",
                "gsrsearch": f"filetype:bitmap {query}", "gsrnamespace": 6,
                "gsrlimit": count, "prop": "imageinfo",
                "iiprop": "url|size|mime|extmetadata", "iiurlwidth": 1280,
            },
        )
        response.raise_for_status()
        pages = (response.json().get("query") or {}).get("pages") or {}

    candidates = []
    for page in pages.values():
        info = (page.get("imageinfo") or [{}])[0]
        meta = info.get("extmetadata") or {}
        get = lambda field: str((meta.get(field) or {}).get("value", "")).strip()
        candidates.append({
            "provider": "wikimedia",
            "url": info.get("thumburl") or info.get("url", ""),
            "title": str(page.get("title", "")).removeprefix("File:"),
            "creator": _plain(get("Artist"))[:120],
            "license": get("LicenseShortName") or "see Commons",
            "license_url": get("LicenseUrl"),
            "source_page": info.get("descriptionurl", ""),
            "width": int(info.get("thumbwidth") or info.get("width") or 0),
            "height": int(info.get("thumbheight") or info.get("height") or 0),
            "mime": info.get("mime", ""),
        })
    return candidates


# The order matters: the first library that returns something usable wins, and
# they are ranked by how close their output is to what the reference decks use.
ALL_PROVIDERS: tuple[tuple[str, Callable[..., list[dict[str, Any]]]], ...] = (
    ("pexels", _pexels),
    ("openverse", _openverse),
    ("wikimedia", _wikimedia),
)


def _providers() -> tuple[tuple[str, Callable[..., list[dict[str, Any]]]], ...]:
    """Which libraries may be searched, given that the deck prints no credits.

    The Pexels licence permits use without attribution. The Creative Commons
    ones do not: a CC BY photograph on an uncredited slide is a licence
    violation, however small. So when Pexels is available it is the only library
    used, and the CC aggregators are the fallback for having no key at all —
    where the alternative is not "an uncredited photograph" but "no lesson".

    Restore the full list by printing credits again in `layouts._photo`, not by
    editing this function.
    """
    return ALL_PROVIDERS[:1] if _pexels_key() else ALL_PROVIDERS[1:]


# Kept as a module attribute so tests and callers can substitute it wholesale.
PROVIDERS = ALL_PROVIDERS


def _usable(candidate: dict[str, Any]) -> bool:
    """Reject what would print badly before anything is downloaded."""
    url = str(candidate.get("url") or "")
    if not url.startswith("http"):
        return False
    if url.lower().rsplit("?", 1)[0].endswith((".svg", ".gif", ".tif", ".tiff")):
        return False
    width = int(candidate.get("width") or 0)
    return width == 0 or width >= MIN_WIDTH


# Words that carry no meaning in a query and match everything in a title.
_STOPWORDS = frozenset(
    "a an the of on in at with and or for to from is are this that plain "
    "background isolated white close up view photo photograph picture image "
    "two three some several his her their".split()
)


def _content_words(text: str) -> set[str]:
    """The words in a title or a query that are worth matching on."""
    words = re.split(r"[^\w]+", (text or "").lower())
    return {w for w in words if len(w) > 2 and w not in _STOPWORDS}


def relevance(candidate: dict[str, Any], query: str) -> float:
    """How much of the query the candidate's title actually accounts for.

    A search engine always returns something. Asked for "two women talking in a
    cafe" Wikimedia returned a bass guitarist at the Hard Rock Cafe, and asked
    for "a cup of coffee" Openverse returned a plate of eggs — both ranked first,
    both entirely wrong, and both would have gone straight onto a slide.

    A title is weak evidence, but zero overlap with the query is strong evidence:
    whatever the picture shows, nobody filed it under the thing being asked for.
    So a candidate that shares no content word with the query is dropped, and the
    rest are ordered by how much they share. What survives is not guaranteed to
    be right — a doll's-house table still matches "wooden dining table" — which
    is why Pexels is first in the list and these two are the fallback.
    """
    wanted = _content_words(query)
    if not wanted:
        return 1.0
    return len(wanted & _content_words(candidate.get("title", ""))) / len(wanted)


def search(query: str | list[str], count: int = 6, orientation: str = "landscape",
           providers: tuple[str, ...] | None = None) -> dict[str, Any]:
    """Look for a photograph of something, across the libraries in order.

    `query` may be one string or a ladder of them, most specific first. Every
    library is asked for the first rung before the second is tried, because a
    precise query answered by the third library beats a vague one answered by
    the first.

    Returns the candidates, which library answered and which rung it answered.
    An empty `candidates` is a normal outcome, not an error — it is the signal
    to generate instead.
    """
    rungs = [query] if isinstance(query, str) else list(query)
    rungs = [r.strip() for r in rungs if r and r.strip()]
    if not rungs:
        return {"query": "", "candidates": [], "provider": "",
                "reason": "empty query"}

    available = PROVIDERS if PROVIDERS is not ALL_PROVIDERS else _providers()
    attempted: list[str] = []
    for rung in rungs:
        for name, provider in available:
            if providers is not None and name not in providers:
                continue
            try:
                raw = [c for c in provider(rung, count, orientation) if _usable(c)]
            except Exception as exc:  # a library being down is not a lesson failure
                attempted.append(f"{name} ({type(exc).__name__})")
                continue
            scored = [(relevance(c, rung), c) for c in raw]
            found = [c for score, c in sorted(scored, key=lambda p: -p[0]) if score > 0]
            if found:
                return {"query": rung, "provider": name, "candidates": found,
                        "attempted": attempted, "rung": rungs.index(rung)}
            attempted.append(
                f"{name} ({len(raw)} results for {rung!r}, none about it)"
                if raw else f"{name} (no results for {rung!r})")

    return {"query": rungs[0], "candidates": [], "provider": "",
            "attempted": attempted, "reason": "no library had a usable photo"}


# Below this mean channel spread a photograph is black-and-white, sepia or
# duotone. Measured on a 64x64 thumbnail, an ordinary colour photograph scores
# 30-80 and a greyscale one scores 0-3; the threshold sits well clear of both.
COLOUR_THRESHOLD = 12.0


def is_monochrome(data: bytes, threshold: float = COLOUR_THRESHOLD) -> bool:
    """Is this photograph black-and-white, sepia or otherwise colourless?

    Stock libraries file monochrome shots under the same terms as colour ones,
    so a vocabulary test came back with a black-and-white Sagrada Familia and a
    black-and-white Statue of Liberty sitting between four colour flags. On a
    slide that reads as a mistake rather than as a style.

    Measured rather than asked for, because no library exposes a "colour only"
    filter: the mean spread between a pixel's brightest and darkest channel is
    near zero for greyscale, small for sepia, and large for anything else.

    An image that cannot be decoded is not judged monochrome — that would throw
    away a usable photograph over a decoder problem. It is let through and fails
    later on its own merits, if at all.
    """
    try:
        import io

        from PIL import Image

        with Image.open(io.BytesIO(data)) as image:
            sample = image.convert("RGB").resize((64, 64))
        pixels = list(getattr(sample, "get_flattened_data", sample.getdata)())
    except Exception:
        return False
    if not pixels:
        return False
    spread = sum(max(p) - min(p) for p in pixels) / len(pixels)
    return spread < threshold


def fetch(candidate: dict[str, Any]) -> tuple[bytes, str]:
    """Download one candidate. Raises, so the caller can fall back to generating."""
    with _client() as client:
        response = client.get(str(candidate.get("url", "")))
        response.raise_for_status()
        mime = (response.headers.get("content-type") or "").split(";")[0].strip()
        if mime not in GOOD_TYPES:
            raise ValueError(f"{mime or 'unknown'} is not a printable image type")
        return response.content, mime


def credit(candidate: dict[str, Any]) -> str:
    """The one-line credit printed under a picture.

    Pexels does not require it and the CC licences do, so it is written for all
    of them rather than remembered for some — a deck that credits half its
    photographs looks worse than one that credits all of them.
    """
    creator = str(candidate.get("creator") or "").strip()
    licence = str(candidate.get("license") or "").strip()
    provider = str(candidate.get("provider") or "").strip()
    parts = [p for p in (creator, licence, provider.capitalize()) if p]
    return " · ".join(parts)
