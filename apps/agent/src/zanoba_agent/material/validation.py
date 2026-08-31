"""Structured validation of generated material, item by item.

The old checker asked a model whether the material was good. A model asked that
about material a model wrote says yes, and it said yes to a German lesson
written in English. So the questions that can be answered by counting are
answered here, in Python, and the model is left only the ones that genuinely
need reading.

Three groups, and the split matters because they fail differently:

  linguistic  — is it correct, natural, and at the band? A wrong answer key
                teaches the learner something false and then marks them wrong
                for disagreeing.
  pedagogical — does it serve an objective, does it do what its brief said, does
                the lesson progress, is the practice varied?
  technical   — are the required fields there, does the structure match the
                exercise type, does the picture match its brief, is anything
                duplicated or dangling?

Everything returns issues with an `item_id` and a `scope`, because that is what
makes regeneration targeted. An issue that cannot name what is wrong sends the
whole lesson round again and throws away the parts that were right.
"""

from __future__ import annotations

import re
import unicodedata
from collections import Counter
from typing import Any

from .images import named_images
from .language_purity import check_package as check_language
from .rubric import (
    EXERCISE_TYPES,
    MAX_OPERATION_SHARE,
    MIN_DISTINCT_OPERATIONS,
    MIN_DISTINCT_READING_SKILLS,
    MIN_PRODUCTIVE_DIRECTIONS,
    MIN_RECYCLED_SHARE,
    PRODUCTIVE_DIRECTIONS,
    SKILL_LADDER,
    SUPPORT_LEVELS,
    operation_variety_exempt,
    stage_order,
)

# What a failing check sends back for repair. The narrower the better: an image
# that came back wrong should cost one image, not a lesson.
SCOPE_IMAGE = "image"
SCOPE_EXERCISE = "exercise"
SCOPE_ITEM = "item"
SCOPE_STAGE = "stage"
SCOPE_LESSON = "lesson"

# Below this an item is not fit to teach and must be regenerated.
PASS_SCORE = 70

# What each severity costs the score. Tuned so one critical issue fails an item
# on its own, and a handful of low notes do not.
_WEIGHT = {"critical": 40, "high": 20, "medium": 8, "low": 3}


def _issue(item_id: str, scope: str, severity: str, category: str, problem: str,
           fix: str = "") -> dict:
    return {"item_id": item_id, "scope": scope, "severity": severity,
            "category": category, "problem": problem, "fix": fix}


def _score(issues: list[dict]) -> int:
    """100 minus what is wrong, charging each distinct defect once.

    The naive sum charged per issue, so one authoring mistake repeated across
    six exercises of the same item cost 120 points and took a finished lesson to
    zero — while a lesson with six DIFFERENT high-severity defects scored the
    same. That is precisely backwards: breadth of defect is worse than repetition
    of one, and the score has to be able to say so.

    So issues are grouped by what they are (severity, category, the shape of the
    problem) and where they are (the owning item). The first occurrence is
    charged in full, each repeat at a quarter, and the group is capped at twice
    the base weight — a repeated defect gets worse, but never unboundedly.
    """
    charged: Counter[tuple[str, str, str, str]] = Counter()
    for issue in issues:
        # Exercise and picture ids are "<item>/<exercise>" and "<item>#pic2";
        # both belong to the item that owns them.
        owner = re.split(r"[/#]", str(issue.get("item_id", "")))[0]
        shape = re.sub(r"\d+|'[^']*'|\"[^\"]*\"", "", issue.get("problem", ""))[:60]
        charged[(issue["severity"], issue.get("category", ""), owner, shape)] += 1

    total = 0.0
    for (severity, _, _, _), count in charged.items():
        weight = _WEIGHT.get(severity, 5)
        total += min(weight * 2, weight + (count - 1) * weight * 0.25)
    return max(0, round(100 - total))


def _words(text: str) -> list[str]:
    return re.findall(r"[^\W\d_]+", re.sub(r"<[^>]+>", " ", text or ""), re.UNICODE)


# ------------------------------------------------------------- technical ----

def inferred_direction(item: dict) -> str:
    """What retrieval a typed slide asks for, when the exercise does not say.

    A picture set whose captions are blank IS picture-to-word retrieval: the
    learner is looking at a photograph and has to produce the German. The
    material agent is supposed to label that on the exercise and routinely does
    not, so the check read an empty set and reported that no activity in the
    lesson made the learner produce a word — on a deck with three picture-naming
    slides in it. Reading the component is how the check sees what is actually
    on the page.

    A caption that is already filled in is the recognition version of the same
    slide, and is deliberately not counted as productive.
    """
    component = item.get("slide") or {}
    kind = component.get("kind", "")
    if kind == "picture_set":
        pictures = component.get("pictures") or []
        blank = [p for p in pictures if not str(p.get("caption", "")).strip()]
        return "picture_to_word" if blank else "word_to_meaning"
    if kind == "tile_grid":
        return "word_to_sentence"
    if kind in {"role_play", "bubble_exchange"}:
        return "situation_to_word"
    if kind == "dialogue" and (component.get("fill_ins") or []):
        return "context_to_word"
    if kind in {"sorting_grid", "choice_cards", "vocab_card"}:
        return "word_to_meaning"
    return ""


