"""Print a built lesson as readable text, slide by slide.

    python scripts/show_lesson.py grammar
    python scripts/show_lesson.py grammar --answers
"""
import json, sys
from pathlib import Path

focus = (sys.argv[1:] or ["grammar"])[0]
show_answers = "--answers" in sys.argv
path = Path(f"out/lesson-{focus}.json")
if not path.exists():
    raise SystemExit(f"{path} not built yet. Available: "
                     + ", ".join(p.stem.replace('lesson-', '')
                                 for p in Path('out').glob('lesson-*.json')))

d = json.loads(path.read_text(encoding="utf-8"))
material, blueprint = d["material"], d.get("blueprint", {})
slots = {s["slot_id"]: s for s in blueprint.get("slots", [])}

print(f"\n{material.get('target_item_title') or material.get('target_item_id')}"
      f"   [{blueprint.get('focus', '')} · {blueprint.get('band', '')} · "
      f"{material.get('target_language', '')}]")
print(f"{blueprint.get('grammar_point') or blueprint.get('context', '')}")
print("=" * 76)
for objective in d.get("objectives", {}).get("objectives", []):
    print(f"  ● {objective['statement']}")

for item in material.get("items", []):
    slot = slots.get(item.get("blueprint_slot_id"), {})
    print(f"\n{'-' * 76}\n[{item.get('stage', '?')}]  {item.get('title', '')}")
    if item.get("instruction"):
        print(f"  » {item['instruction']}")
    print(f"  · why: {(slot.get('pedagogical_goal') or item.get('pedagogical_purpose') or '')[:150]}")
    if item.get("content"):
        for line in item["content"].splitlines():
            print(f"    {line}")
    for exercise in item.get("exercises") or []:
        answer = f"   → {exercise['answer']}" if show_answers else ""
        options = f"   ({' / '.join(exercise['options'])})" if exercise.get("options") else ""
        print(f"    {exercise['id']}. {exercise['prompt']}{options}{answer}")
        if show_answers and exercise.get("evidence_text"):
            print(f"        evidence: {exercise['evidence_text'][:80]!r}")
    for image in item.get("images") or []:
        spec = image.get("spec") or {}
        state = image.get("provider", "?")
        print(f"    [IMAGE · {spec.get('visual_type', '?')} · {state}] "
              f"{spec.get('target_concept', '')}")
        if spec.get("must_not_show"):
            print(f"        must not show: {', '.join(spec['must_not_show'])}")
