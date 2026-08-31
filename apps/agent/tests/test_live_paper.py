"""The lesson paper: what the tutor shows, and what it writes on it.

The paper is the one artefact the student keeps, so these tests are mostly
about two things — that a mark lands on the box the tutor aimed at, and that
what comes out is exactly the JSON the web app already knows how to replay.
"""

from __future__ import annotations

import json
from datetime import datetime, timedelta, timezone

import pytest

from zanoba_agent.agents.live_tutor import (
    LIVE_TUTOR_TOOLS, bind_session, circle_on_paper, explain, fill_in_gap,
    lesson_paper, point_at_paper, session_surfaces, show_page, write_on_paper)
from zanoba_agent.live import state_machine as sm
from zanoba_agent.live.paper import (
    LivePaper, NoSuchPage, PaperNotOpen, gaps_on, targets_on)
from zanoba_agent.schemas.lesson_state import (
    LessonState, ObjectiveProgress, Scheduled)

START = datetime(2026, 8, 30, 10, 0, tzinfo=timezone.utc)

# A three-page paper with one of every shape a mark can land on.
SHEET = {
    "lessonId": "german.a1-1.classroom.l3",
    "version": 2,
    "title": "der, die, das",
    "slides": [
        {
            "id": "s1", "title": "Wortschatz", "tone": "page",
            "blocks": [
                {"kind": "cards", "cols": 3, "items": [
                    {"lead": "der Tisch"}, {"lead": "die Tür"}, {"lead": "das Fenster"}]},
            ],
        },
        {
            "id": "s2", "title": "Ergänze die Artikel", "tone": "page",
            "blocks": [
                {"kind": "exercise", "skillId": "artikel", "rows": [
                    {"prompt": "___ Tisch", "answer": "der"},
                    {"prompt": "___ Tür", "answer": "die"},
                    {"prompt": "___ Fenster", "answer": "das"}]},
                {"kind": "choose", "rows": [
                    {"prompt": "___ Buch", "options": ["der", "das"], "answer": "das"},
                    {"prompt": "___ Lampe", "options": ["die", "das"], "answer": "die"}]},
            ],
        },
        {"id": "s3", "title": "Zusammenfassung", "tone": "page",
         "blocks": [{"kind": "goals", "items": ["Ich kenne die drei Artikel."]}]},
    ],
}


def _state() -> LessonState:
    return LessonState(
        lesson_id="L1", student_id="s1", subject="german", level_id="a1-1",
        scheduled=Scheduled(start_time=START, duration_minutes=60),
        objectives=[ObjectiveProgress(objective_id="o1", statement="I can x.")])


def _teaching() -> LessonState:
    st = _state()
    sm.observe_presence(st, True, False, START + timedelta(minutes=1))
    return sm.start_lesson(st, START + timedelta(minutes=1))


@pytest.fixture
def paper() -> LivePaper:
    return LivePaper(SHEET)


# ---- reading the paper -----------------------------------------------------

def test_gaps_are_numbered_in_reading_order_across_blocks(paper):
    # Three gap-fills then two multiple choices, in the order they are printed.
    # The tutor says "fill gap 3" and the browser must write into the gap the
    # tutor was looking at, so this order is a contract, not a detail.
    assert [g["answer"] for g in gaps_on(SHEET["slides"][1])] == [
        "der", "die", "das", "das", "die"]


def test_circleable_things_are_numbered_in_reading_order(paper):
    assert targets_on(SHEET["slides"][0]) == ["der Tisch", "die Tür", "das Fenster"]
    # An `exercise` offers its numbered prompts, then `choose` its options —
    # blocks in the order they are printed. A maths page is made of these, and
    # without them there was nothing on it for a tutor to point at.
    assert targets_on(SHEET["slides"][1]) == [
        "___ Tisch", "___ Tür", "___ Fenster", "der", "das", "die", "das"]


def test_a_page_arrives_with_its_key_and_its_numbering(paper):
    page = paper.describe_page("s2")
    assert page["title"] == "Ergänze die Artikel"
    assert [g["row"] for g in page["gaps"]] == [0, 1, 2, 3, 4]
    assert page["gaps"][1]["answer"] == "die"
    assert [c["index"] for c in page["circleable"]] == [0, 1, 2, 3, 4, 5, 6]


def test_an_unknown_page_is_refused_rather_than_invented(paper):
    with pytest.raises(NoSuchPage):
        paper.show("s99")


# ---- marking it ------------------------------------------------------------

def test_a_mark_names_a_page_never_a_position(paper):
    paper.show("s2")
    mark = paper.write("der Tisch — masculine")
    assert mark.on.box == "s2"
    # Still no coordinates anywhere — `at` names a numbered thing on the page,
    # not a position on it, which is what makes a mark survive a phone.
    assert set(mark.on.model_dump()) == {"box", "where", "at"}


