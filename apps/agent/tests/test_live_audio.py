"""The spoken lesson: tickets, and how the model is configured to speak.

The audio itself is not tested here — that needs a microphone and a live model.
What is tested is everything that decides whether the audio comes out right:
who may open the socket, and which language the tutor speaks.
"""

from __future__ import annotations

import time

import pytest

from zanoba_agent.live import tickets
from zanoba_agent.live.audio import (
    INPUT_MIME, INPUT_SAMPLE_RATE, OUTPUT_SAMPLE_RATE, is_native_audio,
    language_note, live_run_config, speech_config)

SECRET = "shared-with-the-web-app"


# ---- who may open the socket ----------------------------------------------

def test_a_ticket_names_the_lesson_it_was_minted_for():
    assert tickets.verify(tickets.mint("bk1", SECRET), SECRET) == "bk1"


def test_a_ticket_signed_with_another_secret_is_refused():
    with pytest.raises(tickets.BadTicket, match="signature"):
        tickets.verify(tickets.mint("bk1", "someone-elses-secret"), SECRET)


def test_a_ticket_cannot_be_edited_to_name_another_lesson():
    ticket = tickets.mint("bk1", SECRET)
    forged = ticket.replace("bk1", "bk2", 1)
    with pytest.raises(tickets.BadTicket, match="signature"):
        tickets.verify(forged, SECRET)


def test_a_ticket_cannot_be_edited_to_last_longer():
    booking, expiry, signature = tickets.mint("bk1", SECRET).split(".")
    later = f"{booking}.{int(expiry) + 86_400}.{signature}"
    with pytest.raises(tickets.BadTicket, match="signature"):
        tickets.verify(later, SECRET)


def test_an_expired_ticket_is_refused():
    old = tickets.mint("bk1", SECRET, now=time.time() - 3600)
    with pytest.raises(tickets.BadTicket, match="expired"):
        tickets.verify(old, SECRET)


def test_a_ticket_is_short_lived_by_default():
    # It travels in a websocket URL, so it lands in logs. Two minutes is what
    # makes that not matter.
    assert tickets.TTL_SECONDS <= 300


def test_nothing_is_signed_or_verified_without_a_secret():
    # Fails closed, like the marks endpoint: an unset AGENT_TOKEN means nobody
    # may open a lesson, not that anybody may.
    with pytest.raises(tickets.BadTicket):
        tickets.mint("bk1", "")
    with pytest.raises(tickets.BadTicket):
        tickets.verify(tickets.mint("bk1", SECRET), "")


def test_a_booking_id_cannot_smuggle_a_field_separator():
    with pytest.raises(tickets.BadTicket, match="dot"):
        tickets.mint("bk1.9999999999", SECRET)


def test_rubbish_is_refused_rather_than_crashing():
    for bad in ["", "nonsense", "a.b", "a.b.c.d"]:
        with pytest.raises(tickets.BadTicket):
            tickets.verify(bad, SECRET)


# ---- speaking the right language -------------------------------------------

def test_a_native_audio_model_is_given_no_language_code():
    # It rejects one, and it picks the language from what it is saying — which
    # is the whole reason this route is better than a tag set by hand.
    config = speech_config("fr-FR", model="gemini-3.1-flash-live-preview")
    assert config.language_code is None
    assert config.voice_config.prebuilt_voice_config.voice_name


def test_a_half_cascade_model_is_told_the_language():
    # This is the family where a missing code produces French read with an
    # English mouth.
    assert speech_config("fr-FR", model="gemini-2.0-flash-exp").language_code == "fr-FR"


def test_an_unknown_model_is_treated_as_native_audio():
    # The conservative way round: omitting a code leans on the instruction,
    # while setting one a model rejects fails the whole session.
    assert is_native_audio("some-future-live-model") is True
    assert speech_config("fr-FR", model="some-future-live-model").language_code is None


def test_the_language_is_named_in_the_instruction_whatever_the_model():
    # The only signal both families obey, and the only one a native-audio model
    # gets at all.
    assert "FRENCH" in language_note("fr-FR")
    assert "GERMAN" in language_note("de-DE")
    assert "KOREAN" in language_note("ko-KR")
    assert language_note("") == ""


def test_an_unrecognised_tag_is_passed_through_rather_than_guessed():
    assert "CY-GB" in language_note("cy-GB")


# ---- the run configuration -------------------------------------------------

def test_a_spoken_lesson_runs_bidirectional_audio_with_both_transcripts():
    config = live_run_config("fr-FR")
    assert config.streaming_mode.value == "bidi"
    assert [m.value for m in config.response_modalities] == ["AUDIO"]
    # Both transcriptions on: the transcript is what the browser renders, what
    # is written to LessonMessage, and what the lesson record is made of.
    assert config.input_audio_transcription is not None
    assert config.output_audio_transcription is not None


def test_the_audio_formats_are_the_ones_the_live_api_fixes():
    # Not ours to choose. The browser has to match these exactly or the audio
    # is noise, so they are stated once here and imported by the client.
    assert (INPUT_SAMPLE_RATE, OUTPUT_SAMPLE_RATE) == (16_000, 24_000)
    assert INPUT_MIME == "audio/pcm;rate=16000"


def test_a_spoken_lesson_is_told_to_take_turns():
    """A tutor that talks for half a minute cannot be answered.

    The student speaks over it, the browser is still holding the rest of the
    monologue, and the reply to the new question queues up behind it — which
    from the student's side looks exactly like the tutor ignoring them.
    """
    note = language_note("fr-FR")
    assert "TURNS, NOT PARAGRAPHS" in note
    assert "stop" in note.lower()


def test_a_spoken_tutor_is_told_not_to_route_its_voice_through_a_tool():
    """`say` is for a lesson taught in text.

    In a spoken lesson the model has a voice, and putting the words through a
    tool instead produced a turn with no audio in it at all — the tutor
    answered into nowhere and the student heard silence.
    """
    note = language_note("fr-FR")
    assert "do NOT put what you want to say" in note
    assert "`say` tool" in note


def test_the_spoken_instruction_only_names_tools_the_spoken_tutor_has():
    """It was given the text tutor's instruction, which commands three tools the
    spoken tutor does not have. The model spent its turn calling for them and
    ended without saying anything at all."""
    from zanoba_agent.agents.live_tutor import (
        LIVE_TUTOR_TOOLS, SPOKEN_INSTRUCTION, SPOKEN_TUTOR_TOOLS)

    has = {t.__name__ for t in SPOKEN_TUTOR_TOOLS}
    missing = {t.__name__ for t in LIVE_TUTOR_TOOLS} - has
    # Only the underscored names are checked. `say` and `explain` are ordinary
    # English words as well as tool names, and the instruction uses them as
    # words — "say what you want to say" is the opposite of commanding a tool.
    named = {name for name in missing if "_" in name and name in SPOKEN_INSTRUCTION}
    assert named == set(), f"instruction commands tools it does not have: {named}"
    # And it still names the ones it does have, or they would never be used.
    assert {"show_page", "write_on_board", "evaluate_student_answer"} <= {
        n for n in has if n in SPOKEN_INSTRUCTION}