def component_options(item: dict) -> list[str]:
    """The choices a typed slide offers, when the exercise does not carry them.

    A sorting grid prints its categories once, above the tiles, and each item is
    "which column does this word go in" — so the options belong to the slide, not
    repeated onto six exercises. The checker did not know that and charged a
    twenty-point defect six times for a slide that renders perfectly, which on
    its own took a finished lesson to a score of zero.

    Same failure as the one in `check_images`: a rule written before the typed
    components existed, still asking the question the old shape answered.
    """
    component = item.get("slide") or {}
    for field in ("categories", "cards", "options", "word_bank"):
        values = component.get(field)
        if isinstance(values, list) and len(values) >= 2:
            return [str(v.get("text", v) if isinstance(v, dict) else v)
                    for v in values]
    return []


def check_structure(item: dict) -> list[dict]:
    """Are the required fields there, and does the structure match the type?

    A multiple-choice item with no options is not a multiple-choice item; a
    classification set with one category is a list. These are the failures that
    read fine in JSON and fall apart in front of a student.
    """
    issues: list[dict] = []
    iid = item.get("id", "?")

    if not str(item.get("title", "")).strip():
        issues.append(_issue(iid, SCOPE_ITEM, "high", "technical",
                             "item has no title", "write a target-language title"))
    # A slide counts. `MaterialItem` says "prefer `slide` to `content` always"
    # and treats prose as the fallback for the rare item no layout fits — so an
    # item carrying a rule table or a question list is complete, and this rule
    # used to fail it for the one field it was told not to use. Every French
    # maths lesson came out of the pipeline marked FAIL for that reason while
    # its material was in fact fine.
    if (not item.get("slide") and not str(item.get("content", "")).strip()
            and not item.get("exercises")):
        issues.append(_issue(iid, SCOPE_ITEM, "critical", "technical",
                             "item has no slide, no content and no exercises",
                             "regenerate the item from its blueprint slot"))
    if not str(item.get("pedagogical_purpose", "")).strip():
        issues.append(_issue(iid, SCOPE_ITEM, "medium", "pedagogical",
                             "item states no pedagogical purpose",
                             "carry the purpose through from the blueprint slot"))
    if not item.get("objective_ids"):
        issues.append(_issue(iid, SCOPE_ITEM, "high", "pedagogical",
                             "item serves no objective",
                             "name the objective ids, or drop the item"))
    if item.get("exercises") and not str(item.get("instruction", "")).strip():
        issues.append(_issue(iid, SCOPE_ITEM, "medium", "technical",
                             "an activity with no instruction line — the learner "
                             "does not know what to do",
                             "add a target-language imperative, e.g. 'Ordne zu.'"))

    for exercise in item.get("exercises") or []:
        eid = f"{iid}/{exercise.get('id', '?')}"
        etype = exercise.get("exercise_type")

        if not str(exercise.get("prompt", "")).strip():
            issues.append(_issue(eid, SCOPE_EXERCISE, "critical", "technical",
                                 "exercise has no prompt", "regenerate the item"))
        if not str(exercise.get("answer", "")).strip():
            issues.append(_issue(eid, SCOPE_EXERCISE, "critical", "linguistic",
                                 "exercise has no answer — it cannot be marked",
                                 "supply the answer, or regenerate the item"))
        if not str(exercise.get("pedagogical_purpose", "")).strip():
            issues.append(_issue(eid, SCOPE_EXERCISE, "low", "pedagogical",
                                 "exercise states no purpose"))

        if etype in {"multiple_choice", "classification"}:
            options = exercise.get("options") or component_options(item)
            if len(options) < 2:
                issues.append(_issue(
                    eid, SCOPE_EXERCISE, "high", "technical",
                    f"{etype} item has {len(options)} options",
                    "give 2-4 options, with plausible distractors"))
            elif exercise.get("answer") and str(exercise["answer"]).strip() not in [
                    str(o).strip() for o in options]:
                issues.append(_issue(
                    eid, SCOPE_EXERCISE, "critical", "linguistic",
                    f"the answer {exercise['answer']!r} is not among the options "
                    f"{options} — the item is unanswerable as printed",
                    "make the answer one of the options"))
        if etype == "gap_fill" and "_" not in str(exercise.get("prompt", "")):
            issues.append(_issue(eid, SCOPE_EXERCISE, "medium", "technical",
                                 "a gap-fill prompt with no gap in it",
                                 "mark the gap, e.g. '_______ Garten'"))
        if etype == "open_production" and not exercise.get("acceptable_answers"):
            issues.append(_issue(
                eid, SCOPE_EXERCISE, "medium", "pedagogical",
                "an open item with a single answer — the learner will be marked "
                "wrong for a different correct response",
                "list acceptable_answers, or describe what makes one acceptable"))
        if etype in {"matching", "classification"} and not exercise.get("explanation"):
            issues.append(_issue(eid, SCOPE_EXERCISE, "low", "pedagogical",
                                 "no explanation of why the pairing is right"))

    return issues


def check_answers_are_findable(item: dict) -> list[dict]:
    """An answer key printed on the worksheet is not an answer key."""
    issues: list[dict] = []
    iid = item.get("id", "?")
    content = str(item.get("content", ""))
    for exercise in item.get("exercises") or []:
        answer = str(exercise.get("answer", "")).strip()
        prompt = str(exercise.get("prompt", ""))
        # Only worth flagging when the answer is a distinctive string; "der"
        # appears in any German paragraph and means nothing here.
        if len(answer) >= 8 and answer.lower() in prompt.lower():
            issues.append(_issue(
                f"{iid}/{exercise.get('id','?')}", SCOPE_EXERCISE, "high", "pedagogical",
                "the answer is printed inside the prompt",
                "remove it from the prompt; the answer belongs in the key"))
    if content and len(content) > 40:
        for exercise in item.get("exercises") or []:
            answer = str(exercise.get("answer", "")).strip()
            if len(answer) >= 12 and answer.lower() in content.lower():
                issues.append(_issue(
                    iid, SCOPE_ITEM, "medium", "pedagogical",
                    f"the answer to {exercise.get('id')} appears in the item's own "
                    "content, so the task requires no work",
                    "move it to answer_key"))
    return issues


