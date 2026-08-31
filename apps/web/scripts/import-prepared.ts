/**
 * Turn a lesson the material agent prepared into the worksheet a student holds.
 *
 *     npx tsx --env-file=.env --conditions=react-server scripts/import-prepared.ts \
 *       mathematics.fr.sixieme.nombres-entiers-et-decimaux.l1 --by "Loubna"
 *     …--list                      what has been prepared but not yet imported
 *
 * The material is NOT written here. It is written by the material agent, in the
 * pipeline, against a plan and a set of objectives, and checked by the quality
 * checker — `python scripts/warm_lessons.py mathematics fr.sixieme` is what
 * produces it. This reads what that left in the agent's cache and lays it out
 * as pages.
 *
 * Keeping the two apart is the whole point. The tutor's marks name a page and a
 * numbered row, so the layout has to be the same shape on every paper; and the
 * material has to come from the agent that was built to write it, not from
 * whatever a script asked a model for on the side.
 */
import { readFileSync, readdirSync } from "node:fs";
import { join } from "node:path";
import { prisma } from "../src/lib/prisma";
import { draft, publish } from "../src/lib/worksheet/store";
import type { Block, Slide as Slide2 } from "../src/lib/worksheet/boxes";

const CACHE = join(process.cwd(), "..", "agent", "out", "cache");

type Cell = { text: string; answer?: string };
type Slide =
  | { kind: "summary"; title?: string; instruction?: string;
      groups: { heading: string; points: string[] }[] }
  | { kind: "rule_table"; title?: string; instruction?: string;
      headers: string[]; rows: Cell[][] }
  | { kind: "question_list"; title?: string; instruction?: string; items: Cell[] };

type Exercise = { id: string; prompt: string; answer: string; hint?: string };
type Item = {
  id: string; kind: string; title?: string; instruction?: string;
  content?: string; exercises?: Exercise[]; slide?: Slide;
};
type Quality = { status?: string; overall_score?: number;
                 critical_issues?: { problem: string; item_id?: string }[] };
type Prepared = {
  material: { target_item_id?: string; target_item_title?: string; items: Item[] };
  objectives?: { objectives?: { statement: string }[] };
  quality?: Quality;
};

