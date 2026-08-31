import "server-only";
import { google } from "googleapis";
import { prisma } from "@/lib/prisma";
import { subjectLabel } from "@/lib/subjects";
import { TUTOR_NAME } from "@/lib/tutor";

const SCOPES = ["https://www.googleapis.com/auth/calendar.events"];
const APP_URL = process.env.NEXT_PUBLIC_APP_URL ?? "http://localhost:3000";

let warnedMissingConfig = false;

function getEnv() {
  const clientId = process.env.GOOGLE_CLIENT_ID;
  const clientSecret = process.env.GOOGLE_CLIENT_SECRET;
  const redirectUri = process.env.GOOGLE_REDIRECT_URI ?? `${APP_URL}/api/google-calendar/callback`;
  return { clientId, clientSecret, redirectUri };
}

export function isGoogleCalendarConfigured() {
  const { clientId, clientSecret } = getEnv();
  return Boolean(clientId && clientSecret);
}

export function getOAuthClient() {
  const { clientId, clientSecret, redirectUri } = getEnv();
  if (!clientId || !clientSecret) {
    if (!warnedMissingConfig) {
      console.warn(
        "[google-calendar] GOOGLE_CLIENT_ID/GOOGLE_CLIENT_SECRET are not set — Google Calendar sync is disabled."
      );
      warnedMissingConfig = true;
    }
    return null;
  }
  return new google.auth.OAuth2(clientId, clientSecret, redirectUri);
}

export function getAuthUrl(userId: string) {
  const client = getOAuthClient();
  if (!client) return null;
  return client.generateAuthUrl({
    access_type: "offline",
    prompt: "consent",
    scope: SCOPES,
    state: userId,
  });
}

async function getCalendarClientForUser(userId: string) {
  const client = getOAuthClient();
  if (!client) return null;

  const connection = await prisma.googleCalendarConnection.findUnique({ where: { userId } });
  if (!connection) return null;

  client.setCredentials({
    access_token: connection.accessToken,
    refresh_token: connection.refreshToken,
    expiry_date: connection.expiryDate.getTime(),
  });

  client.on("tokens", (tokens) => {
    if (!tokens.access_token && !tokens.expiry_date) return;
    prisma.googleCalendarConnection
      .update({
        where: { userId },
        data: {
          ...(tokens.access_token ? { accessToken: tokens.access_token } : {}),
          ...(tokens.expiry_date ? { expiryDate: new Date(tokens.expiry_date) } : {}),
        },
      })
      .catch((err) => console.error("[google-calendar] failed to persist refreshed token", err));
  });

  return google.calendar({ version: "v3", auth: client });
}

type BookingLike = { id: string; startTime: Date; endTime: Date; subject: string };

export async function syncBookingToGoogleCalendar(booking: BookingLike, userId: string) {
  try {
    const calendar = await getCalendarClientForUser(userId);
    if (!calendar) return;

    const res = await calendar.events.insert({
      calendarId: "primary",
      requestBody: {
        summary: `${subjectLabel(booking.subject)} lesson with ${TUTOR_NAME}`,
        description: `Join your lesson: ${APP_URL}/lesson/${booking.id}`,
        start: { dateTime: booking.startTime.toISOString() },
        end: { dateTime: booking.endTime.toISOString() },
      },
    });

    if (res.data.id) {
      await prisma.booking.update({ where: { id: booking.id }, data: { googleEventId: res.data.id } });
    }
  } catch (err) {
    console.error("[google-calendar] failed to sync booking", booking.id, err);
  }
}

export async function deleteGoogleCalendarEvent(booking: { id: string; googleEventId: string | null }, userId: string) {
  if (!booking.googleEventId) return;
  try {
    const calendar = await getCalendarClientForUser(userId);
    if (!calendar) return;

    await calendar.events.delete({ calendarId: "primary", eventId: booking.googleEventId });
  } catch (err) {
    const status = (err as { code?: number; status?: number }).code ?? (err as { status?: number }).status;
    if (status === 404 || status === 410) return; // already gone — treat as success
    console.error("[google-calendar] failed to delete event for booking", booking.id, err);
  }
}
