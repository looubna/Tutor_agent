import { readFileSync } from "node:fs";
import { join } from "node:path";

import { answerKey, ICON_URL_BASE, type PublicWorksheet, type Worksheet, type Block, type PublicBlock, type Slide, type PublicSlide } from "./boxes";
import { byBox, settled, type Op } from "./ops";

/**
 * The maker: deck JSON in, one printable HTML document out.
 *
 * The same function draws both versions. BEFORE is the stripped deck with no
 * ops; AFTER is the full deck with the tutor's marks replayed onto it and the
 * Lösungen page appended. Nothing about the layout differs, because it is meant
 * to be the *same paper* — a parent putting the two side by side should see one
 * document that got used.
 *
 * Pages are 4:3, not A4. A deck is looked at on a shared screen for fifty
 * minutes and printed afterwards; A4 landscape is a compromise that serves
 * neither, and the reference deck this format was drawn from is 4:3.
 */

export type RenderMode =
  | { kind: "before" }
  | { kind: "after"; ops: Op[]; studentName?: string; extraPractice?: string[] };

const esc = (s: string) =>
  s.replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;").replace(/"/g, "&quot;");

/** `___` becomes a ruled space to write on, or the word written into it. */
const gap = (filled?: string) =>
  filled ? `<span class="gap filled">${esc(filled)}</span>` : `<span class="gap"></span>`;

/** Split a prompt on its gaps and put a line — or the solution — in each one. */
const withGaps = (text: string, filled?: string) =>
  text.split("___").map(esc).join(gap(filled));

/**
 * The tutor's hand, resolved against one page.
 *
 * A `fill` names a gap by number and a `circle` names a printed thing by
 * number, both in reading order down the page. Those two numberings are the
 * contract between the tutor and this file — the tutor says "fill gap 3" and
 * the blank the student was looking at is the one that gets written in — so
 * they are counted here as the page is drawn, block by block, in the order the
 * blocks are printed. The agent counts them the same way in
 * `apps/agent/src/zanoba_agent/live/paper.py`; change one and you must change
 * the other.
 *
 * A gap is whatever is visibly blank: every numbered row, and anything else
 * whose text carries `___`. Never "whatever has an answer field" — the
 * student's copy has every answer deleted from it, so counting that way would
 * put the tutor's marks in different blanks than the ones they aimed at.
 *
 * Every block that puts something separable on the page is ringable, not just
 * the language shapes: a maths worksheet is rules, tables and numbered
 * exercises, and while those counted for nothing there was literally nothing on
 * such a page for the tutor to point at while it explained.
 */
type Pen = {
  fills: Map<number, string>;
  rings: Map<number, string>;
  /** Lines the tutor wrote about a particular thing, by that thing's number. */
  notes: Map<number, string[]>;
  /** Cursors, consumed as the page is drawn. */
  gap: number;
  target: number;
};

function pen(ops: Op[] | undefined): Pen {
  const fills = new Map<number, string>();
  const rings = new Map<number, string>();
  const notes = new Map<number, string[]>();
  for (const op of settled(ops ?? [])) {
    if (op.op === "fill") fills.set(op.row, op.text);
    if (op.op === "circle") for (const w of op.words) rings.set(w, op.colour);
    if (op.op === "write" && op.on.at !== null && op.on.at !== undefined) {
      notes.set(op.on.at, [...(notes.get(op.on.at) ?? []), op.text]);
    }
  }
  return { fills, rings, notes, gap: 0, target: 0 };
}

/** The next gap on the page, and what the tutor wrote in it, if anything. */
const inked = (p: Pen) => p.fills.get(p.gap++);

/** The next printed thing, and the colour of the ring round it, if any. */
const ringed = (p: Pen) => {
  const colour = p.rings.get(p.target++);
  return colour ? ` ring ${colour}` : "";
};

/**
 * The tutor's writing about the thing just drawn, drawn against it.
 *
 * Everything the tutor wrote used to land in one block at the foot of the page,
 * so an explanation of the third exercise appeared four inches below the third
 * exercise, under everything else. A line that names what it is about belongs
 * next to it. `since` is the target number returned before it was consumed.
 */
const noteFor = (p: Pen, since: number) => {
  const lines = p.notes.get(since);
  return lines?.length
    ? `<span class="note-hand">${lines.map((l) => `<i>${esc(l)}</i>`).join("")}</span>`
    : "";
};

/**
 * Our icons are drawn in `currentColor`, so they have to become part of the
 * document to take the page's ink.
 *
 * Neither of the easier routes works. An `<img>` renders the file in whatever
 * colour it was drawn in — `currentColor` resolves to black inside a standalone
 * image, so every icon comes out black on a violet page. A CSS mask does tint,
 * but masks are CORS-checked and a printed page is loaded from `file://`, which
 * is an opaque origin: Chrome drops the mask and paints the element with no
 * mask at all, and the icon prints as a solid violet square.
 *
 * Inlining sidesteps both, costs one small file read per distinct icon, and
 * behaves identically over HTTP and from disk.
 */
const ICON_DIR = join(process.cwd(), "public", "materials", "german", "a1-1", "icons");
const inlined = new Map<string, string | null>();

function iconSvg(stem: string): string | null {
  if (!inlined.has(stem)) {
    try {
      // The `<style>` block every icon carries is hoisted into the deck's own
      // stylesheet instead. Thirty-five copies of one rule, injected into the
      // document at global scope, is a collision waiting for the first icon
      // that defines `.a` differently.
      const raw = readFileSync(join(ICON_DIR, `${stem}.svg`), "utf8")
        .replace(/<style>[\s\S]*?<\/style>/g, "")
        .replace("<svg ", '<svg class="ico" aria-hidden="true" focusable="false" ');
      inlined.set(stem, raw);
    } catch {
      inlined.set(stem, null);
    }
  }
  return inlined.get(stem) ?? null;
}

