"""Tools for the two Material agents, and for the Quality checker.

The diagram gives each material agent its own box. They share nothing except
`generate_examples`, so they are kept apart here too — a language agent has no
business calling `verify_calculation` and a maths agent has no use for CEFR
guidelines.

The one tool that is not a convenience: `verify_calculation`. It runs real
arithmetic in Python, not a model, because the brief forbids trusting the
generator to check itself.
"""

from __future__ import annotations

from ..curriculum import repository
from ..material.arithmetic import check as _check

# CEFR descriptors are reference data, not something to be recalled from memory
# and half-remembered. Kept short deliberately: what a planner needs is the
# ceiling for a band, not the full framework.
_CEFR: dict[str, dict] = {
    "A1": {"sentence_length": "3-7 words", "tenses": ["present"],
           "vocabulary": "~500 highest-frequency words, concrete and everyday",
           "avoid": ["subordinate clauses", "past tenses", "passive voice", "idiom"]},
    "A2": {"sentence_length": "5-10 words", "tenses": ["present", "simple past", "perfect"],
           "vocabulary": "~1000 words, everyday topics and routines",
           "avoid": ["subjunctive", "complex relative clauses", "abstract argument"]},
    "B1": {"sentence_length": "8-15 words",
           "tenses": ["present", "past", "perfect", "future", "conditional"],
           "vocabulary": "~2000 words, familiar and some abstract topics",
           "avoid": ["specialist register", "literary or archaic forms"]},
    "B2": {"sentence_length": "10-20 words", "tenses": ["all common tenses", "passive"],
           "vocabulary": "~4000 words, abstract and technical within a field",
           "avoid": ["dense idiom without context"]},
}


def get_cefr_guidelines(band: str) -> dict:
    """Return what language is appropriate at one CEFR band.

    Args:
      band: A CEFR band, e.g. "A1".

    Returns:
      Sentence length, permitted tenses, vocabulary size and what to avoid at
      that band. Use it to pitch a text, not to guess.
    """
    key = (band or "").strip().upper()
    if key not in _CEFR:
        return {"error": f"No guidelines for {band!r}.", "available": sorted(_CEFR)}
    return {"band": key, **_CEFR[key]}


# What each curriculum's language code means, so the answer to "what language is
# this lesson in" is a name the agents can act on rather than an ISO code.
_LANGUAGE_NAMES = {
    "de": "german", "fr": "french", "es": "spanish", "it": "italian",
    "en": "english", "ar": "arabic", "zh": "chinese", "ko": "korean",
}


def get_target_language(subject: str) -> dict:
    """Return the language this lesson must be written in.

    Args:
      subject: Subject id, e.g. "german".

    Returns:
      The target language, read off the curriculum file rather than inferred.
      EVERYTHING the learner reads is written in it — titles, instruction lines,
      exercise prompts, options, answers, the summary, the word list.

      A German lesson is in German from the cover to the last page. A French
      lesson is in French. There is no English scaffolding around
      target-language content: the instruction is "Ordne zu." or "Lisez le
      texte.", never "Match the following" or "Read the text".

      The one exception is a word being discussed AS a foreign word, in quotes.
    """
    try:
        curriculum = repository.load(subject)
    except repository.CurriculumNotFound:
        return {"error": f"No curriculum for {subject!r}.",
                "available": sorted(repository.available_subjects())}
    code = str(getattr(curriculum, "target_language", "") or "")
    name = _LANGUAGE_NAMES.get(code.lower(), subject.lower())
    return {
        "subject": subject,
        "target_language": name,
        "code": code,
        "rule": f"Every learner-facing string in this lesson is written in "
                f"{name}. No English anywhere on a slide.",
    }


def get_language_resources(subject: str, item_id: str) -> dict:
    """Return the curriculum's own content for a language lesson.

    Args:
      subject: Subject id, e.g. "german".
      item_id: The lesson id.

    Returns:
      The lesson's title, focus, topics and objectives as authored. This is the
      source material; anything written must serve these rather than replace them.
    """
    item = repository.find_item(subject, item_id)
    if item is None:
        return {"error": f"No item {item_id!r} in {subject!r}."}
    return {"item_id": item.id, "title": item.title, "focus": item.focus,
            "objectives": item.objectives, "chapter": item.parent_title}


def get_stem_resources(subject: str, item_id: str) -> dict:
    """Return the curriculum's own content for a STEM lesson.

    Args:
      subject: Subject id, e.g. "mathematics".
      item_id: The lesson or unit id.

    Returns:
      Title, learning outcomes and the unit it belongs to. Granularity "unit"
      means no lesson is authored beneath it yet.
    """
    item = repository.find_item(subject, item_id)
    if item is None:
        return {"error": f"No item {item_id!r} in {subject!r}."}
    return {"item_id": item.id, "title": item.title, "granularity": item.granularity,
            "objectives": item.objectives, "unit": item.parent_title}


def verify_calculation(expression: str, claimed_answer: str) -> dict:
    """Check arithmetic independently of whatever produced it.

    Args:
      expression: The arithmetic in machine-readable form, e.g. "3/4 + 1/6".
      claimed_answer: The answer to check, e.g. "11/12".

    Returns:
      A verdict of "correct", "incorrect" or "unverifiable", with the value this
      tool computed. Evaluated in exact fractions by Python, never by a model —
      so a wrong answer is caught even when it was written confidently.
      "unverifiable" means the expression is outside what can be checked exactly;
      it does NOT mean correct.
    """
    return _check(expression, claimed_answer)


def solve_problem(expression: str) -> dict:
    """Compute the value of an arithmetic expression exactly.

    Args:
      expression: The arithmetic to evaluate, e.g. "7 * (3 + 4)".

    Returns:
      The computed value, or why it could not be computed. Use this to obtain an
      answer rather than calculating one yourself.
    """
    result = _check(expression, "0")
    if result["verdict"] == "unverifiable":
        return {"expression": expression, "solved": False, "reason": result["reason"]}
    return {"expression": expression, "solved": True, "value": result["computed"]}
