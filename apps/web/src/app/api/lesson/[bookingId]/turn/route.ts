import { NextResponse } from "next/server";
import type { NextRequest } from "next/server";
import { verifyLessonAccess } from "@/lib/dal";
import { prisma } from "@/lib/prisma";
import { lessonIdFor } from "@/lib/worksheet/lessonId";
import { findLesson, levelsFor } from "@/lib/curriculum";
import { speechLocale } from "@/lib/locales";
import { SUBJECTS } from "@/lib/subjects";

/**
 * One turn of a live lesson.
 *
 * The browser talks to this; this talks to the agent. It exists rather than the
 * page calling the agent directly for three reasons, and each of them is the
 * kind that only hurts once: the agent's token would otherwise be in the
 * browser, the agent would have to be trusted about whose booking this is, and
 * the conversation would live only in a Cloud Run process's memory instead of
 * in the database the transcript is read from.
 *
 * An empty `said` means the student has just joined and the tutor should open
 * the lesson. That is a real turn, not a no-op: someone arriving at a class
 * should be greeted rather than met with silence until they type something.
 */

/** How long to wait on the agent. A turn is a model call and a paper write. */
const TURN_TIMEOUT_MS = 60_000;

export async function POST(request: NextRequest, ctx: { params: Promise<{ bookingId: string }> }) {
  const { bookingId } = await ctx.params;
  const access = await verifyLessonAccess();
  if (!access) return NextResponse.json({ error: "Not signed in." }, { status: 401 });

  const agent = process.env.AGENT_URL;
  if (!agent) {
    return NextResponse.json(
      { error: "AGENT_URL is not set, so there is no tutor to talk to." },
      { status: 503 },
    );
  }

  const booking = await prisma.booking.findFirst({
    where: { id: bookingId, studentId: access.userId },
    select: {
      subject: true, level: true, chapter: true, lesson: true,
      startTime: true, endTime: true, status: true,
    },
  });
  if (!booking) return NextResponse.json({ error: "Booking not found." }, { status: 404 });
  if (booking.status !== "UPCOMING") {
    return NextResponse.json({ error: "This class is over." }, { status: 409 });
  }

  const body = (await request.json().catch(() => ({}))) as {
    said?: string;
    present?: boolean;
    additionalPerson?: boolean;
    /** A PNG data URL of the student's own handwriting on the paper. */
    work?: string | null;
  };
  const said = (body.said ?? "").trim();

  // Recorded before the agent is called, so a turn that times out still leaves
  // the student's own words in the transcript rather than swallowing them.
  if (said) {
    await prisma.lessonMessage.create({
      data: { bookingId, role: "STUDENT", content: said },
    });
  }

  // The curriculum item, taken from the same helper the worksheet uses so the
  // tutor and the paper cannot end up on different lessons. Ours names the
  // worksheet `german.a1-1.classroom.l3`; the agent's curriculum names the item
  // `a1-1.classroom.l3`, which is the same string without its subject prefix.
  // A class that follows no chapter has no item, and the tutor teaches from
  // whatever paper it has.
  const lessonId = lessonIdFor(booking);
  const itemId = lessonId ? lessonId.slice(booking.subject.length + 1) : "";

  /**
   * Who this is and what they did last time.
   *
   * A tutor who has taught you before knows your name and remembers the last
   * hour; one who has not should find out who you are before teaching at you.
   * Both come from what we already have — the student's completed classes in
   * this subject — rather than from anything the tutor has to be told twice.
   */
  const student = await prisma.user.findUnique({
    where: { id: access.userId }, select: { name: true, supportLanguage: true },
  });
  const before = await prisma.booking.findMany({
    where: { studentId: access.userId, subject: booking.subject, status: "COMPLETED" },
    orderBy: { startTime: "desc" },
    select: { level: true, chapter: true, lesson: true, startTime: true },
    take: 1,
  });
  const previous = before[0];
  const covered = previous?.level && previous.chapter && previous.lesson
    ? findLesson(booking.subject, previous.level, previous.chapter, previous.lesson)?.lesson.title
    : null;
  const lastLesson = previous
    ? `${covered ?? "cette matière"}, ${previous.startTime.toLocaleDateString("fr-FR", {
        weekday: "long", day: "numeric", month: "long" })}`
    : "";

  const minutes = Math.max(
    1,
    Math.round((booking.endTime.getTime() - booking.startTime.getTime()) / 60000),
  );

  let reply: Response;
  try {
    reply = await fetch(`${agent.replace(/\/$/, "")}/lesson/turn`, {
      method: "POST",
      headers: { "content-type": "application/json" },
      signal: AbortSignal.timeout(TURN_TIMEOUT_MS),
      body: JSON.stringify({
        booking_id: bookingId,
        student_id: access.userId,
        subject: booking.subject,
        level_id: booking.level ?? "",
        item_id: itemId,
        start_time: booking.startTime.toISOString(),
        duration_minutes: minutes,
        // The tutor is read aloud, so it needs to know which language it is
        // being read in — the same answer the live socket gets.
        language: speechLocale(
          SUBJECTS.find((s) => s.id === booking.subject)?.locale,
          levelsFor(booking.subject).find((l) => l.id === booking.level)?.locale,
          student?.supportLanguage,
        ),
        student_name: student?.name ?? "",
        lessons_so_far: await prisma.booking.count({
          where: { studentId: access.userId, subject: booking.subject,
                   status: "COMPLETED" },
        }),
        last_lesson: lastLesson,
        student_work: body.work ?? "",
        student_said: said,
        student_present: body.present ?? true,
        additional_person_detected: body.additionalPerson ?? false,
      }),
    });
  } catch (error) {
    return NextResponse.json(
      { error: "The tutor did not answer in time.", detail: String(error) },
      { status: 504 },
    );
  }

  if (!reply.ok) {
    return NextResponse.json(
      { error: "The tutor could not take this turn.", detail: await reply.text() },
      { status: 502 },
    );
  }

  const turn = (await reply.json()) as {
    said: string;
    live_state: string;
    minutes_remaining: number;
    lesson_over: boolean;
    beats: ({ say: string; write: string; on: string; highlight?: number }
            | { turn_to: string })[];
    showing_page: string | null;
    showing_material: {
      id: string; kind: string; title: string; instruction: string; content: string;
      exercises: { id: string; prompt: string; instructions: string; options: string[] }[];
    } | null;
    marks_made: number;
    notes: string[];
  };

  if (turn.said?.trim()) {
    await prisma.lessonMessage.create({
      data: { bookingId, role: "TUTOR", content: turn.said.trim() },
    });
  }

  return NextResponse.json(turn, { headers: { "cache-control": "no-store" } });
}
