import { NextResponse } from "next/server";
import type { NextRequest } from "next/server";
import { prisma } from "@/lib/prisma";
import { lessonIdFor } from "@/lib/worksheet/lessonId";
import { tutorSheet } from "@/lib/worksheet/store";

/**
 * The paper, as the tutor needs it — answers and all.
 *
 * Only the agent may read this, and only with the shared token. There is no
 * session path onto it deliberately: a student holding a cookie must never be
 * able to reach the key, and the way to guarantee that is for this route not to
 * know what a session is.
 */
export async function GET(request: NextRequest, ctx: { params: Promise<{ bookingId: string }> }) {
  const { bookingId } = await ctx.params;

  const token = process.env.AGENT_TOKEN;
  if (!token) {
    return NextResponse.json(
      { error: "AGENT_TOKEN is not set on this deployment." },
      { status: 503 },
    );
  }
  if (request.headers.get("authorization") !== `Bearer ${token}`) {
    return NextResponse.json({ error: "Not the tutor." }, { status: 401 });
  }

  const booking = await prisma.booking.findUnique({
    where: { id: bookingId },
    select: { studentId: true, subject: true, level: true, chapter: true, lesson: true },
  });
  if (!booking) return NextResponse.json({ error: "Booking not found." }, { status: 404 });

  const lessonId = lessonIdFor(booking);
  if (!lessonId) {
    return NextResponse.json({ error: "This class follows no chapter." }, { status: 404 });
  }

  const tutors = await tutorSheet(bookingId, booking.studentId, lessonId);
  if (!tutors) {
    return NextResponse.json(
      { error: "No worksheet has been published for this lesson yet." },
      { status: 404 },
    );
  }

  return NextResponse.json(
    { lessonId, version: tutors.version, sheet: tutors.sheet },
    { headers: { "cache-control": "no-store" } },
  );
}
