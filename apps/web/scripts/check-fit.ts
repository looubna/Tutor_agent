/**
 * Measure how full every page of a deck is.
 *
 *     npm run check:fit                          the sample deck
 *     npm run check:fit -- --doc <docId>         a draft from the database
 *     npm run check:fit -- --file <path.json>    a deck that is not saved yet
 *     npm run check:fit -- --json                machine-readable, for the pipeline
 *
 * This is the gate the writing pipeline runs after it builds a deck, and the
 * one you run yourself after changing the CSS. It exits non-zero when a page
 * overflows or comes out mostly empty, so it can sit in front of `publish`.
 *
 * `--file` exists because the pipeline needs the answer BEFORE it saves. How
 * full a page is decides whether the writer has to redo it, and saving a deck
 * in order to find out would put a version in the database for every attempt.
 */
import { validate } from "../src/lib/worksheet/boxes";
import { measureFit, warnings, EMPTY, CRAMPED } from "../src/lib/worksheet/fit";

const bar = (fill: number) => {
  const n = Math.round(fill * 20);
  return "▓".repeat(Math.min(20, n)) + "░".repeat(Math.max(0, 20 - n));
};

async function main() {
  const args = process.argv.slice(2);
  const docId = args.includes("--doc") ? args[args.indexOf("--doc") + 1] : null;
  const file = args.includes("--file") ? args[args.indexOf("--file") + 1] : null;
  const asJson = args.includes("--json");

  const sheet = await (async () => {
    if (file) {
      const { readFile } = await import("node:fs/promises");
      return validate(JSON.parse(await readFile(file, "utf8")));
    }
    if (!docId) {
      const { SAMPLE } = await import("../src/lib/worksheet/sample");
      return validate(SAMPLE);
    }
    // Loaded here and not at the top: --file measures a deck that is not in
    // the database, and importing Prisma pulls in a native module that has to
    // match the running Node version. The writing pipeline calls this with
    // --file, from Python, under whatever Node happens to be on PATH.
    const { prisma } = await import("../src/lib/prisma");
    const doc = await prisma.lessonDoc.findUnique({ where: { id: docId } });
    if (!doc) throw new Error(`No document ${docId}`);
    console.log(`\n  ${doc.lessonId} v${doc.version} ${doc.status}`);
    return validate(JSON.parse(doc.boxes));
  })();

  const { pages, problems } = await measureFit(sheet, `${process.cwd()}/public`);

  // The pipeline reads this; a person reads the bars below it.
  if (asJson) {
    console.log(JSON.stringify({ pages, problems }));
    process.exit(problems.length ? 1 : 0);
  }

  console.log("");
  for (const p of pages) {
    const pct = `${Math.round(p.fill * 100)}%`.padStart(4);
    const flag = p.overflow > 1 ? "✂️  CUT OFF"
      : p.fill < EMPTY ? "❌ empty"
      : p.fill > CRAMPED ? "⚠️  tight"
      : "";
    console.log(`  ${String(p.page).padStart(3)}  ${p.id.padEnd(12)} ${bar(p.fill)} ${pct}  ${flag}`);
  }

  const warn = warnings(pages);
  if (warn.length) {
    console.log("\n  ⚠️  tight, but allowed:");
    for (const w of warn) console.log(`     ${w}`);
  }

  if (problems.length) {
    console.log(`\n  ❌ ${problems.length} page${problems.length > 1 ? "s" : ""} to fix:\n`);
    for (const p of problems) console.log(`     ${p}`);
    console.log("");
    process.exit(1);
  }
  console.log(`\n  ✅ all ${pages.length} pages fit.\n`);
}

main().catch((err) => { console.error(err.message); process.exit(1); });
