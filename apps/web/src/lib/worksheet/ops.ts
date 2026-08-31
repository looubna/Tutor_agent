import * as z from "zod";

/**
 * What the tutor does to the paper during a class (§8.4).
 *
 * An op names a box, never a position. There are no page coordinates anywhere
 * in this file, and that is the point: a mark aimed at `b7` is still on `b7` at
 * a different screen size, on a phone, and in the PDF a parent prints.
 *
 * The list of ops *is* the marked worksheet. We do not build a second document
 * after the class — we replay these onto the same one (§5.1).
 */

const At = z.object({
  box: z.string(),
  /** Where on the box the mark goes. Defaults to under it. */
  where: z.enum(["below", "beside", "over"]).default("below"),
  /**
   * Which numbered thing on the page this mark belongs to, in the same reading
   * order `circle` counts in. A mark that names one is drawn against it; one
   * that names nothing falls to the foot of the page.
   *
   * This is what stops an explanation being a list at the bottom. Working
   * written under the page is working about the page in general; working about
   * the third exercise belongs beside the third exercise, where the student
   * will look for it.
   */
  at: z.number().int().min(0).nullable().default(null),
});

const Write = z.object({
  id: z.string(),
  op: z.literal("write"),
  on: At,
  text: z.string().min(1),
  /** Handwriting by default — this is a teacher's mark, not typesetting. */
  style: z.enum(["hand", "print"]).default("hand"),
});

const Circle = z.object({
  id: z.string(),
  op: z.literal("circle"),
  on: At,
  /** Which words in the box, by index. Empty means the whole box. */
  words: z.array(z.number().int().min(0)).default([]),
  colour: z.enum(["red", "green", "blue"]).default("red"),
});

/** A dot the student can follow while the tutor talks. Live only — not kept. */
const Point = z.object({ id: z.string(), op: z.literal("point"), on: At });

/** Writing the missing word into a gap. */
const Fill = z.object({
  id: z.string(),
  op: z.literal("fill"),
  on: At,
  row: z.number().int().min(0),
  text: z.string().min(1),
});

const Erase = z.object({ id: z.string(), op: z.literal("erase"), target: z.string() });

export const Op = z.discriminatedUnion("op", [Write, Circle, Point, Fill, Erase]);
export const Ops = z.array(Op);
export type Op = z.infer<typeof Op>;

/**
 * Apply the erases and drop the pointers, leaving what is actually on the paper.
 *
 * A pointer is a gesture during the class, not a mark: keeping them would put a
 * scatter of dots on the copy a parent opens.
 */
export function settled(ops: Op[]): Exclude<Op, { op: "point" } | { op: "erase" }>[] {
  const erased = new Set(ops.filter((o) => o.op === "erase").map((o) => o.target));
  return ops.filter(
    (o): o is Exclude<Op, { op: "point" } | { op: "erase" }> =>
      o.op !== "point" && o.op !== "erase" && !erased.has(o.id),
  );
}

/** How much the tutor actually wrote. §13.3 says to watch this on every lesson. */
export function marksMade(ops: Op[]): number {
  return settled(ops).length;
}

export function byBox(ops: Op[]) {
  const map = new Map<string, Exclude<Op, { op: "point" } | { op: "erase" }>[]>();
  for (const op of settled(ops)) {
    const list = map.get(op.on.box) ?? [];
    list.push(op);
    map.set(op.on.box, list);
  }
  return map;
}
