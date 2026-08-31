/**
 * Print a worksheet to PDF.
 *
 *     npm run paper:pdf german.a1-1.classroom.l1
 *     npm run paper:pdf german.a1-1.classroom.l1 -- --after <bookingId>
 *
 * Uses the copy of Chrome already on the machine rather than adding a headless
 * browser to the dependency list. The CSS is what makes the pages: A4
 * landscape, one task per page, the same rules the browser prints with.
 */
import { execFile } from "node:child_process";
import { mkdtemp, writeFile, rm } from "node:fs/promises";
import { tmpdir } from "node:os";
import { join } from "node:path";
import { promisify } from "node:util";

import { beforePaper, afterPaper } from "../src/lib/worksheet/store";
import { render, forFileSystem } from "../src/lib/worksheet/render";

const run = promisify(execFile);
const CHROME = process.env.CHROME_PATH
  ?? "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome";

async function main() {
  const [worksheetId, ...rest] = process.argv.slice(2);
  if (!worksheetId) throw new Error("usage: paper-pdf.ts <subject.level.chapter.lesson> [--after <bookingId>]");

  const bookingId = rest.includes("--after") ? rest[rest.indexOf("--after") + 1] : null;

  const html = await (async () => {
    if (bookingId) {
      const marked = await afterPaper(bookingId);
      if (!marked) throw new Error(`No marked copy for booking ${bookingId}`);
      return render(marked.sheet, {
        kind: "after", ops: marked.ops,
        studentName: marked.studentName, extraPractice: marked.extraPractice,
      });
    }
    const sheet = await beforePaper(worksheetId);
    if (!sheet) throw new Error(`No published worksheet for ${worksheetId}`);
    return render(sheet, { kind: "before" });
  })();

  // Pictures are referenced from public/ by absolute path, so the page is
  // loaded from a file next to them rather than from a string.
  const dir = await mkdtemp(join(tmpdir(), "zanoba-pdf-"));
  const page = join(dir, "paper.html");
  await writeFile(page, forFileSystem(html, `${process.cwd()}/public`));

  const out = join(process.cwd(), "..", "..",
    `${worksheetId}${bookingId ? ".after" : ""}.pdf`);
  await run(CHROME, [
    "--headless", "--disable-gpu", "--no-pdf-header-footer",
    `--print-to-pdf=${out}`, `file://${page}`,
  ]);
  await rm(dir, { recursive: true, force: true });

  console.log(`\n  ${out}\n`);
}

main().catch((err) => { console.error(err.message); process.exit(1); });
