"""Render one clip of the tutor speaking, and drop it where the web app serves it.

Marieke is a HeyGen `talking_photo` — a video-generation avatar. She cannot be
streamed live: LiveAvatar keeps a separate catalogue keyed by UUID, this account
has none in it, and every streaming endpoint on v1, v2 and v3 answers 404. So the
tutor's face is pre-rendered here, once per line, and the call screen plays the
clip.

For a scripted demo that is the better trade anyway — she says exactly what she
is meant to, gestures cleanly, and nothing can drop mid-take.

    python scripts/make_tutor_clip.py greeting "Hi! I'm Luna. Ready for maths?"
    python scripts/make_tutor_clip.py goodbye  "Great work today. See you soon!"

Costs one HeyGen credit per render. `--check` prints the account's remaining
balance and exits.
"""
from __future__ import annotations

import os
import sys
import time
from pathlib import Path

import httpx

API = "https://api.heygen.com"

# "Marieke Warm Autumn 3" — the avatar chosen for the tutor. Her id is a
# talking_photo id, which is why it is 32 hex characters rather than the UUID a
# LiveAvatar streaming avatar would carry.
AVATAR_ID = os.environ.get("HEYGEN_TALKING_PHOTO_ID",
                           "3f15891e021d4c2b989da9e2d50d243e")
VOICE_ID = os.environ.get("HEYGEN_VOICE_ID", "330290724a1b470fb63153f34d4c0183")

# Where the web app looks for them. `CallScreen` plays /marketing/tutor-<name>.mp4
# and falls back to the still portrait when the file is not there.
OUT_DIR = Path(__file__).resolve().parents[2] / "web" / "public" / "marketing"


def key() -> str:
    value = os.environ.get("HEYGEN_API_KEY", "").strip()
    if not value:
        raise SystemExit("HEYGEN_API_KEY is not set (it lives in apps/web/.env)")
    return value


def remaining() -> int:
    with httpx.Client(timeout=30) as client:
        r = client.get(f"{API}/v2/user/remaining_quota", headers={"X-Api-Key": key()})
        r.raise_for_status()
        return int(r.json()["data"]["remaining_quota"])


def render(text: str) -> str:
    """Ask for the video and return its id."""
    body = {
        "video_inputs": [{
            "character": {"type": "talking_photo", "talking_photo_id": AVATAR_ID},
            "voice": {"type": "text", "input_text": text, "voice_id": VOICE_ID},
        }],
        # 16:9, which is the shape of the tile it plays in.
        "dimension": {"width": 1280, "height": 720},
    }
    with httpx.Client(timeout=60) as client:
        r = client.post(f"{API}/v2/video/generate",
                        headers={"X-Api-Key": key(), "Content-Type": "application/json"},
                        json=body)
        if r.status_code != 200:
            raise SystemExit(f"generate failed {r.status_code}: {r.text[:400]}")
        data = r.json()
        if data.get("error"):
            raise SystemExit(f"generate failed: {data['error']}")
        return data["data"]["video_id"]


def wait_for(video_id: str, timeout_s: int = 600) -> str:
    """Poll until the render finishes, and return the download URL."""
    deadline = time.time() + timeout_s
    with httpx.Client(timeout=30) as client:
        while time.time() < deadline:
            r = client.get(f"{API}/v1/video_status.get",
                           params={"video_id": video_id},
                           headers={"X-Api-Key": key()})
            data = r.json().get("data") or {}
            status = data.get("status")
            if status == "completed":
                return data["video_url"]
            if status == "failed":
                raise SystemExit(f"render failed: {data.get('error')}")
            print(f"  {status}…", flush=True)
            time.sleep(10)
    raise SystemExit("timed out waiting for the render")


def main(name: str = "greeting", *words: str) -> None:
    if name == "--check":
        print(f"remaining HeyGen credits: {remaining()}")
        return
    text = " ".join(words).strip()
    if not text:
        raise SystemExit('nothing to say — pass the line, e.g. ... greeting "Hi!"')

    print(f"credits before: {remaining()}")
    video_id = render(text)
    print(f"video_id: {video_id}")
    url = wait_for(video_id)

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    target = OUT_DIR / f"tutor-{name}.mp4"
    with httpx.Client(timeout=180, follow_redirects=True) as client:
        target.write_bytes(client.get(url).content)
    print(f"saved: {target}  ({target.stat().st_size // 1024} KB)")
    print(f"served at: /marketing/{target.name}")


if __name__ == "__main__":
    main(*(sys.argv[1:] or []))
