"""The live lesson endpoint: one turn of one class, start to finish.

No model is called and no network is touched. What is under test is the order
of events around the turn — presence and the clock before the tutor, the marks
onto the paper before the reply goes back — because that order is the whole
contract and it is the part a model cannot be relied upon to keep.
"""

from __future__ import annotations

import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest

# server.py sits beside `src/`, not inside the package: it is the deployable,
# not part of the library.
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import server  # noqa: E402
from zanoba_agent.live.publish import MarksNotAccepted, NoPaper  # noqa: E402

# Relative to the wall clock, because the state machine reads the wall clock:
# a fixed start date turns every test into "the hour is long over" the day after
# it was written.
def _start(minutes_ago: int = 5) -> datetime:
    return datetime.now(timezone.utc) - timedelta(minutes=minutes_ago)

SHEET = {
    "lessonId": "german.a1-1.classroom.l3", "version": 1, "title": "der, die, das",
    "slides": [
        {"id": "s1", "title": "Wortschatz", "blocks": [
            {"kind": "cards", "cols": 3, "items": [
                {"lead": "der Tisch"}, {"lead": "die Tür"}, {"lead": "das Fenster"}]}]},
        {"id": "s2", "title": "Ergänze die Artikel", "blocks": [
            {"kind": "exercise", "skillId": "artikel", "rows": [
                {"prompt": "___ Tisch", "answer": "der"},
                {"prompt": "___ Tür", "answer": "die"}]}]},
    ],
}


def _request(**kw) -> server.TurnRequest:
    base = dict(booking_id="bk1", student_id="stu1", subject="german",
                level_id="a1-1", item_id="", start_time=_start(),
                duration_minutes=60)
    base.update(kw)
    return server.TurnRequest(**base)


@pytest.fixture
def wired(monkeypatch):
    """A tutor that teaches on the paper, with nothing leaving the process."""
    published: list[list[dict]] = []

    monkeypatch.setattr(server, "_lessons", server.LessonRegistry())
    monkeypatch.setattr(server, "fetch_sheet", lambda booking_id, **kw: SHEET)

    def _publish(paper, booking_id, **kw):
        pending = paper.unsent()
        published.append(pending)
        paper.sent(len(pending))
        return len(pending)

    monkeypatch.setattr(server, "publish_marks", _publish)

    async def _teach(lesson, prompt, language="", work=""):
        # Stands in for the model: turn to a page, write on it, say something.
        from zanoba_agent.agents import live_tutor
        live_tutor.show_page("s2")
        live_tutor.write_on_paper("der = masculine")
        return "Let us look at page two.", ["show_page", "write_on_paper"]

    monkeypatch.setattr(server, "_run_turn", _teach)
    return published


# ---- opening the lesson ----------------------------------------------------

async def test_the_first_turn_starts_the_lesson_and_teaches(wired):
    reply = await server.lesson_turn(_request())
    assert reply.started is True
    assert reply.live_state == "TEACHING"
    assert reply.status == "in_progress"
    assert reply.said == "Let us look at page two."
    assert reply.paper_available is True
    assert reply.showing_page == "s2"


async def test_a_second_turn_continues_the_same_lesson(wired):
    await server.lesson_turn(_request())
    reply = await server.lesson_turn(_request(student_said="die Tisch?"))
    assert reply.started is False
    # The marks accumulate on one paper rather than starting again.
    assert reply.marks_made == 2


async def test_the_student_is_heard_before_the_tutor_answers(wired):
    await server.lesson_turn(_request())
    await server.lesson_turn(_request(student_said="die Tisch?"))
    said = [(u["speaker"], u["text"]) for u in
            server._lessons.get("bk1").transcript()]
    assert ("student", "die Tisch?") in said
    assert said[-1][0] == "tutor"


# ---- the marks reach the paper ---------------------------------------------

async def test_what_the_tutor_writes_goes_out_before_the_reply_does(wired):
    reply = await server.lesson_turn(_request())
    # Turning the page is a pointer, the note is a write: both sent, once.
    assert [op["op"] for op in wired[0]] == ["point", "write"]
    assert reply.marks_published == 2


async def test_marks_that_cannot_be_sent_are_kept_not_dropped(monkeypatch, wired):
    def _refuses(paper, booking_id, **kw):
        raise MarksNotAccepted("the web app is down")

    monkeypatch.setattr(server, "publish_marks", _refuses)
    reply = await server.lesson_turn(_request())
    assert reply.marks_published == 0
    assert any("down" in note for note in reply.notes)
    # Still queued, so the next turn carries them.
    assert len(server._lessons.get("bk1").paper.unsent()) == 2


