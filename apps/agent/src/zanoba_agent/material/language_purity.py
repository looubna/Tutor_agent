"""Is this German lesson actually in German?

The pipeline's first output was a German lesson written in English: "Welcome!
Let's warm up your German spelling skills", "Look at these nine classroom
items", "Match the Articles!". Sixty-seven distinct English function words
across six items. Every published A1 deck it was meant to resemble is in the
target language end to end — the title, the instruction line, the objectives,
the summary, the word list. The learner reads "Ordne zu.", not "Match them up."

This is checked here rather than asked for in a prompt because a prompt asking
for German gets German content with English scaffolding around it, every time,
and the model reports that as compliant. A function-word count does not
negotiate.

The detector looks for *function words* — the, and, your, with, this — because
they are what running English prose is made of and what a content word list
would miss. Every marker is checked against the target language first: "was",
"in", "will", "hat", "die", "man" and "so" are ordinary German words that happen
to be spelled like English ones, and flagging them would make the check useless.

Quoted text is exempt. The reference lesson contains the sentence "Der heißt the
auf Englisch" — the English word is the object of study there, which is the one
place it belongs.
"""

from __future__ import annotations

import re
from typing import Any

# English function words that are NOT also words in the languages we teach.
# Curated by hand against German, French, Spanish and Italian orthography; the
# false-positive cost here is high, so anything ambiguous is left out.
_ENGLISH_FUNCTION_WORDS: set[str] = {
    "the", "and", "your", "yours", "you", "with", "this", "that", "these", "those",
    "there", "their", "they", "them", "from", "for", "are", "were", "been", "being",
    "have", "has", "had", "does", "did", "doesn", "what", "which", "when", "where",
    "who", "whose", "how", "why", "because", "about", "into", "onto", "over",
    "under", "between", "before", "after", "again", "each", "every", "both",
    "some", "any", "many", "much", "more", "most", "other", "another", "same",
    "than", "then", "only", "just", "also", "very", "here", "now", "always",
    "never", "something", "anything", "nothing", "everything", "someone",
    "let", "don", "can", "cannot", "could", "should", "would", "may", "might",
    "must", "shall", "need", "want", "going", "get", "got", "make", "makes",
    "made", "take", "takes", "give", "gives", "put", "come", "comes",
    "it", "its", "his", "her", "hers", "him", "she", "we", "our", "ours", "us",
    "my", "mine", "me", "yes", "no", "not", "but", "or", "if", "of", "to", "at",
    "on", "by", "up", "out", "off", "down", "all", "one", "two", "three",
}

# Words a bilingual German word list legitimately contains are still English, so
# the ambiguous ones above are trimmed per target language rather than globally.
_ALSO_TARGET_WORDS: dict[str, set[str]] = {
    "german": {"was", "in", "will", "hat", "die", "man", "so", "wer", "her", "hier",
               "am", "an", "bin", "war", "rot", "gut", "bad", "art", "list", "form",
               "kind", "hut", "tag", "not", "he", "sie", "wie", "we", "me", "my",
               "if", "of", "to", "at", "on", "by", "up", "out", "off", "all", "one",
               "two", "three", "no", "or"},
    "french": {"on", "or", "car", "son", "sur", "pas", "the", "no", "to", "at", "us",
               "me", "my", "if", "of", "by", "up", "out", "all", "one", "two", "three"},
    "spanish": {"no", "con", "son", "por", "sin", "me", "us", "to", "at", "on", "or",
               "of", "by", "up", "out", "all", "one", "two", "three"},
    "italian": {"no", "con", "non", "per", "come", "me", "us", "to", "at", "on", "or",
                "of", "by", "up", "out", "all", "one", "two", "three", "then", "some"},
}

# Instruction verbs are the tell for English scaffolding wrapped around target
# content, and they are exactly what the reference decks render in German
# ("Ordne zu.", "Lies den Text.", "Ergänze", "Sprich nach."). Worth naming
# separately so the report can say *what kind* of English leaked in.
_ENGLISH_INSTRUCTION_VERBS: set[str] = {
    "match", "complete", "choose", "select", "write", "read", "listen", "speak",
    "answer", "fill", "circle", "underline", "sort", "classify", "rewrite",
    "translate", "repeat", "practise", "practice", "look", "find", "say", "ask",
    "correct", "order", "arrange", "build", "describe", "explain", "discuss",
}

# Content words are the other half. The function-word list catches English
# PROSE, but a matching exercise whose prompts are the bare words "table",
# "chair", "book" contains no function words at all — and that is exactly what
# the first rebuilt lesson did, asking an A1 learner to match English nouns to
# pictures in a German lesson. It passed a purity check scoring 100.
#
# So: the everyday nouns and verbs A1-A2 material is actually made of, in
# English, excluding anything spelled the same in a language we teach. Not a
# dictionary — the vocabulary these lessons keep reaching for.
_ENGLISH_CONTENT_WORDS: set[str] = {
    # classroom
    "table", "chair", "book", "books", "pen", "pencil", "bag", "lamp", "desk",
    "door", "window", "board", "notebook", "eraser", "ruler", "scissors",
    "teacher", "student", "classroom", "lesson", "homework", "question",
    "answer", "word", "words", "sentence", "letter", "page", "picture",
    # people and family
    "man", "woman", "boy", "girl", "child", "children", "friend", "mother",
    "father", "sister", "brother", "family", "parents", "husband", "wife",
    "daughter", "neighbour", "neighbor", "people", "person",
    # home and everyday objects
    "house", "home", "room", "kitchen", "garden", "bed", "phone", "computer",
    "car", "key", "clock", "watch", "money", "shop", "street", "city", "town",
    "school", "office", "station", "hotel", "restaurant", "hospital",
    # food and drink
    "bread", "water", "coffee", "tea", "milk", "apple", "banana", "cheese",
    "breakfast", "lunch", "dinner", "food", "drink",
    # time
    "morning", "evening", "night", "today", "tomorrow", "yesterday", "week",
    "month", "year", "hour", "minute", "monday", "tuesday", "wednesday",
    "thursday", "friday", "saturday", "sunday",
    # very common verbs and adjectives
    "hello", "goodbye", "please", "thanks", "thank", "sorry", "yes",
    "good", "bad", "big", "small", "old", "young", "new", "nice", "happy",
    "eat", "drink", "sleep", "work", "live", "like", "know", "understand",
    "spell", "repeat", "help", "buy", "sell", "open", "close", "start", "stop",
}

