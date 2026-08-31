/**
 * Convert stored worksheets from the old box format to the slide format.
 *
 *     npm run convert:decks            what would change
 *     npm run convert:decks -- --write apply it
 *
 * The rename was not just a rename: documents already in the database hold
 * `boxes[]` and no longer parse, so the two published decks answered 500 and
 * the students pinned to them lost the paper their class happened on.
 *
 * Rebuilding is not a substitute. A rebuild produces a *different* deck, and
 * §5.1 says a marked copy is the same paper the class sat in front of — so this
 * converts in place, and above all it KEEPS EVERY BOX ID. The tutor's ops name
 * boxes; keep the ids and every mark that was ever made still lands where it
 * was aimed. Change them and the marked copies survive as blank paper.
 *
 * One box became one page under the old rules, so one box becomes one slide
 * here. Where a box holds more rows than a slide may, it is split across
 * numbered slides rather than truncated.
 */
import { prisma } from "../src/lib/prisma";
import { validate, type Block, type Slide } from "../src/lib/worksheet/boxes";

/** What each kind of page was called on the page itself, in the old renderer. */
const KIND: Record<string, string> = {
  goal: "Lernziele", words: "Wortschatz", match: "Zuordnen", explain: "Grammatik",
  table: "Übersicht", speak: "Aussprache", exercise: "Übung", choose: "Auswählen",
  build: "Sätze bilden", dialogue: "Dialog", board: "Im Unterricht",
  reflect: "Rückblick", vocab: "Wortschatz", notes: "Notizen", image: "Bild",
  heading: "",
};

/**
 * A box from the old schema. Deliberately loose: this file exists to read
 * documents whose type no longer exists in the codebase, so the shape is
 * whatever was written down, and `validate` at the end is what proves the
 * conversion produced something the app can actually parse.
 */
type OldBox = Record<string, unknown> & { id: string; type: string };

const clamp = (n: number, lo: number, hi: number) => Math.max(lo, Math.min(hi, n));

/** Break a long list into slide-sized pieces. */
function chunk<T>(items: T[], size: number): T[][] {
  const out: T[][] = [];
  for (let i = 0; i < items.length; i += size) out.push(items.slice(i, i + size));
  return out.length ? out : [[]];
}

