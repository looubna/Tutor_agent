"""Short-lived tickets that let one browser open one lesson's audio socket.

The audio session runs browser-to-agent, because putting a Next.js route in the
middle of a bidirectional PCM stream would add a hop to every 20ms of sound for
no benefit. But that means the agent is answering a socket the browser opened
directly, and the agent has no idea who is signed in — sessions are the web
app's business and it holds the cookie.

So the web app vouches. It checks the session the way it does everywhere else,
then mints a ticket naming one booking and expiring in a minute or two; the
agent verifies the signature and the expiry and nothing else. The signing key is
`AGENT_TOKEN`, already shared between the two for the paper endpoints.

A ticket is `<booking-id>.<expiry>.<signature>`. It is not secret in transit —
it goes in a websocket URL, which lands in logs — which is exactly why it names
one booking and lives for two minutes rather than being a session token.
"""

from __future__ import annotations

import base64
import hashlib
import hmac
import time

# Long enough to cover a slow page load and a websocket handshake, short enough
# that a ticket in a log file is worthless by the time anyone reads it.
TTL_SECONDS = 120


class BadTicket(ValueError):
    """The ticket was forged, malformed, expired, or for another lesson."""


def _sign(payload: str, secret: str) -> str:
    digest = hmac.new(secret.encode(), payload.encode(), hashlib.sha256).digest()
    return base64.urlsafe_b64encode(digest).decode().rstrip("=")


def mint(booking_id: str, secret: str, *, ttl: int = TTL_SECONDS,
         now: float | None = None) -> str:
    """A ticket for one booking, good for `ttl` seconds."""
    if not secret:
        raise BadTicket("No signing secret; AGENT_TOKEN is not set.")
    if "." in booking_id:
        # The separator is a dot, so a booking id containing one would let a
        # caller shift the boundary between the fields.
        raise BadTicket("A booking id may not contain a dot.")
    expiry = int((now if now is not None else time.time()) + ttl)
    payload = f"{booking_id}.{expiry}"
    return f"{payload}.{_sign(payload, secret)}"


def verify(ticket: str, secret: str, *, now: float | None = None) -> str:
    """Return the booking the ticket is for, or raise.

    Order matters: the signature is checked before the expiry, so a forged
    ticket cannot learn anything from which complaint it gets back.
    """
    if not secret:
        raise BadTicket("No signing secret; AGENT_TOKEN is not set.")
    try:
        booking_id, expiry, signature = ticket.split(".")
    except (ValueError, AttributeError) as exc:
        raise BadTicket("Malformed ticket.") from exc

    expected = _sign(f"{booking_id}.{expiry}", secret)
    if not hmac.compare_digest(signature, expected):
        raise BadTicket("Bad signature.")

    try:
        deadline = int(expiry)
    except ValueError as exc:
        raise BadTicket("Malformed expiry.") from exc
    if (now if now is not None else time.time()) > deadline:
        raise BadTicket("Ticket expired.")

    return booking_id
