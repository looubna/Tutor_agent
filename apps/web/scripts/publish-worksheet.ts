/**
 * Publish a worksheet draft. This is the human gate (§5.3).
 *
 *     npx tsx --env-file=.env --conditions=react-server scripts/publish-worksheet.ts --list
 *     npx tsx --env-file=.env --conditions=react-server scripts/publish-worksheet.ts german.a1-1.classroom --by "Loubna"
 *
 * Read the paper first — open /api/lesson/<a booking>/paper. A draft serves
 * nobody; a published one serves every student who ever books that chapter,
 * so this is the one moment a person is in the loop.
 */
import { prisma } from "../src/lib/prisma";
import { publish } from "../src/lib/worksheet/store";

async function main() {
  const args = process.argv.slice(2);
  const by = args.includes("--by") ? args[args.indexOf("--by") + 1] : undefined;
  const lessonId = args.find((a) => !a.startsWith("--") && a !== by);

  const docs = await prisma.lessonDoc.findMany({ orderBy: [{ lessonId: "asc" }, { version: "asc" }] });
  if (!lessonId || args.includes("--list")) {
    for (const d of docs) {
      console.log(`  ${d.status === "PUBLISHED" ? "✓" : "·"} ${d.lessonId} v${d.version}` +
        `  ${d.status}${d.publishedBy ? ` — ${d.publishedBy}` : ""}  (${d.id})`);
    }
    if (!lessonId) console.log("\n  pass a lessonId and --by \"your name\" to publish its newest draft");
    return;
  }
  if (!by) throw new Error('--by is required: a worksheet is published by a person, not a script');

  const draft = docs.filter((d) => d.lessonId === lessonId).at(-1);
  if (!draft) throw new Error(`No worksheet for ${lessonId}`);
  if (draft.status === "PUBLISHED") return console.log(`  ${lessonId} v${draft.version} is already published`);

  await publish(draft.id, by);
  console.log(`  published ${lessonId} v${draft.version} as ${by}`);
}

main().catch((err) => { console.error(err.message); process.exit(1); });
