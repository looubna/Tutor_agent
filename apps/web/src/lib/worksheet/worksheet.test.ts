import { test } from "node:test";
import assert from "node:assert/strict";

import words from "@data/words.de.json";
import { validate, stripAnswers, assertNoAnswers, answerKey, picturesIn } from "./boxes";
import { settled, marksMade, byBox, Ops } from "./ops";
import { render } from "./render";
import { problemsFor, warnings } from "./fit";
import { SAMPLE } from "./sample";

const WORDS = words.words as Record<string, { article: string }>;
const sheet = validate(SAMPLE);

/** Every term a block puts a definite article in front of. */
function terms(): string[] {
  return sheet.slides.flatMap((slide) =>
    slide.blocks.flatMap((block) =>
      block.kind === "cards" ? block.items.map((i) => i.label ?? i.lead ?? "")
      : block.kind === "list" ? block.items.map((i) => i.term)
      : block.kind === "hero" ? [block.label]
      : [],
    ),
  );
}

test("a deck with two slides sharing an id is refused", () => {
  assert.throws(
    () => validate({ ...SAMPLE, slides: [SAMPLE.slides[0], { ...SAMPLE.slides[0] }] }),
    /share the id/,
  );
});

test("🔒 §11: the word 'answer' appears nowhere in what a student receives", () => {
  const before = stripAnswers(sheet);
  assert.doesNotThrow(() => assertNoAnswers(before));
  assert.equal(/answer/i.test(JSON.stringify(before)), false);
});

test("🔒 §11: nor anywhere in the page built from it", () => {
  const html = render(stripAnswers(sheet), { kind: "before" });
  assert.equal(/answer/i.test(html), false, "the rendered page must not mention answers either");

  // There are exactly three ways the renderer draws a solution: a filled gap, a
  // picked option, a written-out sentence. None of them may exist on a blank
  // deck. This is the check that matters — a bare string search cannot do it,
  // because `choose` prints "der die das" as the options a student picks from,
  // and one of those three words is always the right one.
  // Matched as whole class attributes: the stylesheet is inlined into every
  // page, so a bare "picked" finds the CSS rule and not a marked option.
  for (const drawn of ['class="gap filled"', 'class="opt picked"', 'class="sol"']) {
    assert.equal(html.includes(drawn), false, `the blank deck draws a solution: ${drawn}`);
  }

  // And nothing a student can only know by being told appears as text at all.
  const spoken = sheet.slides.flatMap((slide) =>
    slide.blocks.flatMap((block) =>
      block.kind === "exercise" || block.kind === "build"
        ? block.rows.map((r) => r.answer)
        : block.kind === "cards" ? block.items.map((i) => i.answer).filter(Boolean) as string[]
        : block.kind === "dialogue" ? block.lines.map((l) => l.answer).filter(Boolean) as string[]
        : [],
    ),
  );
  for (const solution of spoken) {
    assert.equal(
      html.includes(`>${solution}<`), false,
      `the answer "${solution}" is visible in the blank deck`,
    );
  }
});

test("🔒 §11: and the Lösungen page is not built for a student at all", () => {
  const html = render(stripAnswers(sheet), { kind: "before" });
  assert.equal(html.includes("Lösungen"), false, "the answer key leaked onto the blank deck");
  assert.ok(render(sheet, { kind: "after", ops: [] }).includes("Lösungen"));
});

test("the blank deck still shows the questions", () => {
  const html = render(stripAnswers(sheet), { kind: "before" });
  const exercise = sheet.slides
    .flatMap((s) => s.blocks)
    .find((b) => b.kind === "exercise")!;
  assert.ok(exercise.kind === "exercise");
  assert.ok(html.includes(exercise.rows[0].prompt.split("___")[1].trim().slice(0, 8)));
  assert.ok(html.includes('class="gap"'), "and a line to write on");
});


