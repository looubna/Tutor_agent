import { NextResponse } from "next/server";
import type { NextRequest } from "next/server";
import { verifySession } from "@/lib/dal";

const AGENT_SERVICE_URL = process.env.AGENT_SERVICE_URL ?? "http://localhost:8000";

type ChatTurn = { role: "student" | "tutor"; content: string };

function isValidHistory(history: unknown): history is ChatTurn[] {
  return (
    Array.isArray(history) &&
    history.length > 0 &&
    history.every(
      (turn): turn is ChatTurn =>
        !!turn &&
        typeof turn === "object" &&
        (turn as ChatTurn).role !== undefined &&
        ((turn as ChatTurn).role === "student" || (turn as ChatTurn).role === "tutor") &&
        typeof (turn as ChatTurn).content === "string" &&
        (turn as ChatTurn).content.trim().length > 0
    ) &&
    history[history.length - 1].role === "student"
  );
}

export async function POST(request: NextRequest) {
  await verifySession();

  const { history } = await request.json();
  if (!isValidHistory(history)) {
    return NextResponse.json({ error: "Invalid conversation history." }, { status: 400 });
  }

  let reply: string;
  try {
    const agentRes = await fetch(`${AGENT_SERVICE_URL}/agent/respond`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ subject: "Math", history }),
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

  return NextResponse.json({ reply });
}
