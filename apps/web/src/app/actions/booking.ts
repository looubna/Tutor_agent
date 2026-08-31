"use server";

import { redirect } from "next/navigation";
import { revalidatePath } from "next/cache";
import { format, isAfter, subMinutes } from "date-fns";
import { prisma } from "@/lib/prisma";
import { verifySession } from "@/lib/dal";
import { generateAvailableSlots, LESSON_DURATION_MINUTES } from "@/lib/slots";
import { syncBookingToGoogleCalendar, deleteGoogleCalendarEvent } from "@/lib/googleCalendar";
import { isLang } from "@/lib/locales";

export type BookSlotsState = { error?: string } | undefined;

/** How early a booked lesson can be joined — matches the call screen's gate. */
const JOIN_WINDOW_MINUTES = 10;

export type BookingContext = {
  subject: string;
  level: string;
  /** null for a freestyle conversation, which follows no chapter. */
  chapter: string | null;
  /**
   * Which lesson of that chapter. Omitted means the first one, which is what a
   * chapter booked from the calendar has always meant.
   *
   * It matters more than it looks: the worksheet and the prepared material are
   * per lesson, so a class that does not name one always lands on lesson 1 and
   * a student who pressed "Start now" beside lesson 3 gets lesson 1's paper.
   */
  lesson?: string | null;
  kind?: "LESSON" | "FREESTYLE";
  /**
   * The language the tutor may explain in when the learner is stuck. Asked when
   * booking a language class, but stored on the learner rather than the booking
   * — it is a fact about them, and it should hold for every class they take.
   */
  supportLanguage?: string;
};

/** Remembers the help language chosen while booking, if a valid one was sent. */
async function rememberSupportLanguage(userId: string, value: string | undefined) {
  if (!isLang(value)) return;
  await prisma.user.update({ where: { id: userId }, data: { supportLanguage: value } });
}

/** A learner-typed topic is free text, so it is trimmed and capped before it is stored. */
const TOPIC_MAX_LENGTH = 200;

export async function bookSlots(
  startTimes: string[],
  context: BookingContext,
): Promise<BookSlotsState> {
  const { userId } = await verifySession();

  if (!Array.isArray(startTimes) || startTimes.length === 0) {
    return { error: "Please choose at least one lesson time." };
  }

  const requested = startTimes.map((raw) => new Date(raw));
  if (requested.some((d) => Number.isNaN(d.getTime()))) {
    return { error: "Invalid lesson time." };
  }

  const existingBookings = await prisma.booking.findMany({
    where: { studentId: userId, status: "UPCOMING" },
    select: { startTime: true, endTime: true },
  });

  const validTimes = new Set(generateAvailableSlots(existingBookings).map((s) => s.startTime.getTime()));

  const seen = new Set<number>();
  const invalid: string[] = [];
  for (const date of requested) {
    const t = date.getTime();
    if (!validTimes.has(t) || seen.has(t)) {
      invalid.push(format(date, "MMM d, h:mm a"));
    }
    seen.add(t);
  }

  if (invalid.length > 0) {
    return {
      error: `These times are no longer available: ${invalid.join(", ")}. Please review your selection.`,
    };
  }

  // Slots start every 30 minutes but run for 50, so two offered times can
  // overlap. Bookings already made are filtered out by generateAvailableSlots;
  // times picked together in the same basket are only caught here.
  const ordered = [...requested].sort((a, b) => a.getTime() - b.getTime());
  for (let i = 1; i < ordered.length; i++) {
    const previousEnd = ordered[i - 1].getTime() + LESSON_DURATION_MINUTES * 60_000;
    if (ordered[i].getTime() < previousEnd) {
      return {
        error: `${format(ordered[i - 1], "MMM d, h:mm a")} and ${format(ordered[i], "h:mm a")} overlap — a lesson lasts ${LESSON_DURATION_MINUTES} minutes. Please drop one of them.`,
      };
    }
  }

  await rememberSupportLanguage(userId, context.supportLanguage);

  const created = await prisma.$transaction(
    requested.map((startTime) =>
      prisma.booking.create({
        data: {
          studentId: userId,
          startTime,
          endTime: new Date(startTime.getTime() + LESSON_DURATION_MINUTES * 60_000),
          subject: context.subject,
          level: context.level,
          chapter: context.chapter,
          lesson: context.lesson ?? null,
        },
      })
    )
  );

  // Best-effort: Google Calendar sync must never block or fail a booking that already succeeded.
  await Promise.all(created.map((booking) => syncBookingToGoogleCalendar(booking, userId)));

  revalidatePath("/dashboard");
  revalidatePath("/calendar");
  redirect("/dashboard");
}