def test_the_ops_are_exactly_what_the_web_app_parses(paper):
    paper.show("s2")
    paper.write("Learn the article with the word.", where="beside")
    paper.fill(0, "der")
    paper.circle([1], colour="red")
    assert paper.ops() == [
        # Turning to the page is itself a pointer, so the student's view follows.
        {"id": "m1", "op": "point", "on": {"box": "s2", "where": "over", "at": None}},
        {"id": "m2", "op": "write", "on": {"box": "s2", "where": "beside", "at": None},
         "text": "Learn the article with the word.", "style": "hand"},
        {"id": "m3", "op": "fill", "on": {"box": "s2", "where": "over", "at": None},
         "row": 0, "text": "der"},
        {"id": "m4", "op": "circle", "on": {"box": "s2", "where": "over", "at": None},
         "words": [1], "colour": "red"},
    ]


def test_a_gap_that_is_not_on_the_page_is_refused(paper):
    paper.show("s2")
    with pytest.raises(ValueError, match="5 gaps"):
        paper.fill(9, "der")


def test_circling_something_that_is_not_printed_is_refused(paper):
    paper.show("s1")
    with pytest.raises(ValueError, match="3 things to circle"):
        paper.circle([7])


def test_nothing_can_be_marked_before_a_page_is_shown(paper):
    with pytest.raises(PaperNotOpen):
        paper.write("too early")


def test_a_pointer_is_a_gesture_and_is_not_kept(paper):
    paper.show("s1")
    paper.point()
    paper.write("kept")
    assert len(paper.ops()) == 3
    assert [o.id for o in paper.settled()] == ["m3"]


def test_an_erased_mark_leaves_the_paper(paper):
    paper.show("s1")
    wrong = paper.write("die Tisch")
    paper.erase(wrong.id)
    right = paper.write("der Tisch")
    assert [o.id for o in paper.settled()] == [right.id]
    assert paper.marks_made() == 1


def test_marks_are_reported_per_page(paper):
    paper.show("s1")
    paper.write("on the first page")
    paper.show("s2")
    paper.write("on the second")
    assert len(paper.marks_on("s1")) == 1
    assert len(paper.marks_on("s2")) == 1


# ---- the tutor's paper tools -----------------------------------------------

def test_the_tutor_turns_the_page_and_reads_it_in_one_move():
    st = _teaching()
    bind_session(st, {}, {}, paper=SHEET)
    page = show_page("s2")
    assert page["showing"] == "s2"
    assert page["gaps"][0]["answer"] == "der"
    assert lesson_paper()["showing"] == "s2"


def test_marking_the_paper_is_counted_as_teaching():
    st = _teaching()
    bind_session(st, {}, {}, paper=SHEET)
    show_page("s2")
    write_on_paper("der = masculine")
    fill_in_gap(0, "der")
    circle_on_paper([1], colour="red")
    point_at_paper()
    # The pointer is a gesture, so it is not one of the three marks counted.
    assert st.tutor_actions.paper_marks == 3
    _, paper, _, _ = session_surfaces()
    assert paper.marks_made() == 3


def test_a_bad_gap_number_comes_back_as_an_error_not_an_exception():
    st = _teaching()
    bind_session(st, {}, {}, paper=SHEET)
    show_page("s2")
    assert "error" in fill_in_gap(99, "der")


def test_the_tools_say_so_when_no_worksheet_was_published():
    st = _teaching()
    bind_session(st, {}, {})
    assert lesson_paper()["paper_available"] is False
    assert "error" in show_page("s2")
    assert "error" in write_on_paper("anything")


# ---- explaining ------------------------------------------------------------

def test_an_explanation_says_it_shows_it_and_checks_it():
    st = _teaching()
    bind_session(st, {}, {}, paper=SHEET)
    show_page("s2")
    out = explain(
        idea="German nouns carry their article",
        in_plain_words="Every German noun comes with a little word in front of it.",
        worked_example="der Tisch · die Tür · das Fenster",
        check_question="Which one goes in front of Fenster?")
    audio, paper, _, _ = session_surfaces()
    # Said, written on the paper, and asked — all three, in that order.
    assert [u.text for u in audio.transcript()] == [
        "Every German noun comes with a little word in front of it.",
        "Which one goes in front of Fenster?"]
    assert out["shown_on"] == "paper"
    assert [o.text for o in paper.settled()] == ["der Tisch · die Tür · das Fenster"]
    assert st.tutor_actions.explanations_given == 1


def test_an_explanation_with_nowhere_to_write_is_spoken_not_pretended():
    # The example used to go onto an in-memory whiteboard nobody rendered, and
    # the tutor would then say "look at the board". Now it is said out loud and
    # the tutor is told plainly that it was not written down.
    st = _teaching()
    bind_session(st, {}, {})
    out = explain(idea="carrying", in_plain_words="Ten ones make a ten.",
                  worked_example="17 + 5 = 22", check_question="What is 18 + 4?")
    audio, paper, _, _ = session_surfaces()
    assert out["shown_on"] == "nothing — spoken only"
    assert "17 + 5 = 22" in [u.text for u in audio.transcript()]
    assert paper.marks_made() == 0
    assert "show_page" in out["next"]


