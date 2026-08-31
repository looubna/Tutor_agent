/**
 * Render a deck straight to HTML and PDF.
 *
 *     npm run deck:preview                      the sample deck
 *     npm run deck:preview -- --after           …with the answers on it
 *     npm run deck:preview -- --doc <docId>     a draft from the database
 *     npm run deck:preview -- --file <path>     a sheet built outside the app
 *
 * Two jobs. Without --doc it renders the sample, which is the loop the format
 * was designed in: change the CSS, run this, put the PDF beside the reference
 * deck. With --doc it renders a real draft, and with --after as well it shows
 * the answers and the Lösungen page — which is why this is a script and not a
 * route. Nothing here publishes anything.
 */
import { execFile } from "node:child_process";
import { writeFile } from "node:fs/promises";
import { join } from "node:path";
import { promisify } from "node:util";

import { readFile } from "node:fs/promises";

import { validate, stripAnswers } from "../src/lib/worksheet/boxes";
import { render, forFileSystem } from "../src/lib/worksheet/render";
import { SAMPLE } from "../src/lib/worksheet/sample";

const run = promisify(execFile);
const CHROME = process.env.CHROME_PATH
  ?? "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome";

async function main() {
  const args = process.argv.slice(2);
  const after = args.includes("--after");
  const docId = args.includes("--doc") ? args[args.indexOf("--doc") + 1] : null;

  // A sheet built outside the app — by the material agents, before it is saved.
  // Rendering one should not need the database, so prisma is only reached for
  // --doc: importing it at the top made a file preview fail on a native module
  // it never uses.
  const file = args.includes("--file") ? args[args.indexOf("--file") + 1] : null;

  const sheet = await (async () => {
    if (file) {
      const parsed = validate(JSON.parse(await readFile(file, "utf8")));
      console.log(`\n  ${parsed.lessonId} v${parsed.version} from ${file}`);
      return parsed;
    }
    if (!docId) return validate(SAMPLE);
    const { prisma } = await import("../src/lib/prisma");
    const doc = await prisma.lessonDoc.findUnique({ where: { id: docId } });
    if (!doc) throw new Error(`No document ${docId}`);
    console.log(`\n  ${doc.lessonId} v${doc.version} ${doc.status}`);
    return validate(JSON.parse(doc.boxes));
  })();
  const html = after
    ? render(sheet, { kind: "after", ops: [], studentName: "Amal" })
    : render(stripAnswers(sheet), { kind: "before" });

  const out = args.find((a) => a.endsWith(".pdf"))
    ?? join(process.cwd(), `${docId ?? (file ? "file" : "sample")}-deck${after ? ".after" : ""}.pdf`);
  const page = out.replace(/\.pdf$/, ".html");

  // Pictures are referenced from public/ by absolute path, so the page is
  // loaded from a file next to them rather than from a string.
  await writeFile(page, forFileSystem(html, `${process.cwd()}/public`));
  await run(CHROME, [
    "--headless", "--disable-gpu", "--no-pdf-header-footer",
    `--print-to-pdf=${out}`, `file://${page}`,
  ]);
  console.log(`\n  ${out}\n`);
}

main().catch((err) => { console.error(err.message); process.exit(1); });