export type CancelBookingState = { error?: string } | undefined;

export async function cancelBooking(
  bookingId: string,
  // useActionState requires this shape; the bound bookingId is the only input we need.
  // eslint-disable-next-line @typescript-eslint/no-unused-vars
  _state: CancelBookingState,
  // eslint-disable-next-line @typescript-eslint/no-unused-vars
  _formData: FormData
): Promise<CancelBookingState> {
  const { userId } = await verifySession();

  const booking = await prisma.booking.findFirst({
    where: { id: bookingId, studentId: userId, status: "UPCOMING" },
  });
  if (!booking) {
    return { error: "This lesson can no longer be cancelled." };
  }

  if (isAfter(new Date(), subMinutes(booking.startTime, 30))) {
    return { error: "You can't cancel a lesson less than 30 minutes before it starts." };
  }

  await prisma.booking.update({ where: { id: bookingId }, data: { status: "CANCELLED" } });
  await deleteGoogleCalendarEvent(booking, userId);
  revalidatePath("/dashboard");
  revalidatePath("/calendar");
}

export type StartNowState = { error?: string } | undefined;

/**
 * A lesson that starts this second, for someone who came to study rather than
 * to plan. It writes the same Booking row the calendar does — so the class
 * still lands in My classes and can be resumed — but skips the slot grid,
 * which only offers times on the hour and half hour and never in the past.
 *
 * Deliberately not synced to Google Calendar: an event for something already
 * under way is noise in a diary.
 */
export async function startLessonNow(
  context: BookingContext,
  // useActionState requires this shape; the bound context carries the rest.
  _state: StartNowState,
  formData: FormData,
): Promise<StartNowState> {
  const { userId } = await verifySession();

  const now = new Date();
  const endTime = new Date(now.getTime() + LESSON_DURATION_MINUTES * 60_000);

  const clash = await prisma.booking.findFirst({
    where: {
      studentId: userId,
      status: "UPCOMING",
      startTime: { lt: endTime },
      endTime: { gt: now },
    },
    orderBy: { startTime: "asc" },
  });

  if (clash) {
    // A class that is already joinable is the one they meant — take them into
    // it rather than refusing or booking a second lesson on top of it.
    if (isAfter(now, subMinutes(clash.startTime, JOIN_WINDOW_MINUTES))) {
      redirect(`/lesson/${clash.id}`);
    }
    return {
      error: `You already have a lesson at ${format(clash.startTime, "h:mm a")}. Start it from My classes once it opens, or cancel it first.`,
    };
  }

  // Only a freestyle conversation has somewhere to put a topic; a chapter
  // lesson already knows what it is about.
  const kind = context.kind ?? "LESSON";
  const topic =
    kind === "FREESTYLE"
      ? formData.get("topic")?.toString().trim().slice(0, TOPIC_MAX_LENGTH) || null
      : null;

  // A start-now form can carry the choice as a field; the calendar flow passes
  // it on the bound context. Either way it lands on the learner.
  await rememberSupportLanguage(
    userId,
    formData.get("supportLanguage")?.toString() || context.supportLanguage,
  );

  const booking = await prisma.booking.create({
    data: {
      studentId: userId,
      startTime: now,
      endTime,
      subject: context.subject,
      level: context.level,
      chapter: context.chapter,
      lesson: context.lesson ?? null,
      kind,
      topic,
    },
  });

  revalidatePath("/dashboard");
  revalidatePath("/calendar");
  redirect(`/lesson/${booking.id}`);
}

export async function completeBooking(bookingId: string) {
  const { userId } = await verifySession();

  await prisma.booking.updateMany({
    where: { id: bookingId, studentId: userId },
    data: { status: "COMPLETED" },
  });

  revalidatePath("/dashboard");
  revalidatePath("/calendar");
}
