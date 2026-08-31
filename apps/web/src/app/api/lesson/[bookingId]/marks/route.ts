import { NextResponse } from "next/server";
import type { NextRequest } from "next/server";
import { verifyLessonAccess } from "@/lib/dal";
import { prisma } from "@/lib/prisma";
import { lessonIdFor } from "@/lib/worksheet/lessonId";
import { addOps, paperFor, livePaper } from "@/lib/worksheet/store";
import { marksMade } from "@/lib/worksheet/ops";

/**
 * The tutor's hand, going onto the paper during the class.
 *
 *   GET  …/marks   what has been written so far
 *   POST …/marks   the tutor writes more
 *
 * The two callers are different and so are the two checks. GET is the student's
 * own browser watching their own paper, so it goes through the session. POST is
 * the agent runtime — a different service, not a person with a cookie — so it
 * carries a shared token instead.
 *
 * Ops are appended, never replaced. The list of marks *is* the marked
 * worksheet, so losing the middle of it would lose the middle of the lesson.
 */

async function lessonFor(bookingId: string, userId: string) {
  const booking = await prisma.booking.findFirst({
    where: { id: bookingId, studentId: userId },
    select: { subject: true, level: true, chapter: true, lesson: true },
  });
  return booking ? lessonIdFor(booking) : null;
}

export async function GET(_request: NextRequest, ctx: { params: Promise<{ bookingId: string }> }) {
  const { bookingId } = await ctx.params;
  const access = await verifyLessonAccess();
  if (!access) return NextResponse.json({ error: "Not signed in." }, { status: 401 });

  const lessonId = await lessonFor(bookingId, access.userId);
  if (!lessonId) return NextResponse.json({ error: "Booking not found." }, { status: 404 });

  await paperFor(bookingId, access.userId, lessonId);
  const live = await livePaper(bookingId);
  if (!live) {
    return NextResponse.json(
      { error: "No worksheet has been published for this lesson yet." },
      { status: 404 },
    );
  }

  // `showing` is the page the last mark landed on, which is the page the tutor
  // is working on. Derived rather than stored: one fewer thing to keep in sync,
  // and a mark is the only evidence of attention we actually have.
  const showing = [...live.ops].reverse().find((op) => "on" in op)?.on.box ?? null;
  return NextResponse.json(
    { ops: live.ops, marks: marksMade(live.ops), showing },
    { headers: { "cache-control": "no-store" } },
  );
}

export async function POST(request: NextRequest, ctx: { params: Promise<{ bookingId: string }> }) {
  const { bookingId } = await ctx.params;

  // Fails closed. An unset token is a misconfiguration, and the safe reading of
  // "no password is set" on a route that writes to a student's record is that
  // nobody may write, not that anybody may.
  const token = process.env.AGENT_TOKEN;
  if (!token) {
    return NextResponse.json(
      { error: "AGENT_TOKEN is not set on this deployment, so the tutor cannot write." },
      { status: 503 },
    );
  }
  if (request.headers.get("authorization") !== `Bearer ${token}`) {
    return NextResponse.json({ error: "Not the tutor." }, { status: 401 });
  }

  const paper = await prisma.studentLessonDoc.findUnique({ where: { bookingId } });
  if (!paper) {
    return NextResponse.json(
      { error: "This class has no paper yet; the student has not opened it." },
      { status: 404 },
    );
  }

  try {
    const merged = await addOps(bookingId, (await request.json())?.ops);
    return NextResponse.json({ marks: marksMade(merged), total: merged.length });
  } catch (error) {
    // A malformed op is the agent's bug, not the student's problem: say which
    // part failed rather than 500-ing on a Zod message nobody reads.
    return NextResponse.json(
      { error: "These marks were refused.", detail: String(error) },
      { status: 422 },
    );
  }
}