test("every bitmap on the deck names the asset that licenses it", () => {
  // Drawn icons are ours by construction; anything under /materials/ that is a
  // file rather than an icon stem has to point at an Asset row.
  for (const slide of sheet.slides) {
    for (const block of slide.blocks) {
      if (block.kind === "photo") assert.ok(block.assetId, `${slide.id} has no assetId`);
      if (block.kind === "cards") {
        for (const item of block.items) {
          if (item.img) assert.ok(item.assetId, `${slide.id}: ${item.img} has no assetId`);
        }
      }
    }
  }
  // And the licence gate reads the same paths the renderer draws — icons
  // included, so a fetched pictogram cannot reach a deck unregistered.
  const listed = picturesIn(sheet);
  const drawn = sheet.slides.flatMap((slide) =>
    slide.blocks.flatMap((b) =>
      b.kind === "cards" ? b.items.map((i) => i.icon).filter(Boolean) as string[] : [],
    ),
  );
  assert.ok(drawn.length > 0, "the sample deck uses icons");
  for (const stem of drawn) {
    assert.ok(listed.includes(`/materials/german/a1-1/icons/${stem}.svg`), stem);
  }
});

test("the answer key is derived from the deck, page by page", () => {
  const key = answerKey(sheet);
  assert.ok(key.length >= 3, "a deck with exercises has an answer key");
  // The cover is page 1, so the first slide is page 2.
  assert.ok(key.every((k) => k.page >= 2 && k.page <= sheet.slides.length + 1));
  const flat = key.flatMap((k) => k.answers);
  assert.ok(flat.includes("Der") && flat.includes("Die"), flat.join(" "));
});

test("the marked deck is the same deck, with the answers now shown", () => {
  const after = render(sheet, { kind: "after", ops: [], studentName: "Amal" });
  const flat = answerKey(sheet).flatMap((k) => k.answers);
  assert.ok(after.includes(flat[0]), "the answer is on the after copy");
  assert.ok(after.includes("Nach dem Unterricht"), "the deck is in German, stamp included");
  assert.ok(after.includes("Amal"));
});

test("✍️ the tutor's writing lands on the slide it was aimed at", () => {
  const ops = Ops.parse([
    { id: "o1", op: "write", on: { box: "s6" }, text: "der = maskulin" },
    { id: "o2", op: "circle", on: { box: "s8" }, words: [0] },
    { id: "o3", op: "fill", on: { box: "s8" }, row: 0, text: "Der" },
  ]);
  const map = byBox(ops);
  assert.deepEqual([...map.keys()].sort(), ["s6", "s8"]);
  assert.equal(marksMade(ops), 3);

  const html = render(sheet, { kind: "after", ops });
  assert.ok(html.includes("der = maskulin"));
  assert.ok(html.includes("circled"), "the circled slide is marked as circled");
});

test("a pointer is a gesture, not a mark left on the paper", () => {
  const ops = Ops.parse([
    { id: "o1", op: "point", on: { box: "s6" } },
    { id: "o2", op: "write", on: { box: "s6" }, text: "gut!" },
  ]);
  assert.equal(marksMade(ops), 1);
  const kinds = (settled(ops) as { op: string }[]).map((o) => o.op);
  assert.deepEqual(kinds, ["write"]);
});

test("an erased mark does not survive to the marked copy", () => {
  const ops = Ops.parse([
    { id: "o1", op: "write", on: { box: "s6" }, text: "oops" },
    { id: "o2", op: "erase", target: "o1" },
    { id: "o3", op: "write", on: { box: "s6" }, text: "der = maskulin" },
  ]);
  assert.equal(marksMade(ops), 1);
  const html = render(sheet, { kind: "after", ops });
  assert.equal(html.includes("oops"), false);
  assert.ok(html.includes("der = maskulin"));
});

test("§13.3: how much the tutor wrote is a number we can watch", () => {
  assert.equal(marksMade([]), 0, "a lesson where nothing was written must read as zero");
});

test("an op aimed at a slide by name has no page coordinates in it", () => {
  const ops = Ops.parse([{ id: "o1", op: "write", on: { box: "s6" }, text: "x" }]);
  assert.equal(/bbox|x:|y:/.test(JSON.stringify(ops)), false);
});

test("🎨 the deck is one course: no slide chooses its own card colours", () => {
  // The lilac/cream alternation is a CSS rule, not a field. If a tint ever
  // becomes authorable this test is the thing that should stop it.
  assert.equal(/"tint"|"colour"|"color"/.test(JSON.stringify(SAMPLE)), false);
});

/**
 * The fit gate's judgement, without Chrome.
 *
 * `measureFit` needs a browser to get the numbers, but what it does with them
 * is arithmetic, and that is the part with the off-by-one in it. These feed it
 * measurements by hand.
 */