# ------------------------------------------------------------ linguistic ----

# Roughly what a sentence may run to at each band before it is above level.
_MAX_SENTENCE_WORDS = {"A1": 9, "A2": 12, "B1": 18, "B2": 25}


def check_cefr(item: dict, band: str) -> list[dict]:
    """Is the language at the band, measured rather than judged?

    Sentence length is the one CEFR proxy that can be counted honestly. It does
    not catch a B1 word in an A1 text — that needs reading — but it reliably
    catches the A1 lesson whose explanation runs to three subordinate clauses.
    """
    ceiling = _MAX_SENTENCE_WORDS.get((band or "").upper())
    if not ceiling:
        return []
    issues: list[dict] = []
    iid = item.get("id", "?")
    text = " ".join(str(item.get(f, "")) for f in ("content", "instruction"))
    text = re.sub(r"<[^>]+>|[*_#>`|-]", " ", text)
    long_ones = []
    for sentence in re.split(r"(?<=[.!?])\s+|\n", text):
        count = len(_words(sentence))
        if count > ceiling:
            long_ones.append((count, sentence.strip()[:70]))
    if long_ones:
        worst = max(long_ones)
        issues.append(_issue(
            iid, SCOPE_ITEM, "medium" if len(long_ones) < 3 else "high", "linguistic",
            f"{len(long_ones)} sentences run past the {band} ceiling of {ceiling} "
            f"words; the longest is {worst[0]}: {worst[1]!r}",
            f"break them up; at {band} a sentence is {ceiling} words or fewer"))
    return issues


def check_duplication(package: dict) -> list[dict]:
    """The same exercise printed twice is not two exercises."""
    issues: list[dict] = []
    prompts: dict[str, list[str]] = {}
    for item in package.get("items", []) or []:
        for exercise in item.get("exercises") or []:
            key = re.sub(r"[\W_]+", "", str(exercise.get("prompt", ""))).lower()
            if len(key) < 6:
                continue
            prompts.setdefault(key, []).append(f"{item.get('id')}/{exercise.get('id')}")
    for key, where in prompts.items():
        if len(where) > 1:
            issues.append(_issue(
                where[-1], SCOPE_EXERCISE, "medium", "pedagogical",
                f"this prompt already appears at {where[0]}",
                "replace it, or drop it — a repeated item teaches nothing twice"))

    titles = Counter(str(i.get("title", "")).strip().lower()
                     for i in package.get("items", []) or [] if i.get("title"))
    for title, count in titles.items():
        if count > 1:
            issues.append(_issue("", SCOPE_LESSON, "low", "pedagogical",
                                 f"{count} items share the title {title!r}"))
    return issues


# ----------------------------------------------------- against the brief ----

def check_against_blueprint(package: dict, blueprint: dict) -> list[dict]:
    """Did the generator build what was specified, or something else?

    This is the check the pipeline could not previously make at all, because
    there was no specification to compare against. A slot that was planned and
    never filled is a tutor arriving at minute 30 with nothing; a set specified
    as six matching items that arrives as three gap-fills is a lesson whose
    progression no longer holds, however good the three items are.
    """
    issues: list[dict] = []
    slots = {s.get("slot_id"): s for s in blueprint.get("slots", []) or []}
    if not slots:
        return issues

    by_slot: dict[str, list[dict]] = {}
    for item in package.get("items", []) or []:
        by_slot.setdefault(item.get("blueprint_slot_id", ""), []).append(item)

    for slot_id, slot in slots.items():
        filled = by_slot.get(slot_id) or []
        if not filled:
            issues.append(_issue(
                slot_id, SCOPE_ITEM, "critical", "technical",
                f"blueprint slot {slot_id!r} ({slot.get('stage')}) was specified "
                "and never generated",
                f"generate it: {slot.get('pedagogical_goal', '')[:120]}"))
            continue

        for item in filled:
            iid = item.get("id", "?")
            if slot.get("stage") and item.get("stage") != slot.get("stage"):
                issues.append(_issue(
                    iid, SCOPE_ITEM, "medium", "pedagogical",
                    f"item is stage {item.get('stage')!r} but its slot is "
                    f"{slot.get('stage')!r}",
                    "set the stage to the slot's"))

            spec = slot.get("exercise")
            if not spec:
                continue
            exercises = item.get("exercises") or []
            wanted, got = spec.get("number_of_items", 0), len(exercises)
            if got < wanted:
                issues.append(_issue(
                    iid, SCOPE_ITEM, "high" if got == 0 else "medium", "technical",
                    f"slot {slot_id} specified {wanted} items and got {got}",
                    f"write the missing {wanted - got}"))
            wrong_type = [
                f"{iid}/{e.get('id')}" for e in exercises
                if e.get("exercise_type") and e["exercise_type"] != spec.get("exercise_type")
            ]
            if wrong_type:
                issues.append(_issue(
                    iid, SCOPE_ITEM, "high", "pedagogical",
                    f"slot {slot_id} specified {spec.get('exercise_type')!r} but "
                    f"{len(wrong_type)} items are a different type",
                    "rewrite them as the specified type, or the progression the "
                    "blueprint planned no longer holds"))

    for item in package.get("items", []) or []:
        slot_id = item.get("blueprint_slot_id", "")
        if slot_id and slot_id not in slots:
            issues.append(_issue(
                item.get("id", "?"), SCOPE_ITEM, "medium", "technical",
                f"item points at slot {slot_id!r}, which is not in the blueprint",
                "point it at a real slot, or drop it"))
        elif not slot_id:
            issues.append(_issue(
                item.get("id", "?"), SCOPE_ITEM, "medium", "technical",
                "item names no blueprint slot, so it cannot be regenerated "
                "targetedly or graded against a brief",
                "set blueprint_slot_id"))
    return issues


