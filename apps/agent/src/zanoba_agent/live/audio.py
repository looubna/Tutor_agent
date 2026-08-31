"""Configuring the model for a spoken lesson.

The class the browser opens a microphone for is the same lesson the HTTP turn
endpoint teaches — same tools, same paper, same state machine. What changes is
that the model hears and speaks instead of reading and writing, which needs a
different model and a different run configuration.

Two families of live model exist and they differ in exactly the place this
project got burned:

  NATIVE AUDIO      picks the spoken language itself, from what it is saying.
                    It rejects an explicit language code. This is the one to
                    want — a French lesson comes out French because the words
                    are French, with no tag anywhere to set wrongly.
  HALF-CASCADE      speaks through a separate TTS stage and takes
                    `speech_config.language_code`. Set it, or you get French
                    read with an English mouth.

So the language code is set only where it is accepted, and the language is
*also* stated in the instruction, which both families obey and which is the
only signal that cannot be mis-set.
"""

from __future__ import annotations

import os

from google.adk.agents.run_config import RunConfig, StreamingMode
from google.genai import types

# The newest general-purpose live model this project has access to. Overridable
# because the live models are previews and are renamed often.
LIVE_MODEL = os.environ.get("ZANOBA_LIVE_MODEL", "gemini-3.1-flash-live-preview")

# A warm, unhurried voice. Tutors are not newsreaders.
LIVE_VOICE = os.environ.get("ZANOBA_LIVE_VOICE", "Aoede")

# What the Live API speaks and listens in. Not ours to choose: the API fixes
# both, and the browser has to match them exactly or the audio is noise.
INPUT_SAMPLE_RATE = 16_000
OUTPUT_SAMPLE_RATE = 24_000
INPUT_MIME = f"audio/pcm;rate={INPUT_SAMPLE_RATE}"


# The live models that speak through a separate TTS stage and therefore take a
# language code. Everything else is assumed to be native audio — see below for
# why that is the safe default. Substrings, because these ids carry a date
# suffix that changes every few weeks.
HALF_CASCADE = tuple(
    m for m in os.environ.get(
        "ZANOBA_HALF_CASCADE_MODELS", "2.0-flash-live,live-2.5-flash,flash-exp"
    ).split(",") if m.strip()
)


def is_native_audio(model: str) -> bool:
    """Whether this model chooses its own spoken language.

    The id is the only signal available before a session is opened, and an
    unknown model is treated as native audio deliberately. The two mistakes are
    not equal: setting a language code on a model that rejects it fails the
    whole session and the student hears nothing, while omitting one on a model
    that wanted it falls back to the language named in the instruction. Silence
    is the worse failure, so the default avoids it.
    """
    name = model.lower()
    return not any(marker.strip().lower() in name for marker in HALF_CASCADE)


def speech_config(language_tag: str, *, model: str = "", voice: str = "") -> types.SpeechConfig:
    """The voice, and the language where the model accepts one."""
    config = types.SpeechConfig(
        voice_config=types.VoiceConfig(
            prebuilt_voice_config=types.PrebuiltVoiceConfig(
                voice_name=voice or LIVE_VOICE)))
    if language_tag and not is_native_audio(model or LIVE_MODEL):
        config.language_code = language_tag
    return config


def live_run_config(language_tag: str, *, model: str = "",
                    voice: str = "") -> RunConfig:
    """How one spoken lesson runs.

    Both transcriptions are on. They are not a debugging aid: the transcript is
    what the student's browser renders, what is written to `LessonMessage`, and
    what the tutor's own record of the hour is made of. Without them a spoken
    lesson would leave nothing behind but audio nobody replays.
    """
    return RunConfig(
        streaming_mode=StreamingMode.BIDI,
        response_modalities=["AUDIO"],
        speech_config=speech_config(language_tag, model=model, voice=voice),
        input_audio_transcription=types.AudioTranscriptionConfig(),
        output_audio_transcription=types.AudioTranscriptionConfig(),
    )


def language_note(language_tag: str) -> str:
    """The line added to the tutor's instruction naming the spoken language.

    Belt and braces beside `speech_config`, and the half that always applies:
    a native-audio model takes no language code, so this is the only place the
    language of the hour is stated to it at all.
    """
    if not language_tag:
        return ""
    language = {
        "de": "German", "fr": "French", "es": "Spanish", "it": "Italian",
        "en": "English", "ar": "Arabic", "zh": "Mandarin Chinese", "ko": "Korean",
    }.get(language_tag.split("-")[0].lower(), language_tag)
    return (
        f"\n\nTHIS CLASS IS SPOKEN IN {language.upper()}.\n"
        f"Speak {language} throughout, in a {language} accent. The student hears "
        f"you rather than reading you, so say numbers, spellings and worked "
        f"steps the way they are said aloud in {language}, not the way they are "
        f"written.\n"
        "\n"
        "SPEAK IN TURNS, NOT PARAGRAPHS.\n"
        "This is a conversation, not a lecture. Say one thing — a step, a "
        "correction, a question — and stop. Two or three sentences is a turn; "
        "half a minute of talking is a broadcast, and the student cannot get a "
        "word in without talking over you.\n"
        "- Ask your question and then stop. Do not answer it yourself, and do "
        "  not keep talking while you wait.\n"
        "- Break a long explanation into turns and check after each one. If you "
        "  have three steps to give, give the first and ask what comes next.\n"
        "- If the student interrupts you, they have something to say. Stop "
        "  talking and listen; do not finish your sentence first.\n"
        "\n"
        "YOUR VOICE IS YOUR VOICE.\n"
        "You are speaking aloud, so speak: do NOT put what you want to say "
        "through the `say` tool. That tool exists for a lesson taught in text, "
        "where you have no voice; here it swallows your turn and the student "
        "hears nothing.\n"
        "Use `explain` for what it writes on the paper — the worked example — "
        "and say the plain words and the check question aloud yourself."
    )
