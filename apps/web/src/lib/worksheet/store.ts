import "server-only";

import { prisma } from "@/lib/prisma";
import { validate, stripAnswers, assertNoAnswers, picturesIn, type PublicWorksheet, type Worksheet } from "./boxes";
import { Ops, type Op } from "./ops";

/**
 * Decks in and out of the database.
 *
 * The `boxes` column keeps its name: it holds the whole document as one JSON
 * string, so the slide/block rename never reaches the schema and no migration
 * is owed for it.
 *
 * Two rules run through all of it. A student's browser is only ever handed a
 * stripped sheet, and a student's marked copy is pinned to the version they
 * actually sat in front of — publish version 4 next month and last week's
 * lesson still shows version 3, because that is the paper that class happened on.
 */

export async function draft(lessonId: string, sheet: unknown, builtBy: string) {
  const latest = await prisma.lessonDoc.findFirst({
    where: { lessonId }, orderBy: { version: "desc" }, select: { version: true },
  });
  const version = (latest?.version ?? 0) + 1;

  // The writer does not choose these. Which lesson it belongs to is the
  // caller's to say, and which version it is belongs to whatever came before.
  const parsed = validate({ ...(sheet as object), lessonId, version });

  // §11: every picture has a licence. A path with no Asset row is a picture we
  // cannot prove we may use, so it never reaches a published document.
  const used = picturesIn(parsed);
  const licensed = new Set(
    (await prisma.asset.findMany({ where: { path: { in: used } }, select: { path: true } }))
      .map((a) => a.path),
  );
  const unlicensed = used.filter((path) => !licensed.has(path));

  // The two language gates that used to run here are gone with the German
  // course: one checked every article against words.de.json, the other refused
  // any English word on a German deck. Both were right for that course and
  // meaningless for a maths one, and a gate that cannot fire is a gate nobody
  // maintains. A maths deck needs its own — the answer keys are what matter
  // there, not the articles — and that check does not exist yet.
  const problems = unlicensed.map(
    (p) => `${p} has no Asset row, so its licence is unknown.`,
  );
  if (problems.length) {
    throw new Error("This deck cannot be saved:\n  " + problems.join("\n  "));
  }

  return prisma.lessonDoc.create({
    data: {
      lessonId, version, status: "DRAFT", builtBy,
      boxes: JSON.stringify({ ...parsed, version }),
    },
  });
}

/** A person says yes. Students only ever see a doc that has been through here. */
export async function publish(docId: string, publishedBy: string) {
  return prisma.lessonDoc.update({
    where: { id: docId },
    data: { status: "PUBLISHED", publishedBy, publishedAt: new Date() },
  });
}

export async function currentDoc(lessonId: string) {
  return prisma.lessonDoc.findFirst({
    where: { lessonId, status: "PUBLISHED" },
    orderBy: { version: "desc" },
  });
}

const parse = (row: { boxes: string }): Worksheet => validate(JSON.parse(row.boxes));

/** What the browser gets before a class: no answers, checked on the way out. */
export async function beforePaper(lessonId: string): Promise<PublicWorksheet | null> {
  const doc = await currentDoc(lessonId);
  if (!doc) return null;
  const stripped = stripAnswers(parse(doc));
  assertNoAnswers(stripped);
  return stripped;
}

/**
 * The student's own copy, created the first time they open the paper and pinned
 * to whatever version is published at that moment.
 */
export async function paperFor(bookingId: string, userId: string, lessonId: string) {
  const existing = await prisma.studentLessonDoc.findUnique({
    where: { bookingId }, include: { doc: true },
  });
  if (existing) return existing;

  const doc = await currentDoc(lessonId);
  if (!doc) return null;

  return prisma.studentLessonDoc.create({
    data: { bookingId, userId, docId: doc.id, docVersion: doc.version },
    include: { doc: true },
  });
}

/** Everything the tutor wrote, appended in order. */
export async function addOps(bookingId: string, incoming: unknown) {
  const ops = Ops.parse(incoming);
  const paper = await prisma.studentLessonDoc.findUniqueOrThrow({ where: { bookingId } });
  const merged: Op[] = [...(JSON.parse(paper.ops) as Op[]), ...ops];
  await prisma.studentLessonDoc.update({
    where: { bookingId }, data: { ops: JSON.stringify(merged) },
  });
  return merged;
}

/**
 * The tutor's copy, for the agent that is about to teach on it.
 *
 * This one has the answers on it, and it is the only path that serves them.
 * That is not a hole in §11: the agent is a server, not a browser, and it is
 * behind the same token as the marks endpoint. A tutor without the key cannot
 * tell a right answer from a plausible one, and a tutor that has to guess is
 * worse than no tutor.
 *
 * Opening it also pins the version, so the tutor and the student are looking at
 * the same paper even if a newer one is published mid-class.
 */
export async function tutorSheet(bookingId: string, userId: string, lessonId: string) {
  const pinned = await paperFor(bookingId, userId, lessonId);
  if (!pinned) return null;
  return { sheet: parse(pinned.doc), version: pinned.docVersion };
}

/**
 * What the student is looking at *during* the class.
 *
 * The paper they were given, with whatever the tutor has written on it so far,
 * and no key. It reads the pinned version like `afterPaper` does, and strips it
 * like `beforePaper` does — because both rules apply at once here: it is the
 * paper this class is happening on, and the class is not over.
 *
 * The marks carry answers, and that is the point: an answer the tutor wrote in
 * front of the student is one the student has already been shown. What must
 * never appear is the key to the questions nobody has reached yet, and
 * stripping the sheet is what keeps it out.
 */
export async function livePaper(bookingId: string) {
  const paper = await prisma.studentLessonDoc.findUnique({
    where: { bookingId }, include: { doc: true },
  });
  if (!paper) return null;

  const sheet = stripAnswers(parse(paper.doc));
  assertNoAnswers(sheet);
  return { sheet, ops: Ops.parse(JSON.parse(paper.ops)), version: paper.docVersion };
}

/**
 * The marked copy. Note it reads `paper.doc`, the version pinned at class time,
 * rather than looking up whatever is current now.
 */
export async function afterPaper(bookingId: string) {
  const paper = await prisma.studentLessonDoc.findUnique({
    where: { bookingId },
    include: { doc: true, user: { select: { name: true } } },
  });
  if (!paper) return null;

  return {
    sheet: parse(paper.doc),
    ops: Ops.parse(JSON.parse(paper.ops)),
    version: paper.docVersion,
    studentName: paper.user.name,
    extraPractice: paper.extraPractice ? (JSON.parse(paper.extraPractice) as string[]) : undefined,
  };
}