def check_images(package: dict, images_produced: bool = True) -> list[dict]:
    """Does each picture exist, and does it satisfy the brief it was made from?

    Existence is countable and checked here. Whether the picture *reads* as its
    target concept is a judgement, and belongs to the model — but it can only be
    asked usefully because the brief says what the picture was supposed to show.

    `images_produced` says whether the pipeline has run yet. The material agent
    is told, in bold, to leave every picture "pending" because it does not
    generate images. Checking a draft as though it should have them told the
    agent that ten pictures it was forbidden to produce were each a critical
    defect, against an instruction to emit nothing that fails — an unsatisfiable
    loop, and the agent stopped emitting anything at all. On a draft, the brief
    is the agent's responsibility and the file is not.
    """
    issues: list[dict] = []
    for item in package.get("items", []) or []:
        for where, image in named_images(item):
            provider = str(image.get("provider", "pending")).lower()
            url = str(image.get("url", "")).strip()

            if images_produced:
                if provider == "failed":
                    issues.append(_issue(
                        where, SCOPE_IMAGE, "critical", "technical",
                        f"image generation failed: "
                        f"{image.get('reason', 'no reason given')}",
                        "regenerate this image only"))
                elif provider == "pending" or not url:
                    issues.append(_issue(
                        where, SCOPE_IMAGE, "critical", "technical",
                        "image is specified but not produced — a deck of "
                        "promises arrives at the lesson blank",
                        "regenerate this image only"))
            if not str(image.get("alt_text", "")).strip():
                issues.append(_issue(where, SCOPE_IMAGE, "medium", "technical",
                                     "image has no alt text"))

            spec = image.get("spec")
            if not spec:
                # A search query says what the picture must show just as well as
                # a specification does, and costs twenty times less to write.
                # Demanding the full spec on every picture is what made a
                # vocabulary lesson's output too large to finish.
                if not str(image.get("search_query", "")).strip():
                    issues.append(_issue(
                        where, SCOPE_IMAGE, "high", "pedagogical",
                        "image says nothing about what it should show — no "
                        "search query and no visual specification",
                        "write a search_query, or drop the image"))
                continue
            # The prompt built from a no-text brief ENDS with "No text,
            # letters, words, numbers, labels or watermarks" — so a naive search
            # for those words flags every correctly-built prompt. Strip the
            # negations first and look at what is actually being asked for.
            prompt = str(image.get("prompt", ""))
            asked_for = re.sub(
                r"(?:no|not|without|avoid|must not (?:appear|show|contain))\b[^.]*\.?",
                " ", prompt, flags=re.I)
            if spec.get("text_allowed") is False and re.search(
                    r"\b(text|label|caption|writing|sign|written words)\b",
                    asked_for, re.I):
                issues.append(_issue(
                    where, SCOPE_IMAGE, "medium", "technical",
                    f"the brief forbids text but the prompt asks for it: "
                    f"{asked_for.strip()[:70]!r}",
                    "rebuild the prompt from the specification"))
            if not spec.get("must_not_show"):
                issues.append(_issue(
                    where, SCOPE_IMAGE, "low", "pedagogical",
                    "the brief names nothing to exclude, so competing readings "
                    "were never ruled out"))
    return issues


# ----------------------------------------------------------- the lesson ----

def check_progression(package: dict, focus: str = "grammar") -> list[dict]:
    """Does the lesson as generated still progress, and is the practice varied?

    The blueprint was validated for this, but the generator can still collapse
    it — by dropping a stage, or by writing every set as the same task under
    different headings.
    """
    issues: list[dict] = []
    staged = [i for i in package.get("items", []) or [] if i.get("stage")]
    orders = [(i.get("id"), stage_order(focus, i["stage"])) for i in staged]
    known = [o for o in orders if o[1]]
    if known != sorted(known, key=lambda x: x[1]):
        issues.append(_issue(
            "", SCOPE_LESSON, "high", "pedagogical",
            f"items are not in stage order: {[i['stage'] for i in staged]}",
            "reorder the items; practice before presentation teaches nothing"))

    operations = [e.get("operation") for i in package.get("items", []) or []
                  for e in i.get("exercises") or [] if e.get("operation")]
    practice = [e.get("operation") for i in package.get("items", []) or []
                if not operation_variety_exempt(focus, i.get("stage") or "")
                for e in i.get("exercises") or [] if e.get("operation")]
    if len(operations) >= 4:
        distinct = len(set(operations))
        if distinct < MIN_DISTINCT_OPERATIONS:
            issues.append(_issue(
                "", SCOPE_LESSON, "high", "pedagogical",
                f"{len(operations)} exercises using only {distinct} cognitive "
                f"operations {sorted(set(operations))}",
                "vary what the learner actually does between sets"))
    if len(practice) >= 4:
        commonest, count = Counter(practice).most_common(1)[0]
        if count / len(practice) > MAX_OPERATION_SHARE:
            issues.append(_issue(
                "", SCOPE_LESSON, "medium", "pedagogical",
                f"{count} of {len(practice)} practice exercises are {commonest!r}",
                "replace some with a different cognitive operation"))

    # Measured against the highest rung reached so far: a lesson may drop back
    # (a recycling stage returns to recognition on purpose), and what matters is
    # whether the learner has ever been supported at this level.
    reached = 0
    for item in package.get("items", []) or []:
        for exercise in item.get("exercises") or []:
            rank = SKILL_LADDER.get(exercise.get("skill") or "", 0)
            if not rank:
                continue
            if reached and rank - reached > 2:
                issues.append(_issue(
                    item.get("id", "?"), SCOPE_STAGE, "high", "pedagogical",
                    f"this jumps {rank - reached} rungs past anything the lesson "
                    "has practised with support",
                    "add a controlled or guided step before this one"))
                return issues
            reached = max(reached, rank)
    return issues


