import { createHmac } from "node:crypto";
import { NextResponse } from "next/server";
import { verifyLessonAccess } from "@/lib/dal";
import { prisma } from "@/lib/prisma";
import { levelsFor } from "@/lib/curriculum";
import { speechLocale } from "@/lib/locales";
import { SUBJECTS } from "@/lib/subjects";
import { lessonIdFor } from "@/lib/worksheet/lessonId";

/**
 * Permission to open one lesson's audio socket.
 *
 * The spoken lesson runs browser-to-agent: putting a Next route in the middle
 * of a bidirectional PCM stream would add a hop to every 20ms of sound and buy
 * nothing. But the agent has no session — the cookie is ours — so this is where
 * the check happens, once, and the agent is handed a signature instead.
 *
 * The ticket names one booking and expires in two minutes. It travels in a
 * websocket URL and therefore lands in logs, which is exactly why it is not a
 * session token. Signed with AGENT_TOKEN, the secret the two already share.
 *
 * The reply also carries the language the class is spoken in, because that is
 * ours to decide and not the agent's: it comes from the subject, then the
 * level's programme, then the student.
 */

const TTL_SECONDS = 120;

export async function POST(_request: Request, ctx: { params: Promise<{ bookingId: string }> }) {
  const { bookingId } = await ctx.params;
  const access = await verifyLessonAccess();
  if (!access) return NextResponse.json({ error: "Not signed in." }, { status: 401 });

  const secret = process.env.AGENT_TOKEN;
  const agent = process.env.AGENT_URL;
  if (!secret || !agent) {
    return NextResponse.json(
      { error: "AGENT_URL and AGENT_TOKEN must both be set for a spoken lesson." },
      { status: 503 },
    );
  }

  const booking = await prisma.booking.findFirst({
    where: { id: bookingId, studentId: access.userId, status: "UPCOMING" },
    select: {
      subject: true, level: true, chapter: true, lesson: true,
      startTime: true, endTime: true,
    },
  });
  if (!booking) return NextResponse.json({ error: "Booking not found." }, { status: 404 });

  // A dot separates the ticket's fields, so an id containing one could shift
  // the boundary. cuid2 ids never do; this refuses rather than assuming.
  if (bookingId.includes(".")) {
    return NextResponse.json({ error: "Unusable booking id." }, { status: 400 });
  }

  const expiry = Math.floor(Date.now() / 1000) + TTL_SECONDS;
  const payload = `${bookingId}.${expiry}`;
  const signature = createHmac("sha256", secret).update(payload).digest("base64url");

  const subject = SUBJECTS.find((s) => s.id === booking.subject);
  const level = levelsFor(booking.subject).find((l) => l.id === booking.level);
  const user = await prisma.user.findUnique({
    where: { id: access.userId }, select: { supportLanguage: true },
  });

  const lessonId = lessonIdFor(booking);
  return NextResponse.json(
    {
      // ws:// for a local agent, wss:// for a deployed one — derived from the
      // agent's own scheme rather than from how this page happens to be served.
      url: `${agent.replace(/^http/, "ws").replace(/\/$/, "")}/lesson/live`,
      ticket: `${payload}.${signature}`,
      hello: {
        booking_id: bookingId,
        student_id: access.userId,
        subject: booking.subject,
        level_id: booking.level ?? "",
        item_id: lessonId ? lessonId.slice(booking.subject.length + 1) : "",
        start_time: booking.startTime.toISOString(),
        duration_minutes: Math.max(
          1,
          Math.round((booking.endTime.getTime() - booking.startTime.getTime()) / 60000),
        ),
        language: speechLocale(subject?.locale, level?.locale, user?.supportLanguage),
      },
    },
    { headers: { "cache-control": "no-store" } },
  );
}
