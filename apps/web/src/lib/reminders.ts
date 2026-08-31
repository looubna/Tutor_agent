import "server-only";
import { format } from "date-fns";
import { Resend } from "resend";
import { prisma } from "@/lib/prisma";
import { subjectLabel } from "@/lib/subjects";
import { TUTOR_NAME } from "@/lib/tutor";

const REMINDER_WINDOW_MINUTES = 60;
const CHECK_INTERVAL_MS = 60_000;
const APP_URL = process.env.NEXT_PUBLIC_APP_URL ?? "http://localhost:3000";

let warnedMissingConfig = false;
let schedulerStarted = false;

function getResendClient() {
  const apiKey = process.env.RESEND_API_KEY;
  if (!apiKey) {
    if (!warnedMissingConfig) {
      console.warn("[reminders] RESEND_API_KEY is not set — lesson reminder emails are disabled.");
      warnedMissingConfig = true;
    }
    return null;
  }
  return new Resend(apiKey);
}

type ReminderBooking = {
  id: string;
  subject: string;
  startTime: Date;
  student: { email: string; name: string };
};

export async function sendLessonReminder(booking: ReminderBooking) {
  const resend = getResendClient();
  if (!resend) return false;

  const from = process.env.RESEND_FROM_EMAIL ?? "Zanoba <onboarding@resend.dev>";
  const time = format(booking.startTime, "h:mm a 'on' EEEE, MMMM d");
  const link = `${APP_URL}/lesson/${booking.id}`;
  const lesson = `${subjectLabel(booking.subject)} lesson`;

  try {
    await resend.emails.send({
      from,
      to: booking.student.email,
      subject: `Your ${lesson} starts in 1 hour`,
      html: `<p>Hi ${booking.student.name},</p><p>Your ${lesson} with ${TUTOR_NAME} starts in 1 hour, at ${time}.</p><p><a href="${link}">Join your lesson</a></p>`,
    });
    return true;
  } catch (err) {
    console.error("[reminders] failed to send reminder for booking", booking.id, err);
    return false;
  }
}

export async function checkAndSendReminders() {
  const now = new Date();
  const windowEnd = new Date(now.getTime() + REMINDER_WINDOW_MINUTES * 60_000);

  const bookings = await prisma.booking.findMany({
    where: {
      status: "UPCOMING",
      reminderSentAt: null,
      startTime: { gte: now, lte: windowEnd },
    },
    include: { student: { select: { email: true, name: true } } },
  });

  for (const booking of bookings) {
    const sent = await sendLessonReminder(booking);
    if (sent) {
      await prisma.booking.update({ where: { id: booking.id }, data: { reminderSentAt: new Date() } });
    }
  }
}

export function startReminderScheduler() {
  if (schedulerStarted) return;
  schedulerStarted = true;

  if (!process.env.RESEND_API_KEY) {
    getResendClient(); // logs the single "not configured" notice
    return;
  }

  setInterval(() => {
    checkAndSendReminders().catch((err) => console.error("[reminders] scheduler tick failed", err));
  }, CHECK_INTERVAL_MS);
}
