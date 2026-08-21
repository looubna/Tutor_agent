import { NextResponse } from "next/server";
import type { NextRequest } from "next/server";
import { verifySession } from "@/lib/dal";
import { prisma } from "@/lib/prisma";

const AGENT_SERVICE_URL = process.env.AGENT_SERVICE_URL ?? "http://localhost:8000";
const HISTORY_LIMIT = 20;

export async function POST(request: NextRequest, ctx: { params: Promise<{ bookingId: string }> }) {
  const { userId } = await verifySession();
  const { bookingId } = await ctx.params;

  const booking = await prisma.booking.findFirst({
    where: { id: bookingId, studentId: userId },
  });
  if (!booking) {
    return NextResponse.json({ error: "Booking not found." }, { status: 404 });
  }

  const { text } = await request.json();
  if (typeof text !== "string" || !text.trim()) {
    return NextResponse.json({ error: "Missing text." }, { status: 400 });
  }

  await prisma.lessonMessage.create({
    data: { bookingId, role: "STUDENT", content: text },
  });

  const recentMessages = await prisma.lessonMessage.findMany({
    where: { bookingId },
    orderBy: { createdAt: "asc" },
    take: HISTORY_LIMIT,
  });

  const history = recentMessages.map((m) => ({
    role: m.role === "STUDENT" ? "student" : "tutor",
    content: m.content,
  }));

  let reply: string;
  try {
    const agentRes = await fetch(`${AGENT_SERVICE_URL}/agent/respond`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ subject: booking.subject, history }),
    });
    if (!agentRes.ok) throw new Error(`agent service returned ${agentRes.status}`);
    const data = await agentRes.json();
    reply = data.reply;
  } catch (err) {
    return NextResponse.json(
      { error: `Could not reach the tutor agent service: ${(err as Error).message}` },
      { status: 502 }
    );
  }

  await prisma.lessonMessage.create({
    data: { bookingId, role: "TUTOR", content: reply },
  });

  return NextResponse.json({ reply });
}
