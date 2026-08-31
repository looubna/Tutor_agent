import { NextResponse } from "next/server";

import { verifySession } from "@/lib/dal";

/**
 * A short-lived ticket for one Simli session.
 *
 * Simli renders a face that lip-syncs to audio you send it, which is the only
 * part of a spoken lesson this app does not already have: Gemini does the
 * teaching and the talking, and the browser streams its voice straight through.
 *
 * The API key is minted into a session token here rather than in the browser.
 * The SDK will happily do this client-side — `generateSimliSessionToken` takes
 * an `apiKey` — and that would put a key with a billing account behind it into
 * every page. It sits behind the same `verifySession` gate as every other
 * lesson route, so a session is only ever minted for somebody with a class.
 */
const SIMLI_API_URL = "https://api.simli.ai";

/** An hour, which is a lesson, rather than the ten minutes a demo needs. */
const SESSION_SECONDS = 3600;
/** How long she may sit silent before the session is reaped. */
const IDLE_SECONDS = 600;

export async function POST() {
  await verifySession();

  const apiKey = process.env.SIMLI_API_KEY;
  const faceId = process.env.SIMLI_FACE_ID;

  if (!apiKey || !faceId) {
    return NextResponse.json(
      {
        error:
          "SIMLI_API_KEY and SIMLI_FACE_ID must both be set. The face id is a " +
          "UUID — one of Simli's preset faces, or one of your own created from " +
          "a photograph at app.simli.com.",
      },
      { status: 500 },
    );
  }

  const res = await fetch(`${SIMLI_API_URL}/compose/token`, {
    method: "POST",
    headers: { "x-simli-api-key": apiKey, "Content-Type": "application/json" },
    body: JSON.stringify({
      faceId,
      // No `apiVersion`. The spec pins it to "v2" and the SDK's own request
      // type omits it entirely — and pinning it stops a face built through the
      // legacy generator (`simli_version: 1`, which is the only generator the
      // free plan allows) from ever connecting: the token mints, the session
      // never starts, and nothing says why.
      // She keeps breathing and blinking between sentences rather than freezing
      // on the last frame of the last word.
      handleSilence: true,
      maxSessionLength: SESSION_SECONDS,
      maxIdleTime: IDLE_SECONDS,
      audioInputFormat: "pcm16",
      // Which renderer drives the face. Undocumented in the REST spec but named
      // in the SDK's own request type, and both values are accepted: `fasttalk`
      // is the low-latency one, `artalk` the more animated. A face built from a
      // single still has only so much to work with either way — the head does
      // not turn because there is no footage of it turning — but this is the
      // one lever that costs nothing.
      model: process.env.SIMLI_MODEL ?? "artalk",
    }),
  });

  const body = await res.json().catch(() => null);
  const token = body?.session_token;

  // A refused request still answers with a `session_token` — the string "FAIL
  // TOKEN" — so the status is what decides, not the presence of the field.
  if (!res.ok || !token || token === "FAIL TOKEN") {
    return NextResponse.json(
      { error: `Simli refused the session (${res.status}): ${body?.detail ?? "no detail"}` },
      { status: 502 },
    );
  }

  return NextResponse.json({ token }, { headers: { "cache-control": "no-store" } });
}