# --------------------------------------------------------- communication ----

def check_communicative_task(package: dict, blueprint: dict) -> list[dict]:
    """Is the final activity a real task, or a conversation in costume?

    The test that matters cannot be fully automated — could the learner finish
    this while avoiding the target language? — but two halves of it can. A task
    with no information gap and no goal is two people reading sentences at each
    other, and a lesson whose support never falls has scaffolded the learner all
    the way to the end and called the last slide a role-play.
    """
    issues: list[dict] = []
    task = (blueprint or {}).get("communicative_task")
    if not task:
        return issues

    final_stages = {"communicative-task", "independent-communication",
                    "communicative-practice", "communicative-use"}
    finals = [i for i in package.get("items", []) or [] if i.get("stage") in final_stages]
    if not finals:
        issues.append(_issue(
            "", SCOPE_LESSON, "critical", "pedagogical",
            "the lesson has no communicative task; the learner practised the "
            "language and never used it for anything",
            "generate the task stage from the blueprint"))
        return issues

    required = [str(p).lower() for p in task.get("required_language", [])]
    for item in finals:
        iid = item.get("id", "?")
        blob = " ".join([
            str(item.get("content", "")), str(item.get("instruction", "")),
            " ".join(str(e.get("prompt", "")) for e in item.get("exercises") or []),
        ]).lower()
        if required and not any(_normalise(p) and _normalise(p) in _normalise(blob)
                                for p in required):
            issues.append(_issue(
                iid, SCOPE_ITEM, "high", "pedagogical",
                "the task uses none of the language the lesson taught, so it does "
                "not require the target language to complete",
                f"build it around: {', '.join(task.get('required_language', [])[:3])}"))
        if not task.get("information_gap") and "gap" not in blob and "?" not in blob:
            issues.append(_issue(
                iid, SCOPE_ITEM, "medium", "pedagogical",
                "no information gap and no questions: both speakers already know "
                "everything, so there is no reason to speak",
                "give each side something the other lacks"))

    if not task.get("success_criteria"):
        issues.append(_issue(
            "", SCOPE_LESSON, "high", "pedagogical",
            "the task has no observable success criteria, so nobody can say "
            "whether communication succeeded",
            "list what the learner must actually be seen to do"))
    return issues


def check_support_fades(package: dict, blueprint: dict) -> list[dict]:
    """Scaffolding must come off, or the final task was read aloud."""
    issues: list[dict] = []
    slots = {s.get("slot_id"): s for s in (blueprint or {}).get("slots", []) or []}
    if not slots:
        return issues
    ranked = []
    for item in package.get("items", []) or []:
        slot = slots.get(item.get("blueprint_slot_id"))
        if slot and slot.get("support_level") in SUPPORT_LEVELS:
            ranked.append((item.get("id"), SUPPORT_LEVELS[slot["support_level"]]))
    if ranked and min(r for _, r in ranked) > SUPPORT_LEVELS["low"]:
        issues.append(_issue(
            "", SCOPE_LESSON, "high", "pedagogical",
            "every activity is highly supported; the learner never performs "
            "anything with the scaffolding removed",
            "make the final task low-support or independent"))
    return issues


# ------------------------------------------------------------ vocabulary ----

def check_vocabulary(package: dict, blueprint: dict) -> list[dict]:
    """Is the vocabulary retrieved and recycled, or listed and quizzed?

    Two failures, both of which the old pipeline had. Testing only recognition
    produces a learner who can pick a word out of four and cannot say it. And a
    word introduced once and never seen again was not taught, however good the
    slide that introduced it was.
    """
    issues: list[dict] = []
    selection = (blueprint or {}).get("vocabulary")
    if not selection:
        return issues

    directions: set[str] = set()
    for item in package.get("items", []) or []:
        declared = {e.get("retrieval_direction") for e in item.get("exercises") or []
                    if e.get("retrieval_direction")}
        directions |= declared or {inferred_direction(item)}
    directions.discard("")

    productive = directions & PRODUCTIVE_DIRECTIONS
    if len(productive) < MIN_PRODUCTIVE_DIRECTIONS:
        found = ", ".join(sorted(productive)) if productive else "none"
        issues.append(_issue(
            "", SCOPE_LESSON, "high", "pedagogical",
            f"{len(productive)} of the {MIN_PRODUCTIVE_DIRECTIONS} required "
            f"productive retrieval directions are present ({found}); the rest of "
            "the lesson only asks the learner to recognise the word",
            "add picture-to-word or situation-to-word retrieval"))

    entries = [e for e in selection.get("entries", []) or [] if not e.get("is_known")]
    corpus = _normalise(" ".join(
        [str(i.get("content", "")) + " " + str(i.get("instruction", "")) +
         " " + " ".join(str(x.get("prompt", "")) + str(x.get("answer", ""))
                        for x in i.get("exercises") or [])
         for i in package.get("items", []) or []]))
    appearances = {}
    for entry in entries:
        lemma = _normalise(entry.get("lemma", ""))
        if not lemma:
            continue
        appearances[entry["lemma"]] = corpus.count(lemma)

    never = [w for w, n in appearances.items() if n == 0]
    once = [w for w, n in appearances.items() if n == 1]
    if never:
        issues.append(_issue(
            "", SCOPE_LESSON, "critical", "pedagogical",
            f"vocabulary selected but never used in any material: {never[:8]}",
            "teach them or remove them from the selection"))
    if appearances and len(once) / len(appearances) > (1 - MIN_RECYCLED_SHARE):
        issues.append(_issue(
            "", SCOPE_LESSON, "high", "pedagogical",
            f"{len(once)} of {len(appearances)} words appear exactly once and are "
            f"never recycled: {once[:8]}",
            "bring them back in a later retrieval or recycling activity"))

    for entry in entries:
        lemma = entry.get("lemma", "?")
        example = str(entry.get("example", ""))
        if not example.strip():
            issues.append(_issue(
                lemma, SCOPE_EXERCISE, "medium", "pedagogical",
                f"{lemma!r} has no example sentence, so it is a glossary entry"))
        elif _normalise(lemma) and example.lower().count(lemma.split()[0].lower()) > 1:
            issues.append(_issue(
                lemma, SCOPE_EXERCISE, "medium", "linguistic",
                f"the example for {lemma!r} repeats the word rather than showing "
                f"it in use: {example[:60]!r}",
                "write a sentence a person would actually say"))
    return issues