/**
 * How big the big thing on a card is set.
 *
 * `lead` holds a letter on an alphabet page and a whole sentence on a page of
 * phrases — the reference deck does both — and one font size cannot serve them.
 * Measured here rather than left to CSS, which cannot count characters.
 */
function leadSize(text: string): string {
  if (text.length <= 4) return "glyph";
  return text.length <= 14 ? "word" : "phrase";
}

/** A drawn icon takes the page's ink; a bitmap is a bitmap and is left alone. */
function pictureTag(item: { icon?: string; img?: string }, base: string): string {
  if (item.img) return `<img class="pic" src="${esc(item.img)}" alt="" aria-hidden="true">`;
  if (!item.icon) return "";
  // The stem is `^[a-z0-9-]+$` by schema, so it cannot climb out of ICON_DIR.
  return iconSvg(item.icon)
    ?? `<img class="ico" src="${base}/${esc(item.icon)}.svg" alt="" aria-hidden="true">`;
}

/**
 * What kind of word a vocabulary row holds, so the page can colour it.
 *
 * The reference deck tints its Wortschatz rows by word type, and it is the one
 * page in the deck where colour carries meaning rather than rhythm. That makes
 * it the one place a tint may not alternate — so it is worked out here, from
 * the term itself, and never offered to the writer as a field. A model given
 * the choice will colour by mood.
 *
 * Only the article is trusted, because only the article is checked against the
 * word file. Everything else falls back to `other`, which is deliberately the
 * commonest outcome: a wrong colour teaches a wrong fact, and no colour
 * teaches nothing.
 */
function wordKind(term: string): "m" | "f" | "n" | "other" {
  const article = term.trim().split(/\s+/)[0]?.toLowerCase();
  return article === "der" ? "m" : article === "die" ? "f" : article === "das" ? "n" : "other";
}

/* ── blocks ──────────────────────────────────────────────────────────────── */