test("📐 a page whose content runs past the bottom is reported as cut off", () => {
  const problems = problemsFor([
    { id: "s4", page: 5, overflow: 31, fill: 1 },
  ]);
  assert.equal(problems.length, 1);
  assert.match(problems[0], /s4 \(page 5\)/);
  assert.match(problems[0], /cut off/);
  assert.match(problems[0], /31px/);
});

test("📐 a page that stops halfway down is reported as empty", () => {
  const problems = problemsFor([
    { id: "s10", page: 11, overflow: 0, fill: 0.45 },
  ]);
  assert.equal(problems.length, 1);
  assert.match(problems[0], /45% full/);
});

test("📐 overflow wins over emptiness — a clipped page is never called empty", () => {
  // Both can be true at once: a two-column page can leave a white right-hand
  // side while the left column runs off the bottom. Cutting text off is the
  // worse fault, so it is the one reported.
  const [problem] = problemsFor([{ id: "s7", page: 8, overflow: 40, fill: 0.3 }]);
  assert.match(problem, /cut off/);
  assert.doesNotMatch(problem, /full/);
});

test("📐 the cover is exempt — its decoration is meant to bleed past the edge", () => {
  assert.deepEqual(problemsFor([{ id: "cover", page: 1, overflow: 170, fill: 0.2 }]), []);
});

test("📐 a full page is neither a problem nor a warning", () => {
  const pages = [{ id: "s2", page: 3, overflow: 0, fill: 0.82 }];
  assert.deepEqual(problemsFor(pages), []);
  assert.deepEqual(warnings(pages), []);
});

test("📐 a page at the edge is a warning, never a failure", () => {
  const pages = [{ id: "s8", page: 9, overflow: 0, fill: 1 }];
  assert.deepEqual(problemsFor(pages), []);
  assert.equal(warnings(pages).length, 1);
  assert.match(warnings(pages)[0], /100% full/);
});

/**
 * The deck is written in the language being taught, and in no other.
 */
const german = (over: Record<string, unknown>) => validate({
  lessonId: "german.a1-1.classroom.l1", version: 1, title: "Test",
  slides: [{ id: "s1", title: "Test", blocks: [] }], ...over,
});







/* ── the tutor's marks land where they were aimed ───────────────────────── */

/**
 * A small sheet with one of everything a mark can land on. Built here rather
 * than taken from SAMPLE so the numbering under test is visible in one screen:
 * these tests are about *which* blank and *which* word, and a fixture you have
 * to scroll through to count is a fixture that hides an off-by-one.
 */
const MARKABLE = validate({
  lessonId: "german.a1-1.classroom.l3",
  version: 1,
  title: "der, die, das",
  slides: [
    {
      id: "s1",
      title: "Ergänze die Artikel",
      blocks: [
        { kind: "exercise", skillId: "artikel", rows: [
          { prompt: "___ Tisch", answer: "der" },
          { prompt: "___ Tür", answer: "die" },
          { prompt: "___ Fenster", answer: "das" },
        ] },
        { kind: "choose", rows: [
          { prompt: "___ Buch", options: ["der", "das"], answer: "das" },
          { prompt: "___ Lampe", options: ["die", "das"], answer: "die" },
        ] },
      ],
    },
  ],
});

const blank = stripAnswers(MARKABLE);
const mark = (ops: unknown) => render(blank, { kind: "after", ops: Ops.parse(ops) });

test("a fill writes into the gap it names, and into no other", () => {
  // Gap 1 is the second exercise row. Nothing else on the page fills in.
  const html = mark([{ id: "m1", op: "fill", on: { box: "s1", where: "over" }, row: 1, text: "die" }]);
  assert.match(html, /class="gap filled">die</);
  assert.equal((html.match(/class="gap filled"/g) ?? []).length, 1);
});

test("gaps are numbered in reading order across the blocks on a page", () => {
  // Three exercise rows are 0-2, so the first `choose` row is 3. Writing "das"
  // there picks the option rather than filling a line, because that is what
  // answering a multiple choice looks like on paper.
  const html = mark([{ id: "m1", op: "fill", on: { box: "s1", where: "over" }, row: 3, text: "das" }]);
  assert.equal((html.match(/class="opt picked"/g) ?? []).length, 1);
  assert.match(html, /class="opt picked">das</);
});

