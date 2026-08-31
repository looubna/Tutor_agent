import "server-only";
import { cache } from "react";
import { redirect } from "next/navigation";
import { getSession } from "@/lib/session";
import { prisma } from "@/lib/prisma";

export const verifySession = cache(async () => {
  const session = await getSession();
  if (!session?.userId) {
    redirect("/login");
  }
  return { userId: session.userId };
});

export const getCurrentUser = cache(async () => {
  const session = await getSession();
  if (!session?.userId) return null;

  return prisma.user.findUnique({
    where: { id: session.userId },
    select: { id: true, name: true, email: true, image: true, supportLanguage: true },
  });
});

/**
 * Who is allowed to read the material for this booking.
 *
 * `verifySession` redirects to /login on failure, which is right for a page and
 * wrong for a route a browser fetches, so this returns null instead and lets the
 * route answer 401.
 */
export async function verifyLessonAccess(): Promise<{ userId: string } | null> {
  const session = await getSession();
  return session?.userId ? { userId: session.userId } : null;
}