function renderBlock(block: Block | PublicBlock, base: string, ink: Pen): string {
  switch (block.kind) {
    case "cards": {
      const items = block.items as { lead?: string; label?: string; caption?: string;
        answer?: string; icon?: string; img?: string }[];
      // A card carrying a photograph is a different shape from a card carrying
      // a word: the picture runs to the card's edges and the text sits under
      // it on a band, which is how the reference deck's word cards are built.
      // The class is set here rather than guessed in CSS because `:has()` on a
      // print stylesheet is one more thing that can silently not apply.
      return `<div class="cards c${block.cols}">${items.map((c, i) => {
        const ring = ringed(ink);
        // A card is a gap only when its label shows one. The card itself is
        // always something a ring can go round, so the ring is taken first.
        const written = c.label?.includes("___") ? inked(ink) : undefined;
        return `<div class="card${c.img ? " shot" : ""}${ring}">
        ${block.numbered ? `<span class="n">${i + 1}</span>` : ""}
        ${c.lead ? `<span class="lead ${leadSize(c.lead)}">${esc(c.lead)}</span>` : pictureTag(c, base)}
        ${c.label || c.caption ? `<span class="say">
          ${c.label ? `<span class="label">${withGaps(c.label, c.answer ?? written)}</span>` : ""}
          ${c.caption ? `<span class="cap">${esc(c.caption)}</span>` : ""}
        </span>` : ""}
      </div>`;
      }).join("")}</div>`;
    }

    case "bubbles": {
      const turns = block.turns as { side: "l" | "r"; text: string; answer?: string }[];
      return `<div class="bubbles">${turns.map((t, i) => {
        const ring = ringed(ink);
        const written = t.text.includes("___") ? inked(ink) : undefined;
        return `<div class="turn ${t.side}">
        ${block.numbered && t.side === "l" ? `<span class="n">${Math.floor(i / 2) + 1}</span>` : ""}
        <div class="bub${ring}">${withGaps(t.text, t.answer ?? written)}</div>
      </div>`;
      }).join("")}</div>`;
    }

    case "rows":
      return `<div class="stack">${block.items.map((r) => {
        const n = ink.target;
        const ring = ringed(ink);
        return `<div class="srow${ring}">
        <span class="head">${esc(r.head)}</span>
        <span class="body">${esc(r.body)}</span>
        ${noteFor(ink, n)}
      </div>`;
      }).join("")}</div>`;

    case "hero":
      return `<div class="hero${ringed(ink)}">
        ${block.glyph ? `<span class="glyph">${esc(block.glyph)}</span>` : pictureTag(block, base)}
        <span class="label">${esc(block.label)}</span>
        ${block.sub ? `<span class="cap">${esc(block.sub)}</span>` : ""}
      </div>`;

    case "list":
      return `<div class="list l${block.cols}">${block.items.map((it) => `<p class="li ${wordKind(it.term)}${ringed(ink)}">
        <span class="term">${esc(it.term)}</span>
        ${it.gloss ? `<span class="gloss">${esc(it.gloss)}</span>` : ""}
      </p>`).join("")}</div>`;

    case "lines":
      return `<div class="rule ${block.tone} r${block.cols}">
        ${block.label ? `<span class="rlabel">${esc(block.label)}</span>` : ""}
        <div class="ruled">${Array.from({ length: block.count }, (_, i) =>
          `<i>${block.numbered ? `<b>${i + 1}</b>` : ""}</i>`).join("")}</div>
      </div>`;

    case "bins":
      return `<div class="bins">${block.items.map((b) => `<div class="bin">
        <span class="rlabel">${esc(b.label)}</span>
        <div class="ruled">${"<i></i>".repeat(b.lines)}</div>
      </div>`).join("")}</div>`;

    case "dialogue": {
      const lines = block.lines as { who: string; says: string; answer?: string }[];
      return `${block.scene ? `<p class="scene">${esc(block.scene)}</p>` : ""}
        <div class="dlg">${lines.map((l) => {
        const blank = l.says.includes("___");
        const written = blank ? inked(ink) : undefined;
        return `<p class="line${ringed(ink)}">
          <span class="who">${esc(l.who)}:</span>
          <span class="says">${blank ? withGaps(l.says, l.answer ?? written)
            : l.answer !== undefined ? gap(l.answer) : esc(l.says)}</span>
        </p>`;
      }).join("")}</div>`;
    }

    case "table":
      return `<div class="scroll"><table class="grid">
        <thead><tr>${block.head.map((h) => `<th>${esc(h)}</th>`).join("")}</tr></thead>
        <tbody>${block.rows.map((row) =>
          `<tr class="${ringed(ink).trim()}">${row.map((c) =>
            `<td>${esc(c)}</td>`).join("")}</tr>`).join("")}</tbody>
      </table>${block.caption ? `<p class="cap">${esc(block.caption)}</p>` : ""}</div>`;

    case "exercise": {
      const rows = block.rows as { prompt: string; hint?: string; answer?: string }[];
      return `<ol class="task">${rows.map((r, i) => {
        // Consumed for every row, answered or not: the cursor has to advance
        // the same way on the blank sheet and on the marked one, or a ring
        // further down the page lands on the wrong word.
        const written = inked(ink);
        const n = ink.target;
        const ring = ringed(ink);
        return `<li class="${ring.trim()}">
        <span class="n">${i + 1}</span>
        <span class="q">${withGaps(r.prompt, r.answer ?? written)}
          ${r.hint ? `<span class="hint">${esc(r.hint)}</span>` : ""}</span>
        ${noteFor(ink, n)}
      </li>`;
      }).join("")}</ol>`;
    }

    case "choose": {
      const rows = block.rows as { prompt: string; options: string[]; answer?: string }[];
      return `<ol class="task">${rows.map((r, i) => {
        // The row's gap first, then its options: the same order the tutor's
        // side counts them in.
        const chosen = r.answer ?? inked(ink);
        return `<li>
        <span class="n">${i + 1}</span>
        <span class="q">${withGaps(r.prompt)}</span>
        <span class="opts">${r.options.map((o) =>
          `<span class="opt${chosen === o ? " picked" : ""}${ringed(ink)}">${esc(o)}</span>`).join("")}</span>
      </li>`;
      }).join("")}</ol>`;
    }

    case "build": {
      const rows = block.rows as { parts: string[]; answer?: string }[];
      return `<ol class="task build">${rows.map((r, i) => {
        const written = r.answer ?? inked(ink);
        const ring = ringed(ink);
        return `<li class="${ring.trim()}">
        <span class="n">${i + 1}</span>
        <span class="parts">${r.parts.map((part) => `<span class="part">${esc(part)}</span>`).join("")}</span>
        ${written ? `<span class="sol">${esc(written)}</span>` : `<span class="writeline"></span>`}
      </li>`;
      }).join("")}</ol>`;
    }

    case "goals":
      return `<ul class="goals">${block.items.map((t, i) => `<li class="${ringed(ink).trim()}">
        <span class="letter">${String.fromCharCode(65 + i)}</span>
        <span>${esc(t)}</span>
      </li>`).join("")}</ul>`;

    case "photo":
      return `<figure class="photo ${block.shape}"><img src="${esc(block.src)}" alt="${esc(block.alt)}">
        ${block.credit ? `<figcaption>${esc(block.credit)}</figcaption>` : ""}</figure>`;
  }
}

/* ── slides ──────────────────────────────────────────────────────────────── */

/**
 * The lines the tutor wrote, put where they were aimed.
 *
 * `below` is the common one: working under the page, the way a teacher writes
 * beneath the exercise they have just done. `beside` goes in the margin, for a
 * word of grammar next to the thing it explains. `over` lies across the page,
 * for the one line that has to interrupt.
 */
function marks(ops: Op[] | undefined, where: "below" | "beside" | "over"): string {
  const written = (ops ?? [])
    .filter((o) => o.op === "write" && o.on.where === where
                   && (o.on.at === null || o.on.at === undefined))
    .map((o) => `<p class="hand ${(o as { style: string }).style}">${esc((o as { text: string }).text)}</p>`)
    .join("");
  return written ? `<div class="marks ${where}">${written}</div>` : "";
}

function renderSlide(slide: Slide | PublicSlide, page: number, base: string, ops?: Op[]): string {
  // A ring with no words named is a ring round the whole page.
  const wholePage = settled(ops ?? []).some((o) => o.op === "circle" && !o.words.length);
  const ink = pen(ops);
  const blocks = slide.blocks as (Block | PublicBlock)[];
  return `<section class="slide t-${slide.tone}${wholePage ? " circled" : ""}${slide.tab ? " tabbed" : ""}" id="${esc(slide.id)}">
    ${slide.tab ? `<span class="tab">${esc(slide.tab)}</span>` : ""}
    <header class="head">
      <div class="titles">
        <h2>${esc(slide.title)}</h2>
        ${slide.subtitle ? `<p class="sub">${esc(slide.subtitle)}</p>` : ""}
      </div>
      <img class="mark" src="/brand/logo.png" alt="Zanoba">
    </header>
    <div class="body">${blocks.map((b) => renderBlock(b, base, ink)).join("")}
      ${marks(ops, "beside")}</div>
    ${slide.note ? `<aside class="note ${slide.note.tone}">
      ${slide.note.title ? `<b>${esc(slide.note.title)}</b>` : ""}
      <span>${esc(slide.note.text)}</span></aside>` : ""}
    ${marks(ops, "below")}
    ${marks(ops, "over")}
    <footer class="pg"><span>${page}</span><span class="sid">${esc(slide.id)}</span></footer>
  </section>`;
}

