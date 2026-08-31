import { test } from "node:test";
import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import { join } from "node:path";

import { FR_MATHS_LEVELS } from "./frMaths";
import { lessonIdFor } from "../worksheet/lessonId";

/**
 * The French maths syllabus belongs to the agent. These check that the copy the
 * web app books against still says the same thing.
 *
 * The id is the whole contract. A booking becomes
 * `mathematics.<level>.<chapter>.<lesson>`; the turn route strips the subject
 * and sends the rest to the tutor, which looks it up in its own curriculum. If
 * the two drift, a class is bookable that the tutor cannot find — and the
 * failure is silent, because a tutor with no prepared lesson simply teaches
 * with less.
 */
const SOURCE = join(process.cwd(), "..", "agent", "data", "curriculum", "mathematics.json");

type Lesson = { id: string; title: string; learning_outcomes?: string[] };
type Unit = { id: string; title: string; lessons?: Lesson[] };
type Program = { id: string; label: string; units?: Unit[] };

const agent = (JSON.parse(readFileSync(SOURCE, "utf8")) as { programs: Program[] })
  .programs.filter((p) => p.id.startsWith("fr."));

/** Every lesson id the agent can teach, as `level.chapter.lesson`. */
const agentIds = new Set(
  agent.flatMap((p) => (p.units ?? []).flatMap((u) => (u.lessons ?? []).map((l) => l.id))),
);

/** Every lesson id the web app can book, built the way a booking builds it. */
const bookableIds = FR_MATHS_LEVELS.flatMap((level) =>
  level.chapters.flatMap((chapter) =>
    chapter.lessons.map((lesson) =>
      `${level.id}.${chapter.id}.${lesson.id}`),
  ),
);

test("every French maths lesson a student can book is one the tutor can find", () => {
  const orphans = bookableIds.filter((id) => !agentIds.has(id));
  assert.deepEqual(orphans, [], "these are bookable but unteachable");
});

test("every French maths lesson the tutor has is one a student can book", () => {
  const unreachable = [...agentIds].filter((id) => !bookableIds.includes(id));
  assert.deepEqual(unreachable, [], "these are authored but cannot be reached");
});

test("the whole programme is there", () => {
  assert.equal(bookableIds.length, 191);
  assert.equal(FR_MATHS_LEVELS.length, 7);
});

test("a booking builds exactly the id the agent's curriculum uses", () => {
  // The one join that has to be right. `lessonIdFor` prefixes the subject; the
  // turn route takes it back off again, and what is left must be the item id.
  const lessonId = lessonIdFor({
    subject: "mathematics", level: "fr.sixieme",
    chapter: "nombres-entiers-et-decimaux", lesson: "l2",
  });
  assert.equal(lessonId, "mathematics.fr.sixieme.nombres-entiers-et-decimaux.l2");
  assert.ok(agentIds.has(lessonId!.slice("mathematics.".length)));
});

test("every lesson carries the can-do outcomes it is taught against", () => {
  const bare = FR_MATHS_LEVELS.flatMap((level) =>
    level.chapters.flatMap((chapter) =>
      chapter.lessons.filter((l) => !l.objectives?.length)
        .map((l) => `${level.id}.${chapter.id}.${l.id}`)),
  );
  assert.deepEqual(bare, [], "a lesson with no outcomes cannot be planned against");
});

test("a French maths level says it is taught in French", () => {
  // Without this the call screen reads "Je sais comparer deux nombres
  // décimaux" with an en-GB voice, because "mathematics" is not a language
  // subject and has no locale of its own.
  const wrong = FR_MATHS_LEVELS.filter((l) => l.locale !== "fr-FR");
  assert.deepEqual(wrong.map((l) => l.id), []);
});
