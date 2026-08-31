import * as z from "zod";

/**
 * What a lesson deck is made of.
 *
 * Two levels, and the split is the whole design. A SLIDE is a page: a title, a
 * subtitle, at most three blocks and one closing note. A BLOCK is a shape that
 * can appear on any slide — a grid of cards, a pair of speech bubbles, a run of
 * writing lines. Nine slides in the reference deck are "cards then a note", and
 * they differ only in what is written on the cards.
 *
 * The earlier schema gave every page its own type, which meant a new kind of
 * page needed a new schema, a new renderer branch and a new line in the agent's
 * prompt. Blocks compose instead: `[cards, bubbles]` with a note under it is a
 * page nobody had to add.
 *
 * Slides carry the ids. The tutor says "write beside s7" and an op names that
 * slide, never a position on it — which is why there is no page arithmetic
 * anywhere in this file, and why a mark survives a phone, a laptop and a PDF.
 */

const Icon = z.string().regex(/^[a-z0-9-]+$/, "icon names are file stems, not paths");
const ImgPath = z.string().startsWith("/materials/");

/** Where the drawn icon set lives, as the browser sees it. */
export const ICON_URL_BASE = "/materials/german/a1-1/icons";
export const iconUrl = (stem: string) => `${ICON_URL_BASE}/${stem}.svg`;

/**
 * A picture on a card, in the order we prefer them: one of our own drawn icons
 * by file stem, or a bitmap under public/materials that an Asset row licenses.
 */
const picture = {
  icon: Icon.optional(),
  img: ImgPath.optional(),
  assetId: z.string().optional(),
};


/* ── blocks ──────────────────────────────────────────────────────────────── */

/**
 * The workhorse. A row of cards, alternately lilac and cream, each one a big
 * lead (a letter, a glyph, a picture) over a label and an optional caption.
 *
 * Alphabet pages, vocabulary pages, pronunciation pages, "pick a word and ask
 * your partner" pages and gap-fill cards are all this block with different
 * fields filled in. `answer` is set when the label contains a `___`.
 */
const CardItem = z.object({
  /** The big thing on the card: "Aa", "Ü ü", "ß", or a whole phrase. */
  lead: z.string().optional(),
  /** What the card says: "Ampel", "der Stift", "Wie ___ man das?" */
  label: z.string().optional(),
  /** Small print at the foot: "/ˈyːbɐ/", "A + Umlaut", "Lippen rund". */
  caption: z.string().optional(),
  /** The word that belongs in the label's `___`. Never sent to a student. */
  answer: z.string().optional(),
  ...picture,
}).refine(
  (i) => i.lead ?? i.label ?? i.icon ?? i.img,
  { message: "a card needs a lead, a label or a picture — an empty card is a mistake" },
).refine(
  // A bitmap has to name the Asset row that licenses it. This used to be
  // checked only by a test over the sample deck, which was enough while the
  // sample was the only thing carrying photographs. Now that every picture is
  // one, it has to hold for the decks the agent writes too — an unlicensed
  // photograph is the one mistake here that costs money rather than
  // embarrassment. Drawn icons are exempt: they are ours by construction.
  (i) => !i.img || Boolean(i.assetId),
  { message: "a photograph needs an assetId — the licence row that permits it", path: ["assetId"] },
);

const Cards = z.object({
  kind: z.literal("cards"),
  cols: z.number().int().min(2).max(5).default(3),
  numbered: z.boolean().default(false),
  items: z.array(CardItem).min(2).max(15),
});

/**
 * Two people talking, drawn as bubbles that lean left and right. The reference
 * deck uses this for every "so sagt man das" page: the question sits high on
 * the left, the answer low on the right, and the empty diagonal between them is
 * what makes the page read as an exchange rather than a list.
 */
const Bubbles = z.object({
  kind: z.literal("bubbles"),
  numbered: z.boolean().default(false),
  turns: z.array(
    z.object({
      side: z.enum(["l", "r"]).default("l"),
      text: z.string(),
      answer: z.string().optional(),
    }),
  ).min(1).max(8),
});

/** Stacked labelled boxes: Klang / Beispiele / Großbuchstabe. */
const Rows = z.object({
  kind: z.literal("rows"),
  items: z.array(z.object({ head: z.string(), body: z.string() })).min(1).max(6),
});

/** One big card, usually beside a `rows` block. The ß page, the closing idiom. */
const Hero = z.object({
  kind: z.literal("hero"),
  /** A letter or symbol set very large. */
  glyph: z.string().optional(),
  label: z.string(),
  sub: z.string().optional(),
  ...picture,
});

/** Reference columns: the alphabet with its letter names, the vocabulary page. */
const List = z.object({
  kind: z.literal("list"),
  cols: z.number().int().min(1).max(3).default(2),
  items: z.array(z.object({ term: z.string(), gloss: z.string().optional() })).min(2).max(40),
});

/**
 * Ruled space. `page` is a student writing on the paper; `board` is the panel
 * the tutor writes into during the class and is drawn as one.
 */