export function render(
  sheet: Worksheet | PublicWorksheet,
  mode: RenderMode,
  iconBase = ICON_URL_BASE,
): string {
  const after = mode.kind === "after";
  const opsFor = after ? byBox(mode.ops) : new Map<string, Op[]>();
  const written = after ? mode.ops.filter((o) => o.op === "write" || o.op === "fill").length : 0;

  /**
   * The words the sheet says about itself: the cover labels, the answers page,
   * the practice page. Chrome, not content.
   *
   * These were written in German because German was the only course. The first
   * French maths sheet printed VOR DEM UNTERRICHT across its cover — the kind
   * of detail that tells a student the paper was not made for them.
   *
   * The language is read from `meta.sprache`, which the writer sets to the
   * language it wrote in. A sheet that does not say falls back to German, so
   * every deck that existed before this keeps the cover it had.
   */
  const CHROME = {
    de: { niveau: "Niveau", nummer: "Nummer", sprache: "Sprache",
          before: "Vor dem Unterricht", after: "Nach dem Unterricht", notes: "Notizen",
          keys: "Lösungen", keysSub: "Für die Lehrkraft und zur Selbstkontrolle.",
          page: "S.", more: "Noch etwas Übung", moreSub: "Bis zum nächsten Mal." },
    fr: { niveau: "Niveau", nummer: "Numéro", sprache: "Langue",
          before: "Avant le cours", after: "Après le cours", notes: "notes",
          keys: "Corrigés", keysSub: "Pour le professeur et pour se corriger seul.",
          page: "p.", more: "Encore un peu d'entraînement", moreSub: "D'ici la prochaine fois." },
    en: { niveau: "Level", nummer: "Number", sprache: "Language",
          before: "Before the lesson", after: "After the lesson", notes: "notes",
          keys: "Answers", keysSub: "For the teacher, and for checking your own work.",
          page: "p.", more: "A little more practice", moreSub: "Until next time." },
  } as const;

  const spoken = (sheet.meta?.sprache ?? "").toLowerCase();
  const lang: keyof typeof CHROME =
    spoken.startsWith("fran") ? "fr" : spoken.startsWith("eng") ? "en" : "de";
  const say = CHROME[lang];

  const slides = sheet.slides as (Slide | PublicSlide)[];
  const body = slides
    .map((s, i) => renderSlide(s, i + 2, iconBase, opsFor.get(s.id)))
    .join("\n");

  const meta = sheet.meta ?? {};
  const cell = (label: string, value?: string) =>
    value ? `<div><span>${esc(label)}</span><b>${esc(value)}</b></div>` : "";

  const cover = `<section class="slide cover${sheet.cover ? " shot" : ""}" id="cover">
    <span class="blob one"></span><span class="blob two"></span>
    ${sheet.cover ? `<img class="face" src="${esc(sheet.cover.src)}" alt="${esc(sheet.cover.alt)}">` : ""}
    <img class="logo" src="/brand/logo.png" alt="Zanoba">
    ${sheet.subtitle ? `<p class="crumb">${esc(sheet.subtitle)}</p>` : ""}
    <h1>${esc(sheet.title)}</h1>
    <div class="meta">
      ${cell(say.niveau, meta.niveau)}
      ${cell(say.nummer, meta.nummer)}
      ${cell(say.sprache, meta.sprache)}
      ${cell(after ? say.after : say.before,
             after ? (mode.studentName ?? `${written} ${say.notes}`) : `v${sheet.version}`)}
    </div>
    <span class="dom">zanoba.com</span>
  </section>`;

  /**
   * The Lösungen page, derived rather than written, and only ever on the AFTER
   * copy. An answer key typed out by the writer is a second copy of the truth
   * that drifts from the first the moment a card is reworded — and one built on
   * the student's deck would be a leak with a title.
   */
  const key = after ? answerKey(sheet as Worksheet) : [];
  const solutions = key.length
    ? `<section class="slide" id="loesungen">
        <header class="head">
          <div class="titles"><h2>${say.keys}</h2>
            <p class="sub">${say.keysSub}</p></div>
          <img class="mark" src="/brand/logo.png" alt="Zanoba">
        </header>
        <div class="body"><div class="keys">${key.map((k) =>
          `<p><b>${say.page}&nbsp;${k.page}:</b> ${k.answers.map(esc).join("; ")}</p>`).join("")}</div></div>
        <footer class="pg"><span>${slides.length + 2}</span></footer>
      </section>`
    : "";

  const extra =
    after && mode.extraPractice?.length
      ? `<section class="slide" id="extra">
          <header class="head">
            <div class="titles"><h2>${say.more}</h2>
              <p class="sub">${say.moreSub}</p></div>
            <img class="mark" src="/brand/logo.png" alt="Zanoba">
          </header>
          <div class="body"><ol class="task">${mode.extraPractice.map((p, i) =>
            `<li><span class="n">${i + 1}</span><span class="q">${withGaps(p)}</span></li>`).join("")}</ol></div>
          <footer class="pg"><span>${slides.length + (key.length ? 3 : 2)}</span></footer>
        </section>`
      : "";

  return `<!doctype html>
<html lang="${lang}"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>${esc(sheet.title)}</title>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Caveat:wght@600&family=Karla:wght@400;500;600;700;800&family=JetBrains+Mono:wght@400;600&display=swap">
<style>${CSS}</style></head>
<body class="${after ? "after" : "before"}">
<div class="deck">
${cover}
${body}
${solutions}
${extra}
</div>
</body></html>`;
}

