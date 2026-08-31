import "server-only";

import { existsSync } from "node:fs";
import { join } from "node:path";

/**
 * Where a lesson's handout lives, if it has one.
 *
 * Two kinds of paper exist side by side. A generated maths lesson is a PDF,
 * compiled from LaTeX and written into `public/materials/` — a document that
 * does not change between publishes, so it is served as a file. A language
 * deck is a `LessonDoc` row rendered to HTML on request, because a student's
 * copy is stripped of its answers and a tutor's is not.
 *
 * The PDF wins when both exist: it is the one somebody compiled and looked at.
 */
export function pdfFor(lessonId: string): string | null {
  const [subject, level, chapter, lesson] = lessonId.split(".");
  if (!subject || !level || !chapter || !lesson) return null;

  const url = `/materials/${subject}/${level}/${chapter}.${lesson}.pdf`;
  return existsSync(join(process.cwd(), "public", url)) ? url : null;
}