async def test_a_class_with_no_paper_still_happens(monkeypatch, wired):
    def _no_paper(booking_id, **kw):
        raise NoPaper("No worksheet has been published for bk1.")

    monkeypatch.setattr(server, "fetch_sheet", _no_paper)

    async def _talks(lesson, prompt, language="", work=""):
        return "We will work without a sheet today.", []

    monkeypatch.setattr(server, "_run_turn", _talks)

    reply = await server.lesson_turn(_request())
    assert reply.paper_available is False
    assert reply.live_state == "TEACHING"
    assert any("No worksheet" in note for note in reply.notes)


# ---- the clock and the camera win ------------------------------------------

async def test_a_turn_after_the_hour_ends_the_lesson_without_teaching(wired):
    # A lesson whose booked hour is already behind it does not get taught.
    reply = await server.lesson_turn(
        _request(start_time=_start(minutes_ago=90), student_said="hello?"))
    assert reply.lesson_over is True
    assert reply.status == "no_show"
    assert reply.said == ""
    assert reply.marks_made == 0


async def test_the_clock_cannot_be_moved_by_asking_again(wired):
    # The schedule is fixed when the lesson opens. A later turn claiming a
    # different start time changes nothing — otherwise the hour a student paid
    # for would be whatever the last request said it was.
    await server.lesson_turn(_request())
    reply = await server.lesson_turn(
        _request(start_time=_start(minutes_ago=-600), student_said="more time?"))
    assert reply.lesson_over is False
    assert reply.minutes_remaining < 60


async def test_an_empty_room_is_waited_out_rather_than_taught_to(wired):
    await server.lesson_turn(_request())
    reply = await server.lesson_turn(_request(student_present=False))
    assert reply.live_state == "STUDENT_ABSENT"
    assert reply.said == ""
    assert any("away from the camera" in note for note in reply.notes)


async def test_a_student_who_comes_back_carries_on(wired):
    await server.lesson_turn(_request())
    await server.lesson_turn(_request(student_present=False))
    reply = await server.lesson_turn(_request(student_said="sorry, back"))
    assert reply.live_state == "TEACHING"
    assert reply.said == "Let us look at page two."


# ---- reading and closing ---------------------------------------------------

async def test_the_state_of_a_lesson_can_be_read_without_taking_a_turn(wired):
    await server.lesson_turn(_request())
    state = server.lesson_state("bk1")
    assert state["live_state"] == "TEACHING"
    assert state["showing_page"] == "s2"
    assert len(state["transcript"]) == 1


async def test_a_lesson_this_instance_never_taught_is_a_404(wired):
    from fastapi import HTTPException

    with pytest.raises(HTTPException) as raised:
        server.lesson_state("never-heard-of-it")
    assert raised.value.status_code == 404


async def test_leaving_early_closes_the_lesson_and_flushes_the_marks(wired):
    await server.lesson_turn(_request())
    closed = await server.end_lesson("bk1")
    assert closed["status"] == "completed"
    assert closed["marks_made"] == 1
    # Objectives nobody demonstrated are recorded, not quietly dropped.
    assert closed["unfinished_objectives"]


async def test_an_instance_that_never_saw_the_booking_starts_it(wired):
    # Which is what makes the endpoint safe behind a load balancer: a cold
    # instance opens the lesson rather than refusing the turn.
    reply = await server.lesson_turn(_request(booking_id="bk-unknown",
                                              student_said="hello?"))
    assert reply.started is True
    assert reply.live_state == "TEACHING"


# ---- the contract with the web app -----------------------------------------

TURN_ROUTE = (Path(__file__).resolve().parents[3] / "apps" / "web" / "src" / "app"
              / "api" / "lesson" / "[bookingId]" / "turn" / "route.ts")


def _top_level_keys(block: str) -> set[str]:
    """The object's own keys, ignoring the ones nested inside its values.

    A field whose type is itself an object — `showing_material` — puts its
    members in the same text, and they are not fields of the turn. Depth is
    read from the indentation, which is what a formatter guarantees and what a
    brace-counter would have to rediscover.
    """
    import re

    found = re.findall(r"^( +)([a-z_]+):", block, re.MULTILINE)
    if not found:
        return set()
    outermost = min(len(indent) for indent, _ in found)
    return {name for indent, name in found if len(indent) == outermost}


@pytest.mark.skipif(not TURN_ROUTE.exists(), reason="the web app is not checked out here")
def test_the_web_app_sends_exactly_the_fields_a_turn_expects():
    """The two halves are in different languages, so nothing checks this but this.

    A rename on either side of `/lesson/turn` is invisible until a student is
    sitting in a class that will not start. Reading the field names out of the
    route the browser actually calls is the cheapest thing that catches it.
    """
    body = TURN_ROUTE.read_text(encoding="utf-8").split("JSON.stringify({", 1)[1]
    sent = _top_level_keys(body.split("}),", 1)[0])

    expected = set(server.TurnRequest.model_fields)
    required = {name for name, f in server.TurnRequest.model_fields.items()
                if f.is_required()}

    assert required <= sent, f"the web app omits required fields: {required - sent}"
    assert sent <= expected, f"the web app sends fields the agent ignores: {sent - expected}"


