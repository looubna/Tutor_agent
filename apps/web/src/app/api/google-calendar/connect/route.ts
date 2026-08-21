import { NextResponse } from "next/server";
import type { NextRequest } from "next/server";
import { verifySession } from "@/lib/dal";
import { getAuthUrl } from "@/lib/googleCalendar";

export async function GET(request: NextRequest) {
  const { userId } = await verifySession();

  const url = getAuthUrl(userId);
  if (!url) {
    return NextResponse.redirect(new URL("/settings?error=1", request.url));
  }

  return NextResponse.redirect(url);
}
