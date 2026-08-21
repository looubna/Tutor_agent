import { NextResponse } from "next/server";
import type { NextRequest } from "next/server";
import { revalidatePath } from "next/cache";
import { verifySession } from "@/lib/dal";
import { prisma } from "@/lib/prisma";

export async function POST(request: NextRequest) {
  const { userId } = await verifySession();

  await prisma.googleCalendarConnection.deleteMany({ where: { userId } });

  revalidatePath("/settings");
  return NextResponse.redirect(new URL("/settings", request.url));
}
