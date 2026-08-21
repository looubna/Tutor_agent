import { NextResponse } from "next/server";
import { verifySession } from "@/lib/dal";

const LIVEAVATAR_API_URL = "https://api.liveavatar.com";

export async function POST() {
  await verifySession();

  const apiKey = process.env.HEYGEN_API_KEY;
  const avatarId = process.env.HEYGEN_AVATAR_ID;

  if (!apiKey || !avatarId) {
    return NextResponse.json(
      { error: "HEYGEN_API_KEY / HEYGEN_AVATAR_ID are not configured on the server." },
      { status: 500 }
    );
  }

  const res = await fetch(`${LIVEAVATAR_API_URL}/v1/sessions/token`, {
    method: "POST",
    headers: {
      "X-API-KEY": apiKey,
      "Content-Type": "application/json",
    },
    body: JSON.stringify({ avatar_id: avatarId }),
  });

  if (!res.ok) {
    const text = await res.text();
    return NextResponse.json(
      { error: `HeyGen token request failed (${res.status}): ${text}` },
      { status: 502 }
    );
  }

  const json = await res.json();
  const token = json?.data?.token ?? json?.token;

  if (!token) {
    return NextResponse.json({ error: "HeyGen response did not include a token." }, { status: 502 });
  }

  return NextResponse.json({ token });
}
