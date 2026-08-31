"""Render the decks for every warmed lesson in a chapter, from the cache.

`warm_lessons.py` builds and stores the material; this turns what it stored into
the PDF a student actually sees. Kept apart from the warm run because rendering
is free and instant while building is neither — a layout fix should not cost a
second lesson.

    python scripts/render_cached_decks.py german a1-1 a1-1.myself
    python scripts/render_cached_decks.py english a1-1 a1-1.intro
"""
from __future__ import annotations

import sys
from pathlib import Path

from zanoba_agent.curriculum import repository
from zanoba_agent.material import cache, deck
from zanoba_agent.material.validation import validate_package


def main(subject="german", level="a1-1", chapter=None, out_root="out/chapters"):
    band = repository.band_of(subject, level)
    items = [i for i in repository.items_in_order(subject, level)
             if chapter is None or i.parent_id == chapter]

    for item in items:
        entry = cache.load_baseline(subject, item.id, band)
        if entry is None:
            print(f"  {item.id:24} not warmed")
            continue
        package, plan = entry["material"], entry["plan"]
        objectives, blueprint = entry["objectives"], entry.get("blueprint", {})

        report = validate_package(package, blueprint=blueprint or None,
                                  objectives=objectives, band=band,
                                  focus=item.focus or "",
                                  target_language=package.get("target_language", ""))
        # How each picture was actually obtained. The whole point of the search
        # route is that this should mostly say "searched".
        routes: dict[str, int] = {}
        from zanoba_agent.material.images import named_images
        for entry_item in package.get("items", []):
            for _, picture in named_images(entry_item):
                routes[str(picture.get("provider", "?"))] = \
                    routes.get(str(picture.get("provider", "?")), 0) + 1

        built = deck.build(package, plan, objectives,
                           Path(out_root) / subject / item.id)
        print(f"  {item.id:24} {str(item.focus or '-'):14} "
              f"{len(built['slides']):>3} slides  "
              f"{report['status']:4} score={report['overall_score']:>3}  "
              f"pictures={routes}  -> {built['pdf']}")


if __name__ == "__main__":
    main(*(sys.argv[1:] or []))