/** One old box becomes one slide, or several when it does not fit on one. */
function convertBox(box: OldBox): Slide[] {
  const title = (box.title as string) || KIND[box.type] || "";
  const subtitle = (box.instruction as string) || undefined;
  const note = box.note ? { text: box.note as string, tone: "cream" as const } : undefined;

  const slides = (groups: Block[][], extra?: Partial<Slide>): Slide[] =>
    groups.map((blocks, i) => ({
      id: i === 0 ? box.id : `${box.id}-${i + 1}`,
      title: groups.length > 1 ? `${title} (${i + 1}/${groups.length})` : title,
      subtitle, tone: "page" as const, blocks, note, ...extra,
    }));

  switch (box.type) {
    case "heading":
      return slides([[]], { title: box.text as string });

    case "goal":
    case "reflect":
      return slides(chunk(box.items as string[], 6).map((items) => [{ kind: "goals", items }]));

    case "words":
      return slides(chunk(box.items as OldBox[], 12).map((items) => [{
        kind: "cards", cols: 3, numbered: false,
        items: items.map((w) => ({
          label: w.de as string,
          caption: [w.en, w.note].filter(Boolean).join(" · ") || undefined,
          ...(w.icon ? { icon: w.icon as string } : {}),
          ...(w.img ? { img: w.img as string, assetId: w.assetId as string } : {}),
        })),
      }]));

    case "match":
      return slides([[{
        kind: "cards", cols: 4, numbered: true,
        items: (box.pairs as OldBox[]).map((p) => ({
          label: p.de as string,
          ...(p.icon ? { icon: p.icon as string } : {}),
          ...(p.img ? { img: p.img as string, assetId: p.assetId as string } : {}),
        })),
      }]]);

    case "explain": {
      const rows = (box.compare as OldBox[] | undefined) ?? [];
      return slides([rows.length ? [{
        kind: "rows", items: rows.map((c) => ({ head: c.head as string, body: c.body as string })),
      }] : []], { note: { text: box.text as string, tone: "cream" } });
    }

    case "image":
      return slides([[{
        kind: "photo", src: box.src as string, alt: box.alt as string,
        assetId: box.assetId as string, shape: "plate",
        ...(box.caption ? { credit: box.caption as string } : {}),
      }]]);

    case "exercise":
      return slides(chunk(box.rows as OldBox[], 10).map((rows) => [{
        kind: "exercise", skillId: box.skillId as string,
        rows: rows.map((r) => ({
          prompt: r.prompt as string, answer: r.answer as string,
          ...(r.hint ? { hint: r.hint as string } : {}),
        })),
      }]));

    case "choose":
      return slides(chunk(box.rows as OldBox[], 8).map((rows) => [{
        kind: "choose",
        rows: rows.map((r) => ({
          prompt: r.prompt as string, options: r.options as string[], answer: r.answer as string,
        })),
      }]));

    case "build":
      return slides(chunk(box.rows as OldBox[], 8).map((rows) => [{
        kind: "build",
        rows: rows.map((r) => ({ parts: r.parts as string[], answer: r.answer as string })),
      }]));

    case "dialogue":
      return slides(chunk(box.lines as OldBox[], 10).map((lines) => [{
        kind: "dialogue",
        ...(box.scene ? { scene: box.scene as string } : {}),
        lines: lines.map((l) => ({
          who: l.who as string, says: l.says as string,
          ...(l.answer !== undefined ? { answer: l.answer as string } : {}),
        })),
      }]));

    case "board":
      return slides([[{
        kind: "lines", tone: "board", cols: 1, numbered: false,
        count: clamp((box.lines as number) ?? 4, 1, 12),
      }]]);

    case "notes":
      return slides([[{
        kind: "lines", tone: "page", cols: 1, numbered: false,
        count: clamp((box.lines as number) ?? 12, 1, 12),
      }]]);

    case "vocab":
      return slides(chunk(box.rows as OldBox[], 40).map((rows) => [{
        kind: "list", cols: 2,
        items: rows.map((r) => ({
          term: r.de as string,
          gloss: [r.en, r.note].filter(Boolean).join(" · ") || undefined,
        })),
      }]));

    case "speak":
      return slides(chunk(box.items as OldBox[], 12).map((items) => [{
        kind: "cards", cols: 3, numbered: true,
        items: items.map((i) => ({
          label: i.de as string, ...(i.tip ? { caption: i.tip as string } : {}),
        })),
      }]));

    case "table":
      return slides([[{
        kind: "table", head: box.head as string[], rows: box.rows as string[][],
        ...(box.note ? { caption: box.note as string } : {}),
      }]]);

    default:
      throw new Error(`unknown box type "${box.type}"`);
  }
}

async function main() {
  const write = process.argv.includes("--write");
  const docs = await prisma.lessonDoc.findMany({ orderBy: [{ lessonId: "asc" }, { version: "asc" }] });

  let converted = 0;
  for (const doc of docs) {
    const old = JSON.parse(doc.boxes) as Record<string, unknown> & { boxes?: OldBox[] };
    if (!Array.isArray(old.boxes)) {
      console.log(`  · ${doc.lessonId} v${doc.version} already in the slide format`);
      continue;
    }

    const slides = old.boxes.flatMap(convertBox);
    const sheet = {
      lessonId: old.lessonId as string, version: old.version as number,
      title: old.title as string, subtitle: old.subtitle as string | undefined,
      meta: {
        niveau: old.subtitle as string | undefined,
        sprache: "Deutsch",
        nummer: old.lessonId as string,
      },
      slides,
    };

    // Parse it the way the app will. A conversion that does not validate is a
    // 500 moved from today to whenever somebody next opens the page.
    validate(sheet);

    console.log(`  ${write ? "✓" : "→"} ${doc.lessonId} v${doc.version} ${doc.status}` +
      `  ${old.boxes.length} boxes → ${slides.length} slides`);
    if (write) {
      await prisma.lessonDoc.update({
        where: { id: doc.id }, data: { boxes: JSON.stringify(sheet) },
      });
    }
    converted += 1;
  }

  console.log(write
    ? `\n  converted ${converted}\n`
    : `\n  ${converted} would be converted — re-run with --write\n`);
}

main().catch((err) => { console.error("\n  ✗ " + err.message + "\n"); process.exit(1); });