_WORD = re.compile(r"[A-Za-zÀ-ÿ']+")

# Text the learner is meant to read as a foreign word: "the" in a gloss, a
# quoted English sentence inside a dialogue about translation.
_QUOTED = re.compile(r"[\"'«»„“”‚‘’(\[]([^\"'«»„“”‚‘’)\]]{1,80})[\"'«»„“”‚‘’)\]]")


def _markers_for(target_language: str) -> tuple[set[str], set[str], set[str]]:
    exempt = _ALSO_TARGET_WORDS.get((target_language or "").strip().lower(), set())
    return (_ENGLISH_FUNCTION_WORDS - exempt,
            _ENGLISH_INSTRUCTION_VERBS - exempt,
            _ENGLISH_CONTENT_WORDS - exempt)


def check_text(text: str, target_language: str = "german",
               allow_quoted: bool = True) -> dict[str, Any]:
    """Report the English hiding in a piece of target-language text.

    Returns the markers found, how dense they are, and a verdict. Density
    matters: one stray word in a forty-word paragraph is a slip, and eight is a
    paragraph that was written in English and had a few German nouns dropped in.
    """
    raw = text or ""
    scanned = _QUOTED.sub(" ", raw) if allow_quoted else raw
    words = [w.lower() for w in _WORD.findall(scanned)]
    functions, verbs, contents = _markers_for(target_language)

    found_function = sorted({w for w in words if w in functions})
    found_verbs = sorted({w for w in words if w in verbs})
    found_content = sorted({w for w in words if w in contents})
    hits = [w for w in words if w in functions or w in verbs or w in contents]
    density = len(hits) / len(words) if words else 0.0

    return {
        "target_language": target_language,
        "word_count": len(words),
        "english_function_words": found_function,
        "english_instruction_verbs": found_verbs,
        "english_content_words": found_content,
        "marker_count": len(hits),
        "density": round(density, 3),
        "is_target_language": not (found_function or found_verbs or found_content),
    }


# One marker is a slip worth reporting; this much of the text being English
# markers means the field was authored in English.
_AUTHORED_IN_ENGLISH_DENSITY = 0.06

# Fields the learner reads on the slide. English here is the visible defect.
LEARNER_FACING_FIELDS = ("title", "content", "instruction", "prompt", "answer",
                         "statement", "instructions")


def check_package(package: dict, target_language: str = "german") -> dict[str, Any]:
    """Check every learner-facing string in a material package.

    Tutor-only fields are exempt by design — `pedagogical_purpose` and
    `explanation` are notes to the teacher, not slide text, and forcing those
    into German would make the rationale unreadable to the person reviewing it.
    `answer_key` is exempt for the same reason, except for the answers
    themselves, which are target-language and are checked with the exercises.
    """
    violations: list[dict] = []

    def scan(where: str, field: str, text: str, severity_floor: str = "high") -> None:
        if not (text or "").strip():
            return
        result = check_text(text, target_language)
        if result["is_target_language"]:
            return
        severity = severity_floor
        if result["density"] < _AUTHORED_IN_ENGLISH_DENSITY and result["marker_count"] <= 1:
            severity = "medium"
        markers = (result["english_function_words"]
                   + result["english_instruction_verbs"]
                   + result["english_content_words"])
        # A learner-facing prompt made ENTIRELY of English words is not a slip,
        # whatever its length: "table" as the prompt of a German matching task
        # is the defect, and it carries exactly one marker.
        if result["english_content_words"] and len(markers) >= result["word_count"]:
            severity = "high"
        violations.append({
            "item_id": where, "field": field, "severity": severity,
            "markers": markers, "density": result["density"],
            "detail": f"{field} is not in {target_language}: found "
                      f"{', '.join(markers[:6])}",
        })

    for item in package.get("items", []) or []:
        where = item.get("id", "?")
        for field in ("title", "content", "instruction"):
            scan(where, field, str(item.get(field, "") or ""))
        for exercise in item.get("exercises") or []:
            eid = f"{where}/{exercise.get('id', '?')}"
            scan(eid, "instructions", str(exercise.get("instructions", "") or ""))
            scan(eid, "prompt", str(exercise.get("prompt", "") or ""))
            # An answer is target-language by definition, but it is often one
            # word, so a single marker there is not evidence of English prose.
            answer = str(exercise.get("answer", "") or "")
            if len(_WORD.findall(answer)) >= 4:
                scan(eid, "answer", answer, severity_floor="medium")

    return {
        "target_language": target_language,
        "clean": not violations,
        "violation_count": len(violations),
        "blocking_count": sum(1 for v in violations if v["severity"] == "high"),
        "violations": violations,
    }