const Lines = z.object({
  kind: z.literal("lines"),
  count: z.number().int().min(1).max(12).default(6),
  cols: z.number().int().min(1).max(2).default(1),
  label: z.string().optional(),
  numbered: z.boolean().default(false),
  tone: z.enum(["page", "board"]).default("page"),
});

/** Sort the words into two piles — mit Umlaut, mit ß. */
const Bins = z.object({
  kind: z.literal("bins"),
  items: z.array(z.object({ label: z.string(), lines: z.number().int().min(1).max(6).default(2) }))
    .min(2).max(3),
});

const Dialogue = z.object({
  kind: z.literal("dialogue"),
  scene: z.string().optional(),
  lines: z.array(
    z.object({
      who: z.string(),
      says: z.string(),
      /** Set when this line is the one the student fills in. */
      answer: z.string().optional(),
    }),
  ).min(2).max(10),
});

const Table = z.object({
  kind: z.literal("table"),
  caption: z.string().optional(),
  head: z.array(z.string()).min(2),
  rows: z.array(z.array(z.string())).min(1),
});

/** A numbered gap-fill. `prompt` uses `___`; `answer` is the missing word alone. */
const Exercise = z.object({
  kind: z.literal("exercise"),
  skillId: z.string(),
  rows: z.array(
    z.object({ prompt: z.string(), answer: z.string(), hint: z.string().optional() }),
  ).min(1).max(10),
});

/** Circle the right one. Two or three options, never more — this is A1. */
const Choose = z.object({
  kind: z.literal("choose"),
  rows: z.array(
    z.object({
      prompt: z.string(),
      options: z.array(z.string()).min(2).max(4),
      answer: z.string(),
    }),
  ).min(2).max(8),
});

/** Make a sentence from the parts, with a line to write it on. */
const Build = z.object({
  kind: z.literal("build"),
  // Two parts, not three. "Langsamer, bitte." is one of the five phrases the
  // spelling lesson exists to teach, and a minimum invented at the keyboard
  // refused it.
  rows: z.array(z.object({ parts: z.array(z.string()).min(2), answer: z.string() }))
    .min(2).max(8),
});

/** Lettered A · B · C, the shape the reference deck opens and closes with. */
const Goals = z.object({
  kind: z.literal("goals"),
  items: z.array(z.string()).min(1).max(6),
});

/**
 * The one photograph. It gets a slide to itself and never shares a page with
 * drawn cards — a photo among five flat icons makes a page look assembled
 * rather than made. `assetId` is required: no licence row, no picture.
 */
const Photo = z.object({
  kind: z.literal("photo"),
  src: ImgPath,
  alt: z.string(),
  assetId: z.string(),
  credit: z.string().optional(),
  /**
   * How the photograph sits on the page.
   *
   * `panel` is the one the reference deck leans on: the picture takes one side
   * of the slide, floor to ceiling, and the talking happens beside it. `strip`
   * is a band across the top, for a scene that sets up the exercise under it.
   * `plate` is the plain framed picture, and is what a photograph on its own
   * page gets.
   */
  shape: z.enum(["panel", "strip", "plate"]).default("plate"),
});

export const Block = z.discriminatedUnion("kind", [
  Cards, Bubbles, Rows, Hero, List, Lines, Bins,
  Dialogue, Table, Exercise, Choose, Build, Goals, Photo,
]);

/* ── slides ──────────────────────────────────────────────────────────────── */

/**
 * The cream box at the foot of nearly every slide: the tip, the warning, the
 * "und jetzt buchstabiere". It is not a block — it is always last, always one,
 * and always the width of the page, so it is a field rather than a shape.
 */
const Note = z.object({
  title: z.string().optional(),
  text: z.string(),
  tone: z.enum(["cream", "lilac"]).default("cream"),
});

export const Slide = z.object({
  id: z.string(),
  title: z.string(),
  subtitle: z.string().optional(),
  /**
   * `page` is a white slide. `violet` is full-bleed brand — the section
   * dividers and the closing idiom, and nothing else, because it stops being a
   * punctuation mark the third time it is used.
   */
  tone: z.enum(["page", "violet"]).default("page"),
  /**
   * The word printed sideways down the left edge — `Zusatzübungen`, `So sagt
   * man das!`. It names the stretch of the deck a page belongs to, and it is
   * the only thing on the page that is not read left to right.
   *
   * It is a label, not a heading: repeat it on every page of the stretch. A tab
   * that appears once is just a decoration.
   */
  tab: z.string().max(24).optional(),
  blocks: z.array(Block).max(3).default([]),
  note: Note.optional(),
});

export const Worksheet = z.object({
  lessonId: z.string(),
  version: z.number().int().min(1),
  title: z.string(),
  subtitle: z.string().optional(),
  /** The cover's three columns. Missing ones are left off rather than guessed. */
  meta: z.object({
    niveau: z.string().optional(),
    nummer: z.string().optional(),
    sprache: z.string().optional(),
  }).optional(),
  /** The photograph down the left of the cover. */
  cover: z.object({
    src: ImgPath,
    alt: z.string(),
    assetId: z.string(),
    credit: z.string().optional(),
  }).optional(),
  slides: z.array(Slide).min(1),
});

