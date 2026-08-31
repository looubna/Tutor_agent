/**
 * Write the French maths programme into the web curriculum.
 *
 *     npx tsx --conditions=react-server scripts/build-fr-maths.ts
 *
 * The agent owns this syllabus. `apps/agent/data/curriculum/mathematics.json`
 * has 191 authored lessons across seven levels, each with its own can-do
 * outcomes, and the agent resolves a booking against those ids. The web app had
 * its own hand-written version in which a "lesson" was really a whole unit —
 * so a class booked here named something the tutor's curriculum had never heard
 * of, and every French maths lesson fell back to teaching with no plan and no
 * material.
 *
 * Rather than keep two syllabuses in step by hand, this generates one from the
 * other. The ids are the point: `lessonIdFor` builds
 * `mathematics.<level>.<chapter>.<lesson>`, the turn route strips the subject,
 * and what is left has to be exactly the agent's item id —
 * `fr.sixieme.nombres-entiers-et-decimaux.l1`. So the level is the programme id,
 * the chapter is the unit id with that prefix removed, and the lesson keeps its
 * own `lN`.
 *
 * Idempotent. Re-run it after editing the authored lessons.
 */
import { readFileSync, writeFileSync } from "node:fs";
import { join } from "node:path";

const SOURCE = join(process.cwd(), "..", "agent", "data", "curriculum", "mathematics.json");
const TARGET = join(process.cwd(), "src", "lib", "curriculum", "frMaths.ts");

/** Collège first, then lycée: the headings the level menu groups under. */
const GROUP: Record<string, string> = {
  "fr.sixieme": "Collège", "fr.cinquieme": "Collège",
  "fr.quatrieme": "Collège", "fr.troisieme": "Collège",
  "fr.seconde": "Lycée", "fr.premiere": "Lycée", "fr.terminale": "Lycée",
};

/**
 * A badge for each chapter, by what the unit is about.
 *
 * Keyword-matched rather than authored, because 101 units is too many to hand
 * an emoji each and a wrong badge is worse than a general one. First match
 * wins, so the list runs from the most specific topic to the least.
 */
const BADGES: [RegExp, string][] = [
  [/probabilit|statistiq|donnees|données|echantillon/i, "🎲"],
  [/geometrie|géométrie|triangle|cercle|angle|thales|thalès|pythagore|vecteur|espace|solide|droite|configuration/i, "📐"],
  [/aire|perimetre|périmètre|volume|grandeur|mesure|longueur/i, "📏"],
  [/fonction|derive|dériv|limite|continuit|integr|intégr|exponentiel|logarithm|trigonom/i, "📈"],
  [/suite/i, "🔁"],
  [/equation|équation|inequation|inéquation|litteral|littéral|polynome|polýn|second-degre|second degr/i, "🟰"],
  [/proportionnalite|proportionnalit|pourcentage|ratio|echelle|échelle/i, "⚖️"],
  [/fraction|decimaux|décimaux|entier|relatif|puissance|racine|nombre|calcul|divisib|premier/i, "🔢"],
  [/algorithm|programm|python|scratch/i, "💻"],
];

const badge = (title: string, id: string) =>
  BADGES.find(([pattern]) => pattern.test(title) || pattern.test(id))?.[1] ?? "🧮";

type Lesson = { id: string; title: string; order: number; learning_outcomes?: string[] };
type Unit = { id: string; title: string; order: number; lessons?: Lesson[] };
type Program = { id: string; label: string; units?: Unit[] };

const quote = (s: string) => JSON.stringify(s);

function main() {
  const data = JSON.parse(readFileSync(SOURCE, "utf8")) as { programs: Program[] };
  const french = data.programs.filter((p) => p.id.startsWith("fr."));

  let lessons = 0;
  const levels = french.map((program) => {
    const units = [...(program.units ?? [])].sort((a, b) => a.order - b.order);
    const chapters = units
      .filter((unit) => (unit.lessons ?? []).length > 0)
      .map((unit) => {
        // The unit id already carries the programme; the chapter must not
        // repeat it or the id built from level + chapter would say it twice.
        const id = unit.id.startsWith(`${program.id}.`)
          ? unit.id.slice(program.id.length + 1)
          : unit.id;
        const rows = [...(unit.lessons ?? [])].sort((a, b) => a.order - b.order);
        lessons += rows.length;
        const body = rows
          .map((lesson) => {
            const outcomes = (lesson.learning_outcomes ?? []).map(quote).join(", ");
            const short = lesson.id.split(".").pop()!;
            return `        { id: ${quote(short)}, title: ${quote(lesson.title)}` +
              (outcomes ? `,\n          objectives: [${outcomes}] }` : " }");
          })
          .join(",\n");
        return `      { id: ${quote(id)}, title: ${quote(unit.title)}, emoji: ${quote(badge(unit.title, unit.id))},\n        lessons: [\n${body},\n        ] }`;
      })
      .join(",\n");

    const group = GROUP[program.id];
    // Taught in French, whatever language the interface is set to. Without this
    // the call screen reads "Je sais comparer deux nombres décimaux" with an
    // English voice.
    return `    { id: ${quote(program.id)}, programme: FR, label: ${quote(program.label)}, locale: "fr-FR"` +
      (group ? `, group: ${quote(group)}` : "") +
      `,\n      chapters: [\n${chapters},\n      ] }`;
  });

  const file = `// Generated by scripts/build-fr-maths.ts — do not edit by hand.
//
// The source is the agent's own syllabus,
// apps/agent/data/curriculum/mathematics.json, so the ids here are the ids the
// tutor resolves a booking against. Editing this file by hand would make a
// lesson bookable that the tutor cannot find. Edit the authored lessons in
// apps/agent/data/curriculum/source/ and run the script again.
//
// ${lessons} lessons across ${levels.length} levels.
import type { Level } from "@/lib/curriculum";

/** The syllabus name, repeated here so this file stands alone. */
const FR = "Programme français (cours et exercices par niveau)";

export const FR_MATHS_LEVELS: Level[] = [
${levels.join(",\n")},
];
`;

  writeFileSync(TARGET, file, "utf8");
  console.log(`wrote ${lessons} lessons across ${levels.length} levels to ${TARGET}`);
}

main();