/**
 * Point every picture at the file system instead of at the web root.
 *
 * Printing loads the page from a temporary file, so `/materials/…` resolves to
 * the root of the disk and every icon 404s. An `<img>` that fails is merely
 * missing; a *mask* that fails is worse, because CSS then paints the element
 * with no mask at all and a tinted icon comes out as a solid violet square.
 * That is the bug this function exists to prevent, and why it rewrites the
 * urls inside style attributes as well as `src`.
 */
export function forFileSystem(html: string, publicDir: string): string {
  return html
    .replaceAll('src="/', `src="file://${publicDir}/`)
    .replaceAll("url('/", `url('file://${publicDir}/`);
}

/**
 * 4:3 pages, and two tints that alternate down every grid.
 *
 * The alternation is applied here rather than chosen per card, for the same
 * reason the illustration house style lives in the tool and not the prompt: a
 * writer given the choice will make a page of five lilac cards and one cream
 * one by the twelfth slide, and the deck stops looking like one course.
 */
const CSS = `
:root{
  --page:#fff;--paper:#f4f2f7;--ink:#1f1147;--muted:#77747f;--line:#e9e5f2;
  --brand:#7b3fe4;--deep:#3b1c8c;--cover:#45209e;--lift:#5a2bc9;
  --lilac:#f2edfd;--lilac-2:#e4dafb;--cream:#fdf2e0;--gold:#a8791c;
  --hand:#c23b3b;--ok:#1f8a5f;
  /* Vocabulary tints. Three genders and a neutral for everything else, kept
     pale enough that black text stays comfortably readable on all four. */
  --wm:#e6ecfb;--wm-edge:#7d96e0;
  --wf:#fbe6ec;--wf-edge:#dd8aa6;
  --wn:#e4f2e9;--wn-edge:#71b189;
  --wo:#f4f2f7;
  --pw:254mm;--ph:190.5mm;--pad:15mm}
/* No dark palette. This document is printed, and it is looked at on a shared
   screen during class: which of the two people in that call has dark mode on
   is not something the paper should depend on. The old rule here also only
   half-worked — @media print reset the background and left the cards dark. */
*{box-sizing:border-box}
body{margin:0;background:var(--paper);color:var(--ink);
  font-family:Karla,system-ui,-apple-system,sans-serif;font-size:15px;line-height:1.5}
@page{size:254mm 190.5mm;margin:0}
.deck{display:flex;flex-direction:column;align-items:center;gap:10mm;padding:10mm 0}

/* ── the page ─────────────────────────────────────────────────────────── */
.slide{width:min(100%,var(--pw));aspect-ratio:4/3;background:var(--page);
  padding:var(--pad) var(--pad) 9mm;display:flex;flex-direction:column;gap:6mm;
  position:relative;overflow:hidden;
  box-shadow:0 1px 2px rgba(31,17,71,.05),0 14px 36px -24px rgba(31,17,71,.35)}
.head{display:flex;justify-content:space-between;align-items:flex-start;gap:8mm;flex:none}
.head h2{margin:0;font-size:2rem;font-weight:800;letter-spacing:-.02em;line-height:1.1;
  text-wrap:balance}
.sub{margin:.35rem 0 0;font-size:.86rem;color:var(--muted)}
.mark{height:34px;width:auto;flex:none}
.body{flex:1;display:flex;flex-direction:column;gap:5mm;min-height:0}
.pg{margin-top:auto;display:flex;justify-content:space-between;align-items:flex-end;
  font-family:"JetBrains Mono",monospace;font-size:.62rem;color:var(--muted);flex:none}
.sid{opacity:.35}
.circled{outline:2.5px solid var(--hand);outline-offset:-6px}

/* ── cards ────────────────────────────────────────────────────────────── */
.cards{display:grid;gap:3.5mm}
/* Rows share the height the page has left rather than each being as tall as
   its contents. A grid of six photographs at a fixed 4:3 ran 44px off the
   bottom; the same grid of six icons stopped two thirds of the way down. One
   rule fixes both, and it is the same rule the ruled lines use. */
.body>.cards{flex:1;min-height:0;grid-auto-rows:minmax(22mm,1fr)}
.cards:has(.n){padding-top:5mm}
.c2{grid-template-columns:repeat(2,1fr)}.c3{grid-template-columns:repeat(3,1fr)}
.c4{grid-template-columns:repeat(4,1fr)}.c5{grid-template-columns:repeat(5,1fr)}
.card{border-radius:9px;padding:5mm 4mm;display:flex;flex-direction:column;
  align-items:center;justify-content:center;gap:.4rem;text-align:center;position:relative;
  min-height:24mm;background:var(--lilac)}
.card:nth-child(even){background:var(--cream)}
.card .n{position:absolute;top:-4mm;left:-2mm;width:8mm;height:8mm;border-radius:50%;
  background:var(--brand);color:#fff;font-size:.78rem;font-weight:700;
  display:flex;align-items:center;justify-content:center}
.lead{font-weight:800;color:var(--deep);line-height:1.05;letter-spacing:-.02em;
  text-wrap:balance}
.lead.glyph{font-size:2.6rem;line-height:1}
.lead.word{font-size:1.5rem}
.lead.phrase{font-size:1.05rem;color:var(--brand);letter-spacing:0}
.card .label{font-weight:700;font-size:1.05rem}
.cap{font-size:.78rem;color:var(--muted)}
.ico{width:14mm;height:14mm;color:var(--brand);display:block}
/* Hoisted out of every icon file — the soft fill our drawings use. */
.ico .a{fill:currentColor;fill-opacity:.12}
.pic{width:100%;max-width:26mm;aspect-ratio:1;object-fit:contain}

/* ── bubbles ──────────────────────────────────────────────────────────── */
.bubbles{display:flex;flex-direction:column;gap:3mm}
.turn{display:grid;grid-template-columns:9mm 1fr;align-items:center;gap:3mm}
.bub{grid-column:2;width:78%;border-radius:9px;padding:5mm;text-align:center;
  font-weight:600;font-size:1.05rem}
.turn.r .bub{justify-self:end}
.turn.l .bub{background:var(--page);border:1px solid var(--line)}
.turn.r .bub{background:var(--lilac)}
/* The tail is what makes a rounded rectangle read as somebody speaking. It
   points back towards whoever is talking: left-hand turns point left, right
   point right. Drawn with a rotated square rather than a border triangle so it
   can carry the same border and background as the bubble it belongs to. */
.bub{position:relative}
.turn .bub::after{content:"";position:absolute;width:4mm;height:4mm;bottom:-2.1mm;
  background:inherit;transform:rotate(45deg)}
.turn.l .bub::after{left:9mm;border-right:1px solid var(--line);
  border-bottom:1px solid var(--line)}
.turn.r .bub::after{right:9mm}
.turn .n{width:9mm;height:9mm;border-radius:50%;background:var(--brand);color:#fff;flex:none;
  display:flex;align-items:center;justify-content:center;font-weight:700;font-size:.85rem}

/* ── stacked rows, hero, list ─────────────────────────────────────────── */
.body:has(.hero+.stack),.body:has(.stack+.hero){flex-direction:row;align-items:center}
.body:has(.hero+.stack)>*,.body:has(.stack+.hero)>*{flex:1;min-width:0}
.stack{display:flex;flex-direction:column;gap:3mm;justify-content:center}
.srow{border:1px solid var(--line);border-radius:8px;padding:4mm 5mm;background:var(--page);
  display:flex;flex-direction:column;gap:.15rem}
.srow .head{display:block;font-size:.76rem;font-weight:700;color:var(--brand);
  letter-spacing:.02em}
.srow .body{display:block;flex:none;font-size:1rem}
.hero{background:var(--lilac);border-radius:10px;padding:8mm;display:flex;
  flex-direction:column;align-items:center;justify-content:center;gap:.5rem;text-align:center}
.glyph{font-size:3.6rem;font-weight:800;color:var(--deep);line-height:1;
  letter-spacing:-.02em;text-wrap:balance}
.hero .label{font-weight:700;color:var(--brand);font-size:1.1rem}
.list{display:grid;gap:1.2mm 8mm}
.l1{grid-template-columns:1fr}.l2{grid-template-columns:1fr 1fr}
.l3{grid-template-columns:repeat(3,1fr)}
.li{margin:0;padding:2.4mm 4mm;border-radius:6px;background:var(--wo);
  display:flex;gap:.6rem;align-items:baseline;font-size:.94rem;
  border-left:2.5mm solid transparent}
/* The one place in the deck where a tint means something rather than keeping a
   rhythm: the vocabulary page is colour-coded by gender, so a learner can see
   the three groups without reading the articles. Set from the term by
   wordKind(), never chosen by the writer — which is why this replaces the
   even/odd alternation here instead of sitting on top of it. */
.li.m{background:var(--wm);border-left-color:var(--wm-edge)}
.li.f{background:var(--wf);border-left-color:var(--wf-edge)}
.li.n{background:var(--wn);border-left-color:var(--wn-edge)}
.term{font-weight:700}
.gloss{color:var(--muted);font-size:.88rem}

/* ── the word printed sideways down the edge ──────────────────────────── */
.tabbed{padding-left:calc(var(--pad) + 9mm)}
.tab{position:absolute;left:0;top:0;bottom:0;width:9mm;background:var(--brand);
  color:#fff;display:flex;align-items:center;justify-content:center;
  writing-mode:vertical-rl;transform:rotate(180deg);
  font-size:.76rem;font-weight:700;letter-spacing:.08em;z-index:2}

/* ── writing space ────────────────────────────────────────────────────── */
.rule{display:flex;flex-direction:column;gap:2mm}
.body>.rule:only-child,.rule.board{flex:1;min-height:0}
.rule.board{border:2px dashed var(--brand);border-radius:9px;background:var(--lilac);
  padding:5mm 6mm;flex:1}
.rlabel{font-size:.78rem;font-weight:700;color:var(--brand)}
/* Rows share whatever height the page has left, rather than each taking a
   fixed 7mm. Fixed rows are wrong in both directions: nine of them overflowed
   the Notizen page by a few millimetres and the last rule printed half-cut,
   while six left a white slab at the foot. A 1fr row with a floor keeps them
   evenly spaced, always reaching the bottom, and never thinner than a hand
   can write between. */
.ruled{display:grid;gap:0;padding-top:2mm;flex:1;min-height:0;
  grid-auto-rows:minmax(9mm,1fr)}
.r2 .ruled{grid-template-columns:1fr 1fr;column-gap:8mm}
.ruled i{display:flex;align-items:flex-end;gap:3mm;border-bottom:1.5px solid var(--lilac-2);
  min-height:9mm}
.ruled b{font-family:"JetBrains Mono",monospace;font-size:.72rem;color:var(--brand);
  font-weight:600;padding-bottom:.5mm}
.bins{display:grid;grid-template-columns:1fr 1fr;gap:5mm}
.bin{background:var(--lilac);border-radius:9px;padding:5mm 6mm;text-align:center}
.bin .rlabel{display:block;margin-bottom:2mm;font-size:.95rem}

/* ── dialogue, table ──────────────────────────────────────────────────── */
.scene{margin:0;font-size:.72rem;letter-spacing:.08em;text-transform:uppercase;
  font-weight:700;color:var(--muted)}
.dlg{background:var(--page);border:1px solid var(--line);border-radius:9px;padding:5mm 6mm;
  display:flex;flex-direction:column;gap:2.4mm}
.line{margin:0;display:flex;gap:3mm;align-items:baseline}
.who{font-weight:700;color:var(--brand);min-width:22mm;flex:none}
.says{flex:1}
.grid{width:100%;border-collapse:collapse;font-size:.95rem}
.grid th{text-align:left;font-size:.7rem;letter-spacing:.06em;text-transform:uppercase;
  color:var(--brand);font-weight:700;padding:2.5mm 4mm;background:var(--lilac)}
.grid td{padding:2.5mm 4mm;border-bottom:1px solid var(--line)}
.scroll{overflow-x:auto}

/* ── tasks ────────────────────────────────────────────────────────────── */
.task{margin:0;padding:0;list-style:none;display:flex;flex-direction:column;gap:3mm}
.task li{display:flex;align-items:center;gap:3.5mm}
.task .n{width:8mm;height:8mm;border-radius:50%;background:var(--lilac-2);color:var(--deep);
  font-family:"JetBrains Mono",monospace;font-size:.75rem;font-weight:600;flex:none;
  display:flex;align-items:center;justify-content:center}
.task .q{flex:1;background:var(--lilac);border-radius:7px;padding:3.5mm 5mm;font-size:1rem}
.task li:nth-child(even) .q,.task li:nth-child(even) .parts{background:var(--cream)}
.hint{display:block;font-size:.76rem;color:var(--muted);font-style:italic}
.opts{display:inline-flex;gap:2mm;flex:none}
.opt{border:1.5px solid var(--line);border-radius:999px;padding:1mm 4mm;font-weight:600;
  font-size:.9rem}
.opt.picked{border-color:var(--hand);color:var(--hand)}
.build li{align-items:center}
.parts{flex:1;background:var(--lilac);border-radius:7px;padding:3.5mm 5mm;display:flex;
  flex-wrap:wrap;gap:2mm}
.part{font-size:.95rem}.part+.part::before{content:"–";color:var(--muted);margin-right:2mm}
.build li{align-items:stretch}
.writeline{flex:1;border-bottom:1.5px solid var(--lilac-2);align-self:stretch}
.sol{flex:1;font-family:Caveat,cursive;font-size:1.35rem;color:var(--hand);
  border-bottom:1.5px solid var(--hand);line-height:1.1}
.gap{display:inline-block;min-width:22mm;border-bottom:1.5px solid var(--brand);
  height:1em;vertical-align:-.14em;margin:0 1mm}
.gap.filled{border-bottom-color:var(--hand);font-family:Caveat,cursive;font-size:1.3rem;
  color:var(--hand);height:auto;line-height:1.1;text-align:center}

/* ── goals ────────────────────────────────────────────────────────────── */
.goals{margin:0;padding:0;list-style:none;display:flex;flex-direction:column;gap:3mm}
.goals li{display:flex;align-items:center;gap:5mm;border-radius:9px;padding:5mm 6mm;
  background:var(--lilac);font-size:1.05rem}
.goals li:nth-child(even){background:var(--cream)}
.letter{width:9mm;height:9mm;border-radius:50%;background:var(--brand);color:#fff;flex:none;
  display:flex;align-items:center;justify-content:center;font-size:.8rem;font-weight:700}

/* ── photographs ──────────────────────────────────────────────────────── */
.photo{margin:0;flex:1;display:flex;flex-direction:column;gap:2mm;min-height:0}
.photo img{width:100%;flex:1;object-fit:cover;border-radius:9px;min-height:0}
.photo figcaption{font-size:.68rem;color:var(--muted)}

/* A panel takes one side of the page floor to ceiling and the talking happens
   beside it. The body has to become a row for that, and only the photograph is
   allowed to say so — a page with two blocks that both want the full width
   would otherwise squeeze both. */
.body:has(>.photo.panel){flex-direction:row;align-items:stretch;gap:7mm}
.body>.photo.panel{flex:0 0 42%}
.body:has(>.photo.panel)>*:not(.photo){flex:1;min-width:0;display:flex;
  flex-direction:column;justify-content:center;gap:4mm}

/* A strip sets the scene above the work rather than beside it. Fixed height,
   because a band that grows is just a plate. */
.body>.photo.strip{flex:none;height:52mm}
.body>.photo.strip img{flex:none;height:100%}

/* ── a card built round a photograph ──────────────────────────────────── */
/* The picture reaches the card's edges and the words sit on a band under it.
   The old shape — a small centred image with a caption floating below it —
   was drawn for a 14mm icon and makes a photograph look like a stamp. */
.card.shot{padding:0;overflow:hidden;justify-content:flex-start;gap:0;min-height:0}
/* The photograph takes whatever the row has spare once the words underneath
   have theirs, so a card is never taller than its slot. A fixed aspect ratio
   here would fight the row height and win, which is what pushed page 7 off
   the bottom. */
.card.shot .pic{width:100%;max-width:none;flex:1;min-height:14mm;object-fit:cover;
  border-radius:0;display:block}
/* A fixed band under the picture, so that a card whose caption wraps to two
   lines does not steal the height from its neighbour's photograph. Without
   this the six cards on a vocabulary page all have different picture heights,
   which reads as six pictures rather than one set. */
.card.shot .say{width:100%;min-height:19mm;padding:3.5mm 4mm;display:flex;
  flex-direction:column;justify-content:center;gap:.25rem;background:inherit}
.card .say{display:flex;flex-direction:column;gap:.25rem;align-items:center}
.card.shot .say{align-items:center}

/* ── the note at the foot ─────────────────────────────────────────────── */
.note{flex:none;border-radius:9px;padding:5mm 6mm;background:var(--cream);
  display:flex;flex-direction:column;gap:.3rem;font-size:.98rem}
.note.lilac{background:var(--lilac)}
.note b{font-size:.9rem;color:var(--gold)}
.note.lilac b{color:var(--brand)}

/* ── the tutor's hand ─────────────────────────────────────────────────── */
/* A line the tutor wrote about one particular thing, drawn against it rather
   than collected at the foot of the page. */
.note-hand{display:block;margin:.15rem 0 0 .2rem;font-family:Caveat,cursive;
  font-size:1.15rem;line-height:1.15;color:var(--hand)}
.note-hand i{display:block;font-style:normal}
.marks{flex:none;display:flex;flex-direction:column;gap:.2rem}
.hand{margin:0;font-family:Caveat,cursive;font-size:1.4rem;line-height:1.2;color:var(--hand)}
.hand.print{font-family:Karla,sans-serif;font-size:.95rem}
/* In the margin, turned a little, the way a note written down the side sits. */
.marks.beside{position:absolute;right:2mm;top:22%;width:26mm;transform:rotate(-2.5deg);
  border-left:2px solid var(--hand);padding-left:.35rem}
.marks.beside .hand{font-size:1.05rem}
/* Across the page: the one line that has to interrupt what is printed. */
.marks.over{position:absolute;left:8%;right:8%;top:44%;text-align:center;
  transform:rotate(-1.5deg);pointer-events:none}
.marks.over .hand{font-size:1.7rem;text-shadow:0 0 6px #fff,0 0 14px #fff}
/* A ring round one thing, drawn by hand rather than as a rectangle: the
   uneven radii are what stop it reading as a border the deck was designed
   with. Red marks a mistake, green marks something got right, blue marks
   the thing being talked about. */
.ring{position:relative;box-shadow:none;outline:none}
.ring::after{content:"";position:absolute;inset:-.28rem -.5rem;border:2.5px solid var(--hand);
  border-radius:64% 36% 58% 42%/48% 62% 38% 52%;pointer-events:none}
.ring.green::after{border-color:var(--ok)}
.ring.blue::after{border-color:var(--brand)}
.keys{font-size:.88rem;display:flex;flex-direction:column;gap:2mm;background:var(--lilac);
  border-radius:9px;padding:6mm 7mm}
.keys p{margin:0}.keys b{color:var(--brand)}

/* ── cover and dividers ───────────────────────────────────────────────── */
.cover{background:var(--cover);color:#fff;justify-content:flex-start;gap:0;padding:16mm}
/* A photograph down the left third, the way the reference cover is built. The
   text keeps its own column rather than sitting on the picture: white type over
   an uncontrolled photograph is legible until the day someone picks a bright
   one. */
.cover.shot{padding-left:calc(34% + 12mm)}
.cover .face{position:absolute;left:0;top:0;bottom:0;width:34%;height:100%;
  object-fit:cover;z-index:0}
/* Four labels in a column a third narrower than before: without this the last
   one wraps onto a line of its own. */
.cover.shot .meta{gap:7mm}
.blob{position:absolute;border-radius:50%;background:var(--lift);z-index:0}
.blob.one{width:60%;aspect-ratio:1;right:-14%;top:-24%}
.blob.two{width:44%;aspect-ratio:1;left:-16%;bottom:-30%}
/* Lift the text above the decoration. Named one by one rather than as
   "every child except the blobs": that broader rule also caught the two
   elements on this page that place themselves — the photograph, which ended up
   floating in the middle, and the domain, which left the corner and landed on
   top of the meta row. */
.cover .logo,.cover .crumb,.cover h1,.cover .meta{position:relative;z-index:1}
.cover .logo{height:56px;width:auto;align-self:flex-start;margin-bottom:auto}
.crumb{margin:0 0 2mm;font-size:.72rem;letter-spacing:.18em;text-transform:uppercase;
  font-weight:700;color:#c9b6f5}
.cover h1{margin:0 0 auto;font-size:3.2rem;font-weight:800;line-height:1.06;
  letter-spacing:-.03em;max-width:14ch}
.cover .meta{display:flex;gap:12mm;flex-wrap:wrap}
.cover .meta span{display:block;font-size:.62rem;letter-spacing:.16em;text-transform:uppercase;
  font-weight:700;color:#c9b6f5;margin-bottom:1.5mm}
.cover .meta b{font-weight:500;font-size:1rem}
.cover .dom{position:absolute;right:16mm;bottom:14mm;z-index:1;font-size:.72rem;font-weight:700;
  color:#c9b6f5;z-index:2}
.t-violet{background:var(--cover);color:#fff}
.t-violet .head h2,.t-violet .sub{color:#fff}
.t-violet .sub{opacity:.75}
.t-violet .hero{background:#fff}
.t-violet .hero .label{color:var(--deep)}
.t-violet .glyph{color:var(--deep)}
.t-violet .srow{background:rgba(255,255,255,.94);border-color:transparent;color:var(--ink)}
.t-violet .note{background:rgba(255,255,255,.94);color:var(--ink)}
.t-violet .pg{color:#c9b6f5}

@media print{
  body{background:#fff}
  .deck{padding:0;gap:0}
  .slide{box-shadow:none;width:254mm;height:190.5mm;aspect-ratio:auto;break-after:page}
  .slide:last-child{break-after:auto}
  .sid{display:none}
}
@media(max-width:640px){
  .slide{aspect-ratio:auto;min-height:0;padding:8mm}
  .c4,.c5{grid-template-columns:repeat(2,1fr)}
  .l2,.l3{grid-template-columns:1fr}
  .bub{width:78%}
  .cover h1{font-size:2.2rem}
}
`;