test("a ring goes round the thing it names, and round nothing else", () => {
  // Everything printed is ringable, in reading order: the three exercise rows
  // are 0-2, then the four `choose` options are 3-6. Number 5 is "die".
  const html = mark([{ id: "m1", op: "circle", on: { box: "s1", where: "over" }, words: [5], colour: "red" }]);
  assert.equal((html.match(/ ring red"/g) ?? []).length, 1);
  assert.match(html, /class="opt ring red">die</);
  // And a ring on one word is not a ring round the whole page.
  assert.equal(html.includes('class="slide t-page circled"'), false);
});

test("a ring naming nothing goes round the whole page", () => {
  const html = mark([{ id: "m1", op: "circle", on: { box: "s1", where: "over" }, words: [], colour: "red" }]);
  assert.match(html, /class="slide t-page circled"/);
});

test("a written line goes where the tutor aimed it", () => {
  const html = mark([
    { id: "m1", op: "write", on: { box: "s1", where: "below" }, text: "unter der Aufgabe" },
    { id: "m2", op: "write", on: { box: "s1", where: "beside" }, text: "am Rand" },
    { id: "m3", op: "write", on: { box: "s1", where: "over" }, text: "quer über die Seite" },
  ]);
  for (const [where, text] of [["below", "unter der Aufgabe"], ["beside", "am Rand"], ["over", "quer über die Seite"]]) {
    assert.match(html, new RegExp(`class="marks ${where}"><p class="hand hand">${text}<`));
  }
});

test("an erased mark never reaches the paper, and a pointer never does", () => {
  const html = mark([
    { id: "m1", op: "write", on: { box: "s1", where: "below" }, text: "falsch" },
    { id: "m2", op: "erase", target: "m1" },
    { id: "m3", op: "point", on: { box: "s1", where: "over" } },
    { id: "m4", op: "write", on: { box: "s1", where: "below" }, text: "richtig" },
  ]);
  assert.equal(html.includes("falsch"), false);
  assert.match(html, /richtig/);
});

test("🔒 §11: a marked-up blank sheet still gives nothing away", () => {
  // The student's copy carries the tutor's marks and still no key: only the
  // one gap that was actually filled in front of them shows an answer.
  const html = mark([{ id: "m1", op: "fill", on: { box: "s1", where: "over" }, row: 0, text: "der" }]);
  assert.equal(html.includes("Lösungen"), false);
  assert.equal((html.match(/class="gap filled"/g) ?? []).length, 1);
  assert.equal(html.includes(">die<"), true, "the options are printed, as they always were");
});

test("a line about one exercise is drawn against it, not at the foot of the page", () => {
  // Everything the tutor wrote used to land in one block below the whole page,
  // so working about the third question appeared under everything else.
  const html = mark([{
    id: "m1", op: "write", on: { box: "s1", where: "below", at: 1 },
    text: "die, parce que Tür est féminin",
  }]);
  assert.match(html, /class="note-hand"><i>die, parce que/);
  // And it is not also in the block at the bottom.
  assert.equal(html.includes('class="marks below"'), false);
});

test("a line about nothing in particular still falls to the foot of the page", () => {
  const html = mark([{
    id: "m1", op: "write", on: { box: "s1", where: "below" },
    text: "On révise les articles la prochaine fois",
  }]);
  assert.match(html, /class="marks below"/);
  // Matched as the drawn attribute: the stylesheet is inlined into every
  // page, so a bare "note-hand" finds the CSS rule and not a mark.
  assert.equal(html.includes('class="note-hand"'), false);
});

test("the anchored line lands on the thing it names", () => {
  // Target 1 is the second exercise row. Its note belongs inside that <li>.
  const html = mark([{
    id: "m1", op: "write", on: { box: "s1", where: "below", at: 1 },
    text: "ici",
  }]);
  // Split on `<li ` with the space: `<li` alone also matches `<link`.
  const rows = html.split("<li ").slice(1);
  assert.equal(rows.filter((r) => r.includes('class="note-hand"')).length, 1);
  // The second exercise row, which is the one target 1 names.
  assert.match(rows[1], /<span class="n">2<\/span>/);
  assert.match(rows[1], /class="note-hand"/);
});