def check_objective_alignment(package: dict, objectives: dict) -> list[dict]:
    """Every objective taught, and nothing taught that serves no objective."""
    issues: list[dict] = []
    known = {o.get("id") for o in objectives.get("objectives", []) or []}
    if not known:
        return issues
    served: set[str] = set()
    for item in package.get("items", []) or []:
        ids = [o for o in (item.get("objective_ids") or []) if o]
        served.update(ids)
        unknown = [o for o in ids if o not in known]
        if unknown:
            issues.append(_issue(
                item.get("id", "?"), SCOPE_ITEM, "medium", "technical",
                f"item cites objectives {unknown} that do not exist",
                "point it at a real objective"))
    missing = sorted(known - served)
    if missing:
        issues.append(_issue(
            "", SCOPE_LESSON, "critical", "pedagogical",
            f"objectives {missing} have no material teaching them — they will not "
            "happen",
            "generate material for them"))
    return issues


# --------------------------------------------------------------- reading ----

def _normalise(text: str) -> str:
    """Collapse case, punctuation and accents so a quote can be matched fairly.

    Evidence is quoted by a model, and a model re-typing its own French will
    straighten a curly apostrophe, drop a comma, and write "aeroport" for
    "aéroport". None of those means the answer is unsupported.

    The comparison is deliberately permissive, because this check marks failures
    CRITICAL: a false positive here condemns correct material and teaches
    everyone downstream to ignore the checker, which costs more than the rare
    invented quote that slips past.
    """
    folded = unicodedata.normalize("NFKD", (text or "").lower())
    stripped = "".join(c for c in folded if not unicodedata.combining(c))
    return re.sub(r"[^\w]+", "", stripped, flags=re.UNICODE)


def check_reading_evidence(package: dict) -> list[dict]:
    """Every comprehension answer must be supported by words in the text.

    This is the reading lesson's version of `verify_calculation`: the claim is
    checked against the source rather than against the model's confidence. A
    question whose `evidence_text` does not appear in any text in the package is
    a question about a passage that does not say what it claims — the single
    most common defect in generated reading material, and one that reads
    perfectly plausibly.

    Gist questions are exempt from quoting, because their evidence genuinely is
    the whole text.
    """
    issues: list[dict] = []
    texts = {
        item.get("id"): _normalise(item.get("content", ""))
        for item in package.get("items", []) or []
        if item.get("kind") in {"text", "dialogue", "reading_text"}
        or item.get("stage") in {"gist", "detail", "encounter", "situation"}
    }
    corpus = " ".join(texts.values())
    if not corpus:
        return issues

    for item in package.get("items", []) or []:
        stage = item.get("stage")
        if stage not in {"gist", "detail", "inference", "vocabulary-in-context"}:
            continue
        for exercise in item.get("exercises") or []:
            eid = f"{item.get('id', '?')}/{exercise.get('id', '?')}"
            quote = str(exercise.get("evidence_text", "")).strip()

            if stage == "gist":
                continue
            if not quote:
                issues.append(_issue(
                    eid, SCOPE_EXERCISE, "high", "pedagogical",
                    f"a {stage} question with no evidence quoted from the text",
                    "quote the words that support the answer, verbatim"))
                continue
            if _normalise(quote) not in corpus:
                issues.append(_issue(
                    eid, SCOPE_EXERCISE, "critical", "linguistic",
                    f"the evidence quoted for this answer does not appear in the "
                    f"text: {quote[:70]!r}",
                    "either the question is unanswerable from this text or the "
                    "quote is invented; regenerate the question against the text"))
            if not str(exercise.get("evidence_location", "")).strip():
                issues.append(_issue(
                    eid, SCOPE_EXERCISE, "low", "technical",
                    "no evidence_location, so the tutor cannot point at it"))

            # An 'inference' question whose answer is quoted verbatim from the
            # text is a detail question wearing the wrong label.
            if stage == "inference":
                answer = _normalise(str(exercise.get("answer", "")))
                if len(answer) > 12 and answer in _normalise(quote):
                    issues.append(_issue(
                        eid, SCOPE_EXERCISE, "medium", "pedagogical",
                        "this is labelled inference but the answer is stated "
                        "word-for-word in the evidence — it is a detail question",
                        "ask for something the text implies rather than states, "
                        "or move it to the detail stage"))
    return issues


