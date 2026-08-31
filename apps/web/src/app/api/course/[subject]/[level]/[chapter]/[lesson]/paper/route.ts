import { NextResponse } from "next/server";
import { verifySession } from "@/lib/dal";
import { worksheetIdFor } from "@/lib/worksheet/lessonId";
import { beforePaper } from "@/lib/worksheet/store";
import { render } from "@/lib/worksheet/render";

/**
 * The lesson's worksheet, read from the course pages rather than from a class.
 *
 * No booking involved: the blank paper is the same for every student and holds
 * no answers, so anyone signed in may read the one for a chapter they are
 * studying. The marked-up copy is the private one, and that still lives behind
 * a booking.
 */
export async function GET(
  _request: Request,
  ctx: { params: Promise<{ subject: string; level: string; chapter: string; lesson: string }> },
) {
  await verifySession();
  const { subject, level, chapter, lesson } = await ctx.params;

  const worksheetId = worksheetIdFor(subject, level, chapter, lesson);
  if (!worksheetId) {
    return NextResponse.json({ error: "No such lesson." }, { status: 404 });
  }

  const sheet = await beforePaper(worksheetId);
  if (!sheet) {
    return NextResponse.json(
      { error: "No worksheet has been published for this lesson yet." },
      { status: 404 },
    );
  }

  return new NextResponse(render(sheet, { kind: "before" }), {
    headers: { "content-type": "text/html; charset=utf-8", "cache-control": "no-store" },
  });
}
