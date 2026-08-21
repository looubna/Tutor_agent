"use server";

import { redirect } from "next/navigation";
import { revalidatePath } from "next/cache";
import { format, isAfter, subMinutes } from "date-fns";
import { prisma } from "@/lib/prisma";
import { verifySession } from "@/lib/dal";
import { generateAvailableSlots, LESSON_DURATION_MINUTES } from "@/lib/slots";
import { syncBookingToGoogleCalendar, deleteGoogleCalendarEvent } from "@/lib/googleCalendar";

export type BookSlotsState = { error?: string } | undefined;

export async function bookSlots(startTimes: string[]): Promise<BookSlotsState> {
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

  const created = await prisma.$transaction(
    requested.map((startTime) =>
      prisma.booking.create({
        data: {
          studentId: userId,
          startTime,
          endTime: new Date(startTime.getTime() + LESSON_DURATION_MINUTES * 60_000),
          subject: "Math",
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

export async function completeBooking(bookingId: string) {
  const { userId } = await verifySession();

  await prisma.booking.updateMany({
    where: { id: bookingId, studentId: userId },
    data: { status: "COMPLETED" },
  });

  revalidatePath("/dashboard");
  revalidatePath("/calendar");
}
