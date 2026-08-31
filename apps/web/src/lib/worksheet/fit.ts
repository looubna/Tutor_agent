/**
 * Does every page of a deck actually fill its page — and stay inside it?
 *
 * The renderer cannot answer this. `.slide` is a fixed 4:3 box with
 * `overflow:hidden`, so a page with too much on it is silently sliced at the
 * edge, and a page with too little simply ends halfway down. Neither leaves a
 * trace: the HTML is valid, the schema passes, the PDF opens. The only way to
 * know is to lay the page out and measure it.
 *
 * So this module does not parse anything. It renders the deck, opens it in the
 * same headless Chrome that prints the PDF, and asks the browser for two
 * numbers per page:
 *
 *     overflow  how far the content runs past the bottom edge, in px
 *     fill      how much of the page's usable height the content reaches
 *
 * `fill` is measured from the bottom of the lowest painted element, not from
 * the sum of the children — a column with `justify-content:space-between`
 * covers the page even though its boxes are small, and a stack of three cards
 * pinned to the top does not, even though the two have the same total height.
 * What we care about is whether the page *looks* finished, and that is where
 * the ink stops.
 */

import { execFile } from "node:child_process";
import { mkdtemp, rm, writeFile } from "node:fs/promises";
import { tmpdir } from "node:os";
import { join } from "node:path";
import { promisify } from "node:util";

import type { Worksheet } from "./boxes";
import { render, forFileSystem } from "./render";

const run = promisify(execFile);

const CHROME = process.env.CHROME_PATH
  ?? "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome";

/** A page is a failure below this much ink. Above `CRAMPED` it is a warning. */
export const EMPTY = 0.55;
export const CRAMPED = 0.92;

export type PageFit = {
  /** `s7`, or `cover` / `solutions` / `extra` for the pages we generate. */
  id: string;
  /** 1-based, as printed in the footer. */
  page: number;
  /** Pixels of content past the bottom edge. Anything above 1 is a fault. */
  overflow: number;
  /** 0–1. How far down the page the ink reaches. */
  fill: number;
};

export type FitReport = {
  pages: PageFit[];
  problems: string[];
};

/**
 * The script that does the measuring.
 *
 * It has to run *inside* the page, because none of this is knowable from
 * outside: `getBoundingClientRect` needs a layout, and a layout needs the
 * fonts, the photographs and the grid to have resolved.
 *
 * Headless Chrome has no way to evaluate an expression and hand back the
 * result — `--dump-dom` prints the DOM and that is all. So the script writes
 * its answer *into* the DOM, inside a marker, and we read it out of the dump.
 * Round-about, but it needs no debugging port and no extra dependency, which
 * is the same trade `paper-pdf.ts` already makes by shelling out to Chrome.
 */
const MEASURE = `(() => {
  const out = [];
  document.querySelectorAll('.slide').forEach((slide, i) => {
    const box = slide.getBoundingClientRect();
    const body = slide.querySelector('.body');
    const foot = slide.querySelector('.pg');

    // The usable band: below the header, above the page number.
    const top = body ? body.getBoundingClientRect().top : box.top;
    const bottom = foot ? foot.getBoundingClientRect().top : box.bottom;
    const room = Math.max(1, bottom - top);

    // The lowest ink in the body. Empty and hidden elements are skipped: a
    // wrapper stretched by flex would otherwise report a full page.
    let low = top;
    if (body) body.querySelectorAll('*').forEach((el) => {
      const r = el.getBoundingClientRect();
      if (r.height < 1 || r.width < 1) return;
      const st = getComputedStyle(el);
      if (st.visibility === 'hidden' || st.display === 'none') return;
      if (r.bottom > low) low = r.bottom;
    });

    out.push({
      id: slide.id || ('slide-' + (i + 1)),
      page: i + 1,
      overflow: Math.max(0, Math.round(slide.scrollHeight - slide.clientHeight)),
      fill: Math.min(1, Math.max(0, (low - top) / room)),
    });
  });
  // The marker is glued together at runtime so that the literal never appears
  // in this script's own source, which Chrome also prints in the DOM dump.
  // Angle brackets are avoided for the same reason quotes are safe: --dump-dom
  // escapes < and > inside a text node, and nothing else.
  const tag = document.createElement('div');
  tag.id = 'fit-report';
  tag.textContent = 'ZFIT' + 'BEGIN' + JSON.stringify(out) + 'ZFIT' + 'END';
  document.body.appendChild(tag);
})()`;

/**
 * Render a deck, measure every page, and say what is wrong with it in the words
 * the fixing model will be handed.
 *
 * The deck is always rendered in its BEFORE form. The AFTER copy adds the
 * tutor's writing on top of the same boxes, so it is never emptier than the
 * paper it came from — measuring both would double the Chrome runs to catch a
 * fault that cannot exist.
 */
export async function measureFit(sheet: Worksheet, publicDir: string): Promise<FitReport> {
  const dir = await mkdtemp(join(tmpdir(), "zanoba-fit-"));
  try {
    const page = join(dir, "deck.html");
    const html = forFileSystem(render(sheet, { kind: "before" }), publicDir);
    await writeFile(page, html.replace("</body>", `<script>${MEASURE}</script></body>`));

    // `--virtual-time-budget` is what makes this repeatable: it tells Chrome to
    // fast-forward its clock until the page goes quiet, so the photographs have
    // loaded and laid out before the script runs. Without it an image-heavy
    // page measures as empty roughly half the time.
    const { stdout } = await run(
      CHROME,
      [
        "--headless", "--disable-gpu", "--no-sandbox",
        "--virtual-time-budget=10000",
        "--run-all-compositor-stages-before-draw",
        "--dump-dom", `file://${page}`,
      ],
      { maxBuffer: 64 * 1024 * 1024 },
    );

    const pages = parse(stdout);
    return { pages, problems: problemsFor(pages) };
  } finally {
    await rm(dir, { recursive: true, force: true });
  }
}

/** Read the measurement back out of the DOM dump. */
function parse(stdout: string): PageFit[] {
  const raw = stdout.match(/ZFITBEGIN(\[[\s\S]*?\])ZFITEND/)?.[1];
  if (!raw) {
    throw new Error(
      "Chrome returned no measurement. Check CHROME_PATH, or that the deck rendered at all.",
    );
  }
  return JSON.parse(raw.replace(/&quot;/g, '"').replace(/&amp;/g, "&"));
}

/**
 * Turn numbers into the sentence the fixing model gets.
 *
 * Deliberately plain, and always naming the slide id: stage 6 is handed these
 * strings verbatim, and "s14 is 38% full" is actionable in a way that a score
 * out of five is not.
 */
export function problemsFor(pages: PageFit[]): string[] {
  const problems: string[] = [];
  for (const p of pages) {
    if (p.id === "cover") continue; // the cover is ours, and it is meant to be spare
    if (p.overflow > 1) {
      problems.push(
        `${p.id} (page ${p.page}) — content runs ${p.overflow}px past the bottom and is being cut off. Move some of it to a new page, or use fewer items.`,
      );
    } else if (p.fill < EMPTY) {
      problems.push(
        `${p.id} (page ${p.page}) — only ${Math.round(p.fill * 100)}% full. Add rows, add a second block, or merge this page with its neighbour.`,
      );
    }
  }
  return problems;
}

/** Pages that are legal but tight. Worth seeing, never worth failing a build. */
export function warnings(pages: PageFit[]): string[] {
  return pages
    .filter((p) => p.overflow <= 1 && p.fill > CRAMPED)
    .map((p) => `${p.id} (page ${p.page}) — ${Math.round(p.fill * 100)}% full, close to the edge.`);
}
