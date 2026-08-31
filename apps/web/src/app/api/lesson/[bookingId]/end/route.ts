import { NextResponse } from "next/server";
import { verifyLessonAccess } from "@/lib/dal";
import { prisma } from "@/lib/prisma";

/**
 * The student has left the call.
 *
 * The clock ends a lesson on its own, so this is not what closes the hour — it
 * is what stops the agent holding a lesson open for turns that will never come,
 * and what flushes any marks still queued onto the paper. Best-effort by
 * design: a student leaving must never be blocked by the agent being slow.
 */
export async function POST(_request: Request, ctx: { params: Promise<{ bookingId: string }> }) {
  const { bookingId } = await ctx.params;
  const access = await verifyLessonAccess();
  if (!access) return NextResponse.json({ error: "Not signed in." }, { status: 401 });

  const booking = await prisma.booking.findFirst({
    where: { id: bookingId, studentId: access.userId },
    select: { id: true },
  });
  if (!booking) return NextResponse.json({ error: "Booking not found." }, { status: 404 });

  const agent = process.env.AGENT_URL;
  if (!agent) return NextResponse.json({ closed: false, reason: "no agent configured" });

  try {
    const reply = await fetch(`${agent.replace(/\/$/, "")}/lesson/${bookingId}/end`, {
      method: "POST",
      signal: AbortSignal.timeout(10_000),
    });
    // A 404 means the agent had already forgotten this lesson, which is the
    // same outcome as closing it.
    return NextResponse.json({ closed: reply.ok || reply.status === 404 });
  } catch {
    return NextResponse.json({ closed: false, reason: "the agent did not answer" });
  }
}