def check_reading_question_spread(package: dict) -> list[dict]:
    """A set of questions that all test one skill is a test, not a lesson."""
    issues: list[dict] = []
    skills = [e.get("reading_skill") for i in package.get("items", []) or []
              for e in i.get("exercises") or [] if e.get("reading_skill")]
    if len(skills) >= 4 and len(set(skills)) < MIN_DISTINCT_READING_SKILLS:
        issues.append(_issue(
            "", SCOPE_LESSON, "high", "pedagogical",
            f"all {len(skills)} questions test {sorted(set(skills))}",
            "spread the questions across gist, detail and at least one of "
            "inference or context-inference"))
    return issues


def check_distractors(package: dict) -> list[dict]:
    """Multiple choice with an obviously right answer teaches nothing.

    Only the countable half is done here: options that repeat, and options so
    much shorter or longer than the rest that the answer is guessable from its
    shape alone. Whether a distractor is *plausible* needs reading.
    """
    issues: list[dict] = []
    for item in package.get("items", []) or []:
        for exercise in item.get("exercises") or []:
            options = [str(o).strip() for o in (exercise.get("options") or []) if str(o).strip()]
            if len(options) < 2:
                continue
            eid = f"{item.get('id', '?')}/{exercise.get('id', '?')}"
            if len(set(o.lower() for o in options)) != len(options):
                issues.append(_issue(
                    eid, SCOPE_EXERCISE, "high", "technical",
                    f"the same option appears twice: {options}",
                    "give distinct options"))
            lengths = [len(o) for o in options]
            answer = str(exercise.get("answer", "")).strip()
            if answer in options and len(options) > 2 and max(lengths) > 3 * min(lengths):
                if len(answer) == max(lengths):
                    issues.append(_issue(
                        eid, SCOPE_EXERCISE, "medium", "pedagogical",
                        "the correct option is far longer than every distractor, "
                        "so it can be picked without reading the text",
                        "make the options comparable in length"))
    return issues


# ----------------------------------------------------------- the verdict ----

# The dimensions each focus is scored on. Reported separately because "the
# material is weak" is not actionable and "interaction_quality 40" is: it names
# which half of the lesson to send back.
DIMENSIONS_BY_FOCUS: dict[str, list[str]] = {
    "grammar": ["linguistic_accuracy", "level_appropriateness", "progression",
                "objective_alignment", "variety", "visual_quality"],
    "communication": ["communication_alignment", "authenticity", "naturalness",
                      "level_appropriateness", "progression", "interaction_quality",
                      "visual_quality"],
    "vocabulary": ["vocabulary_selection", "level_appropriateness", "meaning_clarity",
                   "example_quality", "retrieval_quality", "contextualisation",
                   "recycling", "productive_use", "visual_quality"],
    "reading": ["text_quality", "level_appropriateness", "coherence",
                "reading_skill_alignment", "question_quality", "evidence_alignment",
                "vocabulary_load", "visual_quality", "progression"],
}

# Which category of issue counts against which dimension. An issue can weigh on
# more than one; a wrong answer is both a linguistic defect and a question-quality
# defect, and both scores should show it.
_DIMENSION_SOURCES: dict[str, set[str]] = {
    "linguistic_accuracy": {"linguistic"},
    "naturalness": {"linguistic"},
    "text_quality": {"linguistic"},
    "coherence": {"linguistic", "pedagogical"},
    "meaning_clarity": {"linguistic"},
    "example_quality": {"linguistic", "pedagogical"},
    "level_appropriateness": {"linguistic"},
    "vocabulary_load": {"linguistic"},
    "question_quality": {"technical", "linguistic"},
    "evidence_alignment": {"linguistic"},
    "progression": {"pedagogical"},
    "objective_alignment": {"pedagogical"},
    "variety": {"pedagogical"},
    "communication_alignment": {"pedagogical"},
    "authenticity": {"pedagogical"},
    "interaction_quality": {"pedagogical"},
    "vocabulary_selection": {"pedagogical"},
    "retrieval_quality": {"pedagogical"},
    "contextualisation": {"pedagogical"},
    "recycling": {"pedagogical"},
    "productive_use": {"pedagogical"},
    "reading_skill_alignment": {"pedagogical"},
    "visual_quality": set(),
}


def _dimension_scores(issues: list[dict], focus: str) -> dict[str, int]:
    """Score each dimension off the issues that bear on it."""
    scores: dict[str, int] = {}
    for dimension in DIMENSIONS_BY_FOCUS.get(focus, DIMENSIONS_BY_FOCUS["grammar"]):
        if dimension == "visual_quality":
            relevant = [i for i in issues if i["scope"] == SCOPE_IMAGE]
        else:
            sources = _DIMENSION_SOURCES.get(dimension, set())
            relevant = [i for i in issues
                        if i["category"] in sources and i["scope"] != SCOPE_IMAGE]
        scores[dimension] = _score(relevant)
    return scores


