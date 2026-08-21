import { NextResponse } from "next/server";
import type { NextRequest } from "next/server";
import { revalidatePath } from "next/cache";
import { verifySession } from "@/lib/dal";
import { prisma } from "@/lib/prisma";
import { getOAuthClient } from "@/lib/googleCalendar";

export async function GET(request: NextRequest) {
  const { userId } = await verifySession();
  const { searchParams } = request.nextUrl;

  if (searchParams.get("error")) {
    return NextResponse.redirect(new URL("/settings?error=1", request.url));
  }

  const code = searchParams.get("code");
  const client = getOAuthClient();
  if (!code || !client) {
    return NextResponse.redirect(new URL("/settings?error=1", request.url));
  }

  try {
    const { tokens } = await client.getToken(code);
    if (!tokens.access_token || !tokens.expiry_date) {
      throw new Error("Google did not return the expected tokens.");
    }

    const existing = await prisma.googleCalendarConnection.findUnique({ where: { userId } });

    await prisma.googleCalendarConnection.upsert({
      where: { userId },
      create: {
        userId,
        accessToken: tokens.access_token,
        // Google only sends a refresh_token on first consent — this is a create, so it must be present.
        refreshToken: tokens.refresh_token ?? "",
        expiryDate: new Date(tokens.expiry_date),
      },
      update: {
        accessToken: tokens.access_token,
        // Re-consent may omit refresh_token — keep the previously stored one rather than wiping it.
        refreshToken: tokens.refresh_token ?? existing?.refreshToken ?? "",
        expiryDate: new Date(tokens.expiry_date),
      },
    });

    revalidatePath("/settings");
    return NextResponse.redirect(new URL("/settings?connected=1", request.url));
  } catch (err) {
    console.error("[google-calendar] OAuth callback failed", err);
    return NextResponse.redirect(new URL("/settings?error=1", request.url));
  }
}
