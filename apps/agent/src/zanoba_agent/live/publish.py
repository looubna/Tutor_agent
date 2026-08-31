"""The paper, travelling between the web app and the agent.

The agent runs as its own service; the paper lives in the web app. So it has to
cross the wire twice. `fetch_sheet` brings the worksheet here at the start of a
class — the tutor's copy, answers included, because a tutor without the key
cannot mark anything. `publish_marks` sends back what the tutor wrote, to
`POST /api/lesson/{booking}/marks`, which appends it to the student's copy and
is what their browser is polling.

Marks are append-only, and sent in order. The endpoint adds what it is given, so a mark
sent twice is drawn twice and a mark skipped is a hole in the middle of the
lesson. The cursor in `LivePaper` only moves after a send actually succeeds.

`urllib` rather than a client library: this is one POST of a small JSON body to
one known URL, and it is not worth a dependency in the deployed image.
"""

from __future__ import annotations

import json
import logging
import os
import urllib.error
import urllib.request

from .paper import LivePaper

_log = logging.getLogger(__name__)

TIMEOUT_SECONDS = 5


class MarksNotAccepted(RuntimeError):
    """The web app refused the marks. The cursor has not moved."""


class NoPaper(RuntimeError):
    """The paper could not be fetched. The lesson runs without one."""


def _endpoint(booking_id: str, leaf: str, base_url: str, token: str) -> tuple[str, str]:
    root = (base_url or os.environ.get("ZANOBA_WEB_URL", "")).rstrip("/")
    secret = token or os.environ.get("AGENT_TOKEN", "")
    if not root or not secret:
        raise MarksNotAccepted(
            "ZANOBA_WEB_URL and AGENT_TOKEN must both be set for the tutor to "
            "reach a student's paper."
        )
    return f"{root}/api/lesson/{booking_id}/{leaf}", secret


def fetch_sheet(
    booking_id: str,
    *,
    base_url: str = "",
    token: str = "",
    timeout: float = TIMEOUT_SECONDS,
) -> dict:
    """The worksheet for one booking, as the tutor needs to see it.

    This is the copy WITH the answers on it. It never goes near a browser — the
    student's copy is stripped by the web app before it is rendered — and it is
    what makes `show_page` able to hand the tutor a key rather than a guess.

    Raises:
      NoPaper: there is no worksheet for this class, or it could not be reached.
        The caller should teach without one rather than abandon the lesson.
    """
    try:
        url, secret = _endpoint(booking_id, "sheet", base_url, token)
    except MarksNotAccepted as exc:
        raise NoPaper(str(exc)) from exc

    request = urllib.request.Request(
        url, headers={"authorization": f"Bearer {secret}"}, method="GET")
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            body = json.loads(response.read() or b"{}")
    except (urllib.error.URLError, OSError, ValueError) as exc:
        raise NoPaper(f"Could not fetch the paper for {booking_id}: {exc}") from exc

    sheet = body.get("sheet")
    if not isinstance(sheet, dict) or not sheet.get("slides"):
        raise NoPaper(f"No worksheet has been published for {booking_id}.")
    return sheet


def publish_marks(
    paper: LivePaper,
    booking_id: str,
    *,
    base_url: str = "",
    token: str = "",
    timeout: float = TIMEOUT_SECONDS,
) -> int:
    """Send everything the tutor has written since the last send.

    Args:
      paper: The lesson's paper.
      booking_id: Which class's copy to write on.
      base_url: The web app, e.g. "https://zanoba.com". Falls back to
        ZANOBA_WEB_URL.
      token: The shared secret the marks endpoint checks. Falls back to
        AGENT_TOKEN.

    Returns:
      How many marks were sent. Zero when there was nothing to send.

    Raises:
      MarksNotAccepted: the request failed. Nothing is marked as sent, so the
        next call carries these marks again.
    """
    pending = paper.unsent()
    if not pending:
        return 0

    url, secret = _endpoint(booking_id, "marks", base_url, token)

    request = urllib.request.Request(
        url,
        data=json.dumps({"ops": pending}).encode("utf-8"),
        headers={"content-type": "application/json",
                 "authorization": f"Bearer {secret}"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            body = json.loads(response.read() or b"{}")
    except (urllib.error.URLError, OSError, ValueError) as exc:
        raise MarksNotAccepted(f"Could not write on the paper: {exc}") from exc

    paper.sent(len(pending))
    _log.info("wrote %d marks on booking %s (%s on the paper)",
              len(pending), booking_id, body.get("marks"))
    return len(pending)