@pytest.mark.skipif(not TURN_ROUTE.exists(), reason="the web app is not checked out here")
def test_the_web_app_reads_fields_a_turn_actually_returns():
    shape = TURN_ROUTE.read_text(encoding="utf-8").split("const turn = (await reply.json()) as {", 1)
    read = _top_level_keys(shape[1].split("};", 1)[0])
    assert read, "no fields were found; the route's response type moved"
    assert read <= set(server.TurnResponse.model_fields), (
        f"the web app reads fields the agent never sends: "
        f"{read - set(server.TurnResponse.model_fields)}")


# ---- the tutor speaks once, in its own voice -------------------------------

async def test_speech_is_taken_from_the_tools_not_doubled(monkeypatch, wired):
    """A real run produced this bug, so it has a test.

    The tutor greeted the class through `say`, and then filled its final
    response with an invented student asking about quadratic equations. Taking
    both channels put that in the transcript as something the tutor said.
    """
    async def _speaks_then_rambles(lesson, prompt, language="", work=""):
        from zanoba_agent.agents import live_tutor
        live_tutor.say("Guten Tag! Let us begin.")
        return "text:\n I'm doing quadratic equations in maths.", ["say"]

    monkeypatch.setattr(server, "_run_turn", _speaks_then_rambles)
    reply = await server.lesson_turn(_request())
    assert reply.said == "Guten Tag! Let us begin."
    assert "quadratic" not in reply.said
    assert len(server._lessons.get("bk1").transcript()) == 1


async def test_a_tutor_that_used_no_tool_is_still_heard(monkeypatch, wired):
    async def _only_talks(lesson, prompt, language="", work=""):
        return "Guten Tag!", []

    monkeypatch.setattr(server, "_run_turn", _only_talks)
    reply = await server.lesson_turn(_request())
    assert reply.said == "Guten Tag!"


# ---- a syllabus is teachable the day it is loaded --------------------------

def test_objectives_come_from_the_curriculum_when_nothing_is_prepared():
    """191 French maths lessons were loaded with no pipeline run behind them.

    Every authored lesson carries its own can-do outcomes, so a class can be
    taught against those from the moment the syllabus exists rather than only
    after something has been generated for it.
    """
    objectives = server._objectives_from(
        {}, "mathematics", "fr.sixieme.nombres-entiers-et-decimaux.l3")
    assert [o.statement for o in objectives] == [
        "Je sais comparer deux nombres décimaux.",
        "Je sais ranger une liste de décimaux dans l'ordre croissant ou décroissant.",
        "Je sais encadrer et arrondir un nombre décimal.",
    ]


def test_a_prepared_lesson_still_wins_over_the_curriculum():
    # The prepared objectives were written against this learner's diagnosis;
    # the curriculum's were written for everybody.
    prepared = {"objectives": {"objectives": [
        {"id": "o1", "statement": "I can round a decimal, which you got wrong last week."}]}}
    objectives = server._objectives_from(
        prepared, "mathematics", "fr.sixieme.nombres-entiers-et-decimaux.l3")
    assert len(objectives) == 1
    assert "last week" in objectives[0].statement


def test_an_unknown_item_falls_back_rather_than_failing():
    objectives = server._objectives_from({}, "mathematics", "fr.sixieme.no-such-unit.l9")
    assert [o.objective_id for o in objectives] == ["o1"]


async def test_a_placeholder_reply_is_not_passed_off_as_speech(monkeypatch, wired):
    """A model that puts everything into tool calls sometimes replies "_".

    Read aloud that is a noise, and in the transcript it is a line of nothing.
    """
    async def _grunts(lesson, prompt, language="", work=""):
        return "_", ["write_on_board"]

    monkeypatch.setattr(server, "_run_turn", _grunts)
    reply = await server.lesson_turn(_request())
    assert reply.said == ""


async def test_real_words_are_still_passed_through(monkeypatch, wired):
    async def _speaks(lesson, prompt, language="", work=""):
        return "Ok, regarde.", []

    monkeypatch.setattr(server, "_run_turn", _speaks)
    reply = await server.lesson_turn(_request())
    assert reply.said == "Ok, regarde."