/** Markdown as plain text: the deck escapes what it draws, so `**` would show. */
const plain = (text: string) =>
  text.replace(/^#{1,6}\s*/gm, "")
      .replace(/\*\*(.+?)\*\*/g, "$1")
      .replace(/\*(.+?)\*/g, "$1")
      .replace(/`(.+?)`/g, "$1")
      .trim();

/**
 * One material item becomes one block.
 *
 * The material agent writes its teaching into `slide` — a structured component
 * with a kind of its own — and the three kinds it produces are already the
 * three shapes a page needs: a summary is labelled rows, a rule table is a
 * table, a question list is numbered gaps. Reading `slide` rather than the
 * prose in `content` is what keeps a table a table instead of flattening it
 * into a paragraph of pipe characters.
 *
 * `content` and `exercises` are still read, because an item may carry either,
 * and a lesson written the other way round must not come out blank.
 */
function blockFor(item: Item, skillId: string): Block | null {
  const slide = item.slide;

  if (slide?.kind === "summary" && slide.groups?.length) {
    return { kind: "rows", items: slide.groups.slice(0, 6).map((g) => ({
      head: plain(g.heading).slice(0, 60),
      body: g.points.map(plain).join(" · "),
    })) } as Block;
  }

  if (slide?.kind === "rule_table" && slide.rows?.length) {
    const head = (slide.headers ?? []).map(plain);
    const rows = slide.rows.map((row) => row.map((c) => plain(c.text ?? "")));
    // `table` wants at least two columns and every row the same width.
    if (head.length >= 2 && rows.every((r) => r.length === head.length)) {
      return { kind: "table", head, rows: rows.slice(0, 8) } as Block;
    }
    // A one-column table is really a list of steps.
    return { kind: "rows", items: rows.slice(0, 6).map((r) => ({
      head: r[0]?.slice(0, 60) ?? "•", body: r.slice(1).join(" · ") || " ",
    })) } as Block;
  }

  const questions = slide?.kind === "question_list" ? slide.items ?? [] : [];
  const rows = questions.length
    ? questions.filter((q) => q.text && q.answer)
        .map((q) => ({ prompt: plain(q.text), answer: plain(q.answer!) }))
    : (item.exercises ?? []).filter((e) => e.prompt && e.answer)
        .map((e) => ({
          prompt: plain(e.prompt).includes("___") ? plain(e.prompt) : `${plain(e.prompt)} ___`,
          answer: plain(e.answer),
          ...(e.hint ? { hint: plain(e.hint) } : {}),
        }));
  if (rows.length) {
    return { kind: "exercise", skillId, rows: rows.slice(0, 10) } as Block;
  }

  // Last resort: prose, split into rows so it is readable on a 4:3 page.
  const lines = plain(item.content ?? "").split("\n").map((l) => l.trim()).filter(Boolean);
  if (!lines.length) return null;
  return { kind: "rows", items: lines.slice(0, 6).map((line) => {
    const split = line.match(/^(.{2,28}?)\s*[:—–]\s+(.+)$/);
    return split ? { head: split[1], body: split[2] } : { head: "•", body: line };
  }) } as Block;
}

function pages(prepared: Prepared, lessonId: string): Slide2[] {
  const slides: Slide2[] = [];
  const goals = (prepared.objectives?.objectives ?? []).map((o) => o.statement).slice(0, 6);
  if (goals.length) {
    slides.push({ id: "b1", title: "Ce que nous allons apprendre", tone: "page",
                  tab: "Objectifs", blocks: [{ kind: "goals", items: goals }] });
  }

  prepared.material.items.forEach((item, i) => {
    const block = blockFor(item, lessonId);
    if (!block) return;
    const title = plain(item.slide?.title ?? item.title ?? `Étape ${i + 1}`);
    const instruction = plain(item.slide?.instruction ?? item.instruction ?? "");
    slides.push({
      id: `b${slides.length + 1}`,
      title,
      subtitle: instruction || undefined,
      tone: "page",
      tab: block.kind === "exercise" ? "Exercices" : "Cours",
      blocks: [block],
    });
  });

  // Room to work, then what the hour was for. Both always last, so a student
  // who has done one of these knows where they are on the next.
  slides.push({ id: `b${slides.length + 1}`, title: "Mon brouillon",
                subtitle: "Pour poser les calculs", tone: "page", tab: "Notes",
                blocks: [{ kind: "lines", count: 8, cols: 1, numbered: false,
                           tone: "page", label: "Mes calculs" }] });
  if (goals.length) {
    slides.push({ id: `b${slides.length + 1}`, title: "Ce que je sais faire maintenant",
      tone: "page", tab: "Bilan", blocks: [{ kind: "goals", items: goals }],
      note: { tone: "cream",
              text: "Coche ce que tu sais faire. Ce qui reste, on le revoit la prochaine fois." } });
  }
  return slides;
}

function cached(): { file: string; prepared: Prepared }[] {
  return readdirSync(CACHE)
    .filter((f) => f.endsWith(".json"))
    .map((file) => ({ file, prepared: JSON.parse(readFileSync(join(CACHE, file), "utf8")) }))
    .filter(({ prepared }) => prepared?.material?.items?.length);
}

async function main() {
  const args = process.argv.slice(2);
  const by = args.includes("--by") ? args[args.indexOf("--by") + 1] : undefined;
  const wanted = args.find((a) => !a.startsWith("--") && a !== by);

  const all = cached();
  if (!wanted || args.includes("--list")) {
    for (const { prepared } of all) {
      const item = prepared.material.target_item_id ?? "?";
      console.log(`  ${item}  —  ${prepared.material.target_item_title ?? ""}` +
        `  (${prepared.material.items.length} items)`);
    }
    console.log("\n  pass a lessonId (subject-prefixed) and --by \"your name\"");
    return;
  }
  if (!by) throw new Error('--by is required: a worksheet is published by a person, not a script');

  const subject = wanted.split(".")[0];
  const itemId = wanted.slice(subject.length + 1);
  const found = all.find(({ prepared }) => prepared.material.target_item_id === itemId);
  if (!found) throw new Error(`Nothing prepared for ${itemId}. Warm it first.`);

  const slides = pages(found.prepared, wanted);
  const taught = slides.filter((s) => !["Mon brouillon", "Ce que nous allons apprendre",
    "Ce que je sais faire maintenant"].includes(s.title));
  if (!taught.length) {
    throw new Error(
      "The prepared material produced no pages that teach anything — only the " +
      "objectives and the blank spaces. Re-run the pipeline for this lesson.");
  }

  /**
   * The quality checker is the gate, and it is not advisory.
   *
   * It failed both of the first maths lessons for a real reason — the material
   * agent had written its teaching into `slide` and left `content` empty — and
   * the papers were published anyway because nothing here looked. A person may
   * still overrule it, which is what --despite-quality is, but they have to
   * mean it and they have to see what they are overruling.
   */
  const quality = found.prepared.quality ?? {};
  if (quality.status && quality.status !== "PASS") {
    console.log(`  quality: ${quality.status} (score ${quality.overall_score ?? "?"})`);
    for (const issue of (quality.critical_issues ?? []).slice(0, 5)) {
      console.log(`    · ${issue.item_id ? `${issue.item_id}: ` : ""}${issue.problem}`);
    }
    if (!args.includes("--despite-quality")) {
      throw new Error(
        "This material did not pass the quality checker, so it is not published. " +
        "Fix it and re-warm the lesson, or pass --despite-quality if you have read " +
        "the issues above and want it anyway.");
    }
    console.log("  publishing anyway, as asked");
  }

  const created = await draft(wanted, {
    title: found.prepared.material.target_item_title ?? itemId,
    subtitle: itemId,
    meta: { niveau: itemId.split(".")[0], sprache: "Français" },
    slides,
  }, "material agent (warm_lessons.py)");
  console.log(`  drafted ${wanted} v${created.version} — ${slides.length} pages`);

  await publish(created.id, by);
  console.log(`  published as ${by}`);
  await prisma.$disconnect();
}

main().catch((err) => { console.error(err.message); process.exit(1); });