def validate_package(package: dict, blueprint: dict | None = None,
                     objectives: dict | None = None, band: str = "",
                     target_language: str = "", focus: str = "",
                     images_produced: bool = True) -> dict[str, Any]:
    """Run every structural check and return one structured report.

    The shape is the brief's: a status, an overall score, a score per dimension,
    the issues, the critical ones called out separately, and whether
    regeneration is required — with targets, so the repair is the smallest one
    that fixes the problem.

    Which checks run depends on the focus, because the four kinds of lesson fail
    differently. A vocabulary lesson fails by testing recognition and calling it
    practice; a reading lesson fails by asking a question the text does not
    answer; a communication lesson fails by scaffolding the learner all the way
    to the end. None of those is detectable by the checks that catch the others.
    """
    blueprint = blueprint or {}
    focus = focus or blueprint.get("focus") or "grammar"
    band = band or blueprint.get("band", "")
    issues: list[dict] = []

    for item in package.get("items", []) or []:
        issues += check_structure(item)
        issues += check_answers_are_findable(item)
        if band:
            issues += check_cefr(item, band)

    issues += check_duplication(package)
    issues += check_images(package, images_produced)
    issues += check_distractors(package)
    issues += check_progression(package, focus)
    if objectives:
        issues += check_objective_alignment(package, objectives)
    if blueprint:
        issues += check_against_blueprint(package, blueprint)

    if focus == "reading":
        issues += check_reading_evidence(package)
        issues += check_reading_question_spread(package)
    if focus in {"communication", "speaking"}:
        issues += check_communicative_task(package, blueprint)
        issues += check_support_fades(package, blueprint)
    if focus == "vocabulary":
        issues += check_vocabulary(package, blueprint)
        issues += check_support_fades(package, blueprint)

    language = (target_language or package.get("target_language")
                or blueprint.get("target_language") or "").strip()
    if language:
        purity = check_language(package, language)
        for violation in purity["violations"]:
            # An exercise-level id needs exercise scope, or the repair planner
            # cannot collapse five English prompts in one item into one rewrite
            # of that item — and lists five separate repairs instead.
            scope = SCOPE_EXERCISE if "/" in violation["item_id"] else SCOPE_ITEM
            issues.append(_issue(
                violation["item_id"], scope,
                "critical" if violation["severity"] == "high" else "medium",
                "linguistic",
                f"{violation['field']} is in English, not {language}: "
                f"{', '.join(violation['markers'][:6])}",
                f"rewrite this field in {language}. The whole lesson is in "
                f"{language} — titles, instructions, prompts and answers."))

    critical = [i for i in issues if i["severity"] == "critical"]
    score = _score(issues)
    regenerate = bool(critical) or score < PASS_SCORE

    return {
        "status": "FAIL" if regenerate else "PASS",
        "focus": focus,
        "overall_score": score,
        "score": score,
        **_dimension_scores(issues, focus),
        "issues": issues,
        "critical_issues": critical,
        "regeneration_required": regenerate,
        "regeneration_targets": build_regeneration_plan(issues),
        "regeneration_instructions": build_regeneration_plan(issues),
        "counts": {
            "items": len(package.get("items", []) or []),
            "exercises": sum(len(i.get("exercises") or [])
                             for i in package.get("items", []) or []),
            "images": sum(len(i.get("images") or [])
                          for i in package.get("items", []) or []),
            "by_severity": dict(Counter(i["severity"] for i in issues)),
            "by_category": dict(Counter(i["category"] for i in issues)),
        },
    }


# The order repairs are attempted in: narrowest first. Regenerating a lesson
# because one image came back wrong is both slower and worse — it throws away
# everything that was right.
_SCOPE_RANK = {SCOPE_IMAGE: 0, SCOPE_EXERCISE: 1, SCOPE_ITEM: 2,
               SCOPE_STAGE: 3, SCOPE_LESSON: 4}


def build_regeneration_plan(issues: list[dict]) -> list[dict]:
    """Turn issues into the smallest set of repairs that fixes them.

    Groups by target and keeps the widest scope needed for that target, so an
    item with three broken exercises is regenerated once rather than three
    times, and an item that also has a bad image does not regenerate the image
    twice.
    """
    repairs: dict[tuple[str, str], dict] = {}
    for issue in issues:
        if issue["severity"] not in {"critical", "high"}:
            continue
        target, scope = issue["item_id"], issue["scope"]
        # An exercise-level failure is repaired by rewriting its item; the item
        # is the unit the generator actually writes.
        if scope == SCOPE_EXERCISE and "/" in target:
            target = target.split("/", 1)[0]
        if scope == SCOPE_IMAGE and "#" in target:
            target = target.split("#", 1)[0] + "#" + target.split("#", 1)[1]
        key = (target, scope)
        entry = repairs.setdefault(key, {
            "target": target, "scope": scope, "reasons": [], "instructions": []})
        entry["reasons"].append(issue["problem"])
        if issue.get("fix"):
            entry["instructions"].append(issue["fix"])

    # A lesson-scope repair subsumes everything narrower; say so rather than
    # emitting both and regenerating twice.
    plan = sorted(repairs.values(), key=lambda r: _SCOPE_RANK.get(r["scope"], 9))
    if any(r["scope"] == SCOPE_LESSON for r in plan):
        narrow = [r for r in plan if r["scope"] != SCOPE_LESSON]
        wide = [r for r in plan if r["scope"] == SCOPE_LESSON]
        # Only escalate to the whole lesson when the blueprint itself is wrong;
        # a missing objective is fixed by generating that material, not by
        # discarding the lesson.
        for repair in wide:
            repair["note"] = ("lesson-wide, but repair the listed targets first — "
                              "only regenerate everything if the blueprint is invalid")
        plan = narrow + wide
    for repair in plan:
        repair["reasons"] = repair["reasons"][:5]
        repair["instructions"] = list(dict.fromkeys(repair["instructions"]))[:5]
    return plan
