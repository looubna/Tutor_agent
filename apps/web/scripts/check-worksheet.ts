/**
 * The §11 worksheet tests, against the database and the real routes.
 *
 *     npm run check:worksheet
 *
 * Three things a unit test cannot prove: that the blank paper served over HTTP
 * carries no answers, that the tutor's marks land on the boxes they were aimed
 * at, and that publishing a new version does not rewrite the paper a student
 * already sat in front of.
 */
import { prisma } from "../src/lib/prisma";
import { encrypt } from "../src/lib/session";
import { publish, currentDoc, paperFor, addOps, afterPaper, beforePaper } from "../src/lib/worksheet/store";
import { marksMade } from "../src/lib/worksheet/ops";

const BASE = "http://localhost:3000";
const LESSON = "german.a1-1.classroom";
const MINUTES = 60 * 1000;

const fails: string[] = [];
const check = (label: string, ok: boolean, detail = "") => {
  console.log(`  ${ok ? "✓" : "✗"} ${label}${detail ? `  ${detail}` : ""}`);
  if (!ok) fails.push(label);
};

async function main() {
  const draft = await prisma.lessonDoc.findFirst({
    where: { lessonId: LESSON }, orderBy: { version: "desc" },
  });
  if (!draft) throw new Error(`No deck for ${LESSON}. Run write_material.py first.`);

  console.log(`\n  ${LESSON} · v${draft.version} · ${draft.status}\n`);

  console.log("publish");
  if (draft.status !== "PUBLISHED") await publish(draft.id, "check script");
  const live = await currentDoc(LESSON);
  check("a published version exists", live?.version === draft.version, `v${live?.version}`);

  console.log("\n🔒 no answers reach the student");
  const before = await beforePaper(LESSON);
  check("the stripped sheet has no answer field", !/answer/i.test(JSON.stringify(before)));

  const user = await prisma.user.findFirstOrThrow({
    where: { email: { not: { contains: "@zanoba.test" } } },
  });
  const booking = await prisma.booking.create({
    data: {
      studentId: user.id, subject: "german", level: "a1-1", chapter: "classroom",
      startTime: new Date(Date.now() - MINUTES), endTime: new Date(Date.now() + 50 * MINUTES),
    },
  });
  const cookie = `session=${await encrypt({ userId: user.id, expiresAt: Date.now() + 60 * MINUTES })}`;

  const res = await fetch(`${BASE}/api/lesson/${booking.id}/paper`, { headers: { cookie } });
  const html = await res.text();
  check("the blank paper is served", res.status === 200, `${html.length} bytes`);
  check("and the page it sends mentions no answer", !/answer/i.test(html));

  const sheet = JSON.parse(live!.boxes) as {
    slides: { id: string; blocks: { kind: string; rows?: { answer?: string }[] }[] }[];
  };
  const answers = sheet.slides.flatMap((slide) =>
    slide.blocks.flatMap((b) =>
      b.kind === "exercise" || b.kind === "build" || b.kind === "choose"
        ? (b.rows ?? []).map((r) => r.answer).filter(Boolean)
        : [],
    ),
  ) as string[];

  // Read the ids off the published deck rather than naming them here. The
  // material agent chooses them, and a check that hardcodes "b4" starts
  // silently passing the day a deck has no b4 to write on.
  const slideIds = sheet.slides.map((s) => s.id);

  // Not "does the string 'der' appear" — of course it does, it is the word being
  // taught, printed all over the page. What must not appear is a gap with
  // something written in it, which is the only place an answer can hide.
  check("every gap on the blank paper is empty",
    !html.includes("gap filled"), `${(html.match(/class="gap"/g) ?? []).length} empty gaps`);
  check("the answers exist on the published doc", answers.length > 0, `${answers.length} of them`);

  console.log("\n✍️ the tutor's writing arrives");
  await paperFor(booking.id, user.id, LESSON);
  const [first, second, third] = slideIds;
  const ops = await addOps(booking.id, [
    { id: "o1", op: "write", on: { box: second }, text: "der = maskulin" },
    { id: "o2", op: "circle", on: { box: third }, words: [0] },
    { id: "o3", op: "fill", on: { box: third }, row: 0, text: "Der" },
    { id: "o4", op: "point", on: { box: first } },
  ]);
  check("four ops in, three marks kept", marksMade(ops) === 3, "the pointer is a gesture");

  const marked = await fetch(`${BASE}/api/lesson/${booking.id}/paper?v=after`, { headers: { cookie } });
  const afterHtml = await marked.text();
  check("the marked paper is served", marked.status === 200);
  check("the handwriting is on it", afterHtml.includes("der = maskulin"));
  check("the answers are on it now", answers.some((a) => afterHtml.includes(a)));
  check("and it is labelled as the after copy", afterHtml.includes("Nach dem Unterricht"));
  check("and it carries the Lösungen page", afterHtml.includes("Lösungen"));

  console.log("\n📌 old papers still work");
  const pinned = await afterPaper(booking.id);
  const v2 = await prisma.lessonDoc.create({
    data: {
      lessonId: LESSON, version: live!.version + 1, status: "PUBLISHED",
      publishedBy: "check script", publishedAt: new Date(),
      boxes: JSON.stringify({ ...JSON.parse(live!.boxes), version: live!.version + 1,
        title: "A NEWER DECK" }),
    },
  });
  const stillPinned = await afterPaper(booking.id);
  check(
    "publishing a newer version does not move an existing copy",
    stillPinned?.version === pinned?.version,
    `class used v${pinned?.version}, current is v${v2.version}`,
  );
  check("and the old copy still shows the old title", stillPinned!.sheet.title !== "A NEWER DECK");

  console.log("\n📷 every picture has a licence");
  const bad = await prisma.asset.count({ where: { licence: "" } });
  check("no asset row with a blank licence", bad === 0, `${await prisma.asset.count()} assets`);

  await prisma.lessonDoc.delete({ where: { id: v2.id } });
  await prisma.booking.delete({ where: { id: booking.id } });

  console.log(fails.length ? `\n  ❌ failed: ${fails.join(", ")}\n` : "\n  ✅ all worksheet checks pass\n");
  if (fails.length) process.exit(1);
}

main().catch((err) => { console.error(err); process.exit(1); });