def test_explaining_is_the_only_way_to_explain():
    # There is no tool that says something clever without also showing it and
    # checking it, and that is deliberate.
    names = {t.__name__ for t in LIVE_TUTOR_TOOLS}
    assert "explain" in names
    assert not {"lecture", "present", "tell"} & names


# ---- getting the marks onto the student's screen ---------------------------

def test_only_unsent_marks_are_sent_and_only_once(paper, monkeypatch):
    from zanoba_agent.live import publish

    sent: list[list[dict]] = []

    class _Response:
        def read(self):
            return b'{"marks": 1}'

        def __enter__(self):
            return self

        def __exit__(self, *exc):
            return False

    def _urlopen(request, timeout=None):
        sent.append(json.loads(request.data)["ops"])
        return _Response()

    monkeypatch.setattr(publish.urllib.request, "urlopen", _urlopen)

    paper.show("s1")
    paper.write("first")
    assert publish.publish_marks(
        paper, "bk1", base_url="https://zanoba.test", token="t") == 2
    paper.write("second")
    assert publish.publish_marks(
        paper, "bk1", base_url="https://zanoba.test", token="t") == 1
    # Nothing new: nothing sent, and no empty request made.
    assert publish.publish_marks(
        paper, "bk1", base_url="https://zanoba.test", token="t") == 0

    assert [[o["id"] for o in batch] for batch in sent] == [["m1", "m2"], ["m3"]]


def test_a_failed_send_keeps_the_marks_for_the_next_one(paper, monkeypatch):
    from zanoba_agent.live import publish

    def _fails(request, timeout=None):
        raise OSError("connection refused")

    monkeypatch.setattr(publish.urllib.request, "urlopen", _fails)
    paper.show("s1")
    paper.write("must not be lost")
    with pytest.raises(publish.MarksNotAccepted):
        publish.publish_marks(paper, "bk1", base_url="https://zanoba.test", token="t")
    # The cursor did not move, so this mark goes out with the next attempt —
    # along with the pointer that turned the page it belongs to.
    assert [o.get("text") for o in paper.unsent()] == [None, "must not be lost"]


def test_marks_are_not_sent_without_somewhere_to_send_them(paper, monkeypatch):
    from zanoba_agent.live import publish

    monkeypatch.delenv("ZANOBA_WEB_URL", raising=False)
    monkeypatch.delenv("AGENT_TOKEN", raising=False)
    paper.show("s1")
    paper.write("nowhere to go")
    with pytest.raises(publish.MarksNotAccepted, match="AGENT_TOKEN"):
        publish.publish_marks(paper, "bk1")


# ---- explaining and writing as one act -------------------------------------

def test_an_explained_step_rings_what_it_is_about():
    """An explanation that points at nothing is talking into the air.

    The words are said while the thing they are about is ringed in blue, so the
    student's eye is on the right part of the page.
    """
    from zanoba_agent.agents.live_tutor import explain_on_paper, turn_beats

    st = _teaching()
    bind_session(st, {}, {}, paper=SHEET)
    show_page("s1")
    out = explain_on_paper(say="Regarde ce mot.", write="der = masculin", highlight=0)

    assert out["highlighted"] == 0
    _, paper, _, _ = session_surfaces()
    rings = [o for o in paper.settled() if o.op == "circle"]
    assert rings and rings[0].words == [0] and rings[0].colour == "blue"
    # The first beat is the page turn; the spoken one follows it.
    spoken = [b for b in turn_beats() if "say" in b]
    assert spoken[0]["say"] == "Regarde ce mot."


def test_an_answer_goes_in_its_blank_not_at_the_foot_of_the_page():
    from zanoba_agent.agents.live_tutor import explain_on_paper

    st = _teaching()
    bind_session(st, {}, {}, paper=SHEET)
    show_page("s2")
    out = explain_on_paper(say="Donc ici, c'est « der ».", write="der", gap=0)

    assert out["filled_gap"] == 0
    _, paper, _, _ = session_surfaces()
    fills = [o for o in paper.settled() if o.op == "fill"]
    assert fills and fills[0].row == 0 and fills[0].text == "der"


def test_a_step_with_nothing_to_point_at_still_works():
    from zanoba_agent.agents.live_tutor import explain_on_paper

    st = _teaching()
    bind_session(st, {}, {}, paper=SHEET)
    show_page("s1")
    out = explain_on_paper(say="Reprenons depuis le début.", write="3 genres")
    assert out["highlighted"] is None and out["filled_gap"] is None
    _, paper, _, _ = session_surfaces()
    assert [o.op for o in paper.settled()] == ["write"]