async def test_what_the_student_wrote_is_put_in_front_of_the_tutor(monkeypatch, wired):
    """The tutor is told in words, not handed a picture and trusted to look.

    Given the image alongside its plan, its briefing and eleven tools, the page
    went unlooked-at — twice it answered something else, once it said nothing.
    So the page is read on its own and the result goes into the prompt.
    """
    seen: list[str] = []

    async def _remembers(lesson, prompt, language="", who=""):
        seen.append(prompt)
        return "Tu as écrit 4 milliers.", []

    monkeypatch.setattr(server, "_run_turn", _remembers)
    monkeypatch.setattr(server, "_read_the_page",
                        lambda work: _resolved("4 307 = 4 milliers"))
    reply = await server.lesson_turn(_request(student_work="data:image/png;base64,zzz"))
    assert "4 307 = 4 milliers" in seen[0]
    assert "WRITTEN this on their paper" in seen[0]
    # And it joins the transcript, so the lesson record shows they answered.
    assert any("written on the paper" in u["text"]
               for u in server._lessons.get("bk1").transcript())
    assert reply.said


async def test_a_page_that_cannot_be_read_does_not_cost_the_turn(monkeypatch, wired):
    async def _answers(lesson, prompt, language="", who=""):
        return "Dis-moi ce que tu as trouvé.", []

    monkeypatch.setattr(server, "_run_turn", _answers)
    monkeypatch.setattr(server, "_read_the_page", lambda work: _resolved(""))
    reply = await server.lesson_turn(_request(student_work="data:image/png;base64,zzz"))
    assert reply.said == "Dis-moi ce que tu as trouvé."


def _resolved(value: str):
    async def _done():
        return value
    return _done()


async def test_a_tutor_that_acts_in_silence_is_asked_to_say_what_it_did(monkeypatch, wired):
    """Marking the paper without a word leaves the student waiting to be spoken
    to, with no idea anything happened. It is asked for words rather than having
    words invented for it."""
    prompts: list[str] = []

    async def _silent_then_speaks(lesson, prompt, language="", who=""):
        prompts.append(prompt)
        if len(prompts) == 1:
            return "_", ["write_on_paper"]
        return "J'ai écrit la décomposition sur ta feuille.", []

    monkeypatch.setattr(server, "_run_turn", _silent_then_speaks)
    reply = await server.lesson_turn(_request(student_said="voilà"))
    assert reply.said.startswith("J'ai écrit")
    assert "without saying anything" in prompts[1]


async def test_a_silent_turn_that_did_nothing_is_left_silent(monkeypatch, wired):
    # Nothing happened, so there is nothing to announce.
    async def _mute(lesson, prompt, language="", who=""):
        return "", []

    monkeypatch.setattr(server, "_run_turn", _mute)
    reply = await server.lesson_turn(_request(student_said="voilà"))
    assert reply.said == ""


async def test_an_internal_token_is_not_read_aloud_as_a_word(monkeypatch, wired):
    """`sf_first_turn_done` came back as a whole reply and was spoken at a child."""
    async def _emits_a_token(lesson, prompt, language="", who=""):
        return "sf_first_turn_done", []

    monkeypatch.setattr(server, "_run_turn", _emits_a_token)
    assert (await server.lesson_turn(_request(student_said="bonjour"))).said == ""


async def test_a_real_one_word_answer_still_gets_through(monkeypatch, wired):
    async def _answers(lesson, prompt, language="", who=""):
        return "Exactement !", []

    monkeypatch.setattr(server, "_run_turn", _answers)
    assert (await server.lesson_turn(_request(student_said="der"))).said == "Exactement !"


# ---- who the tutor is meeting ---------------------------------------------

def test_a_first_lesson_is_an_introduction_not_a_syllabus():
    who = server._who_you_are_teaching(_request(student_name="Louna"))
    assert "Louna" in who
    assert "FIRST lesson" in who
    assert "finding out about them" in who


def test_a_returning_student_is_greeted_by_name_and_reminded():
    who = server._who_you_are_teaching(_request(
        student_name="Louna", lessons_so_far=3,
        last_lesson="Comparer et ranger les décimaux, mardi dernier"))
    assert "Louna" in who
    assert "3 time(s) before" in who
    assert "Comparer et ranger les décimaux" in who
    assert "FIRST lesson" not in who


def test_a_student_with_no_name_is_still_teachable():
    who = server._who_you_are_teaching(_request(lessons_so_far=2))
    assert "the student" in who


def test_a_reply_written_in_the_students_voice_is_dropped():
    """It answered its own question as the child: "celine: Je suis en 6ème…"."""
    assert server._own_words("celine: Je suis en 6ème.", "Celine") == ""
    assert server._own_words("Student: I don't know.", "Celine") == ""


def test_an_ordinary_colon_is_left_alone():
    kept = "Regarde : le 3 est à la place des centaines."
    assert server._own_words(kept, "Celine") == kept
    assert server._own_words("Luna: bonjour.", "Celine") == "Luna: bonjour."
