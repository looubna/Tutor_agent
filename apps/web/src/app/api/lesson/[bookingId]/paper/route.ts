import { NextResponse } from "next/server";
import type { NextRequest } from "next/server";
import { verifyLessonAccess } from "@/lib/dal";
import { prisma } from "@/lib/prisma";
import { lessonIdFor } from "@/lib/worksheet/lessonId";
import { beforePaper, paperFor, afterPaper, livePaper } from "@/lib/worksheet/store";
import { render } from "@/lib/worksheet/render";

/**
 * The paper itself, as a page you can read and print.
 *
 *   GET …/paper            the worksheet as it is before the class
 *   GET …/paper?v=live     the same paper as it stands mid-class, marks and all
 *   GET …/paper?v=after    the tutor's copy: the marks plus the key
 *
 * BEFORE is built from the stripped sheet — the answers are not hidden by CSS,
 * they never leave the server. LIVE is the stripped sheet too, with the marks
 * the tutor has made so far replayed onto it; it is what the class watches, and
 * it carries no key because the class is not over. AFTER reads the version
 * pinned to this booking, not whatever is published today.
 */
export async function GET(request: NextRequest, ctx: { params: Promise<{ bookingId: string }> }) {
  const { bookingId } = await ctx.params;
  const access = await verifyLessonAccess();
  if (!access) return NextResponse.json({ error: "Not signed in." }, { status: 401 });

  const booking = await prisma.booking.findFirst({
    where: { id: bookingId, studentId: access.userId },
    select: { subject: true, level: true, chapter: true, lesson: true },
  });
  if (!booking) return NextResponse.json({ error: "Booking not found." }, { status: 404 });

  const lessonId = lessonIdFor(booking);
  if (!lessonId) {
    return NextResponse.json({ error: "This class follows no chapter." }, { status: 404 });
  }

  const version = request.nextUrl.searchParams.get("v");

  const html = await (async () => {
    if (version === "live") {
      // Opening the paper is also what pins the version for this class, so a
      // student who joins straight into the live view gets a copy like anyone
      // else rather than a 404.
      await paperFor(bookingId, access.userId, lessonId);
      const live = await livePaper(bookingId);
      return live ? render(live.sheet, { kind: "after", ops: live.ops }) : null;
    }
    if (version === "after") {
      await paperFor(bookingId, access.userId, lessonId);
      const marked = await afterPaper(bookingId);
      if (!marked) return null;
      return render(marked.sheet, {
        kind: "after",
        ops: marked.ops,
        studentName: marked.studentName,
        extraPractice: marked.extraPractice,
      });
    }
    // Opening the blank paper is also what pins the version for this class.
    await paperFor(bookingId, access.userId, lessonId);
    const sheet = await beforePaper(lessonId);
    return sheet ? render(sheet, { kind: "before" }) : null;
  })();

  if (!html) {
    return NextResponse.json(
      { error: "No worksheet has been published for this lesson yet." },
      { status: 404 },
    );
  }
  return new NextResponse(html, {
    headers: { "content-type": "text/html; charset=utf-8", "cache-control": "no-store" },
  });
}