export type Block = z.infer<typeof Block>;
export type Slide = z.infer<typeof Slide>;
export type Worksheet = z.infer<typeof Worksheet>;

/** Slide ids must be unique — the tutor addresses slides by them. */
export function validate(input: unknown): Worksheet {
  const sheet = Worksheet.parse(input);
  const ids = sheet.slides.map((s) => s.id);
  const duplicate = ids.find((id, i) => ids.indexOf(id) !== i);
  if (duplicate) {
    throw new Error(`Two slides share the id "${duplicate}"; the tutor could not tell them apart.`);
  }
  return sheet;
}

/**
 * Every picture path on the deck, for the licence check on the way in.
 *
 * Icons count. They did not have to before, when the only icons were the
 * thirty-five drawn for this course — but `find_pictogram` now writes files
 * into the same directory from an outside icon set, and "it is an icon" would
 * otherwise be a way for a picture to reach a published deck without anyone
 * recording where it came from. Seed the drawn set once with
 * `npm run seed:icons`; the pictogram tool registers its own.
 */
export function picturesIn(sheet: Worksheet): string[] {
  const paths = sheet.slides.flatMap((slide) =>
    slide.blocks.flatMap((block) => {
      if (block.kind === "photo") return [block.src];
      if (block.kind === "cards") {
        return block.items.flatMap((i) =>
          [i.img, i.icon && iconUrl(i.icon)].filter(Boolean) as string[]);
      }
      if (block.kind === "hero") {
        return [block.img, block.icon && iconUrl(block.icon)].filter(Boolean) as string[];
      }
      return [];
    }),
  );
  // The cover photograph is a picture like any other, and it is the one a
  // parent sees first. Leaving it out of this list would let it reach a
  // published deck with no licence recorded against it.
  if (sheet.cover) paths.push(sheet.cover.src);
  return [...new Set(paths)];
}

/* ── what a student is allowed to receive ────────────────────────────────── */

/**
 * A different type from `Worksheet`, not the same one with blanked fields: an
 * exercise row here has no `answer` property at all, so there is nothing to
 * find in the network tab, the page source, or a saved copy.
 *
 * Written as one recursive mapped type rather than an Omit per block. The old
 * version listed every answer-bearing shape by hand, which is a list that goes
 * stale the first time someone adds a block and forgets — this one cannot.
 */
export type NoAnswers<T> =
  T extends (infer U)[] ? NoAnswers<U>[]
  : T extends object ? { [K in keyof T as K extends "answer" ? never : K]: NoAnswers<T[K]> }
  : T;

export type PublicBlock = NoAnswers<Block>;
export type PublicSlide = NoAnswers<Slide>;
export type PublicWorksheet = NoAnswers<Worksheet>;

/** The BEFORE deck: the same pages with the answers not hidden but absent. */
export function stripAnswers(sheet: Worksheet): PublicWorksheet {
  const walk = (value: unknown): unknown => {
    if (Array.isArray(value)) return value.map(walk);
    if (value && typeof value === "object") {
      return Object.fromEntries(
        Object.entries(value).filter(([k]) => k !== "answer").map(([k, v]) => [k, walk(v)]),
      );
    }
    return value;
  };
  return walk(sheet) as PublicWorksheet;
}

/**
 * Belt and braces: after stripping, prove it. Cheap enough to run on every
 * response, and it turns a future mistake into a 500 rather than a leak.
 */
export function assertNoAnswers(payload: unknown): void {
  if (/answer/i.test(JSON.stringify(payload))) {
    throw new Error("A deck on its way to a student still mentions an answer.");
  }
}

/**
 * Every answer on the deck, by the slide number a reader sees.
 *
 * This is what the Lösungen page is built from, and it is derived rather than
 * written: an answer key typed out by hand is a second copy of the truth that
 * drifts from the first one the moment a card is reworded.
 */
export function answerKey(sheet: Worksheet): { page: number; answers: string[] }[] {
  return sheet.slides
    .map((slide, i) => {
      const answers = slide.blocks.flatMap((block) => {
        switch (block.kind) {
          case "cards": return block.items.map((x) => x.answer).filter(Boolean) as string[];
          case "bubbles": return block.turns.map((x) => x.answer).filter(Boolean) as string[];
          case "dialogue": return block.lines.map((x) => x.answer).filter(Boolean) as string[];
          case "exercise":
          case "choose":
          // `filter(Boolean)` here as well as on the shapes above, because a
          // stripped sheet has no `answer` on its rows either. The marked copy
          // a student sees during a class is rendered from the stripped sheet
          // — marks on, key off — and without this it would try to build a
          // solutions page out of undefined.
          case "build": return block.rows.map((x) => x.answer).filter(Boolean) as string[];
          default: return [];
        }
      });
      // +2: the cover is page 1, so the first slide is page 2.
      return { page: i + 2, answers };
    })
    .filter((entry) => entry.answers.length > 0);
}
