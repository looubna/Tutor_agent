/**
 * Is the word file plausible?
 *
 *     npx tsx scripts/check-words.ts
 *
 * Every article and plural in a published deck is checked against this file,
 * which makes the file the last word on both — and nothing was checking the
 * file itself. It was built by parsing the printed Goethe list, and a parser
 * that turns "das Wort" into "die Wört" is wrong in a way no downstream test
 * can catch: the deck agrees with the file, and both are wrong together.
 *
 * These rules do not know German. They know what the printed rule beside each
 * word promised, and whether the plural in the file keeps that promise. That is
 * enough to have caught the one bad entry, and it is the kind of check that
 * keeps working as the file grows.
 *
 * It reports; it does not repair. A plural is a fact about the language and
 * guessing a correction would put us back where we started.
 */
import { readFileSync } from "node:fs";
import { join } from "node:path";

type Entry = {
  article: string; plural: string | null; en: string; checked: boolean;
  src?: { printed?: string };
};

const file = join(import.meta.dirname, "..", "data", "words.de.json");
const words = JSON.parse(readFileSync(file, "utf8")).words as Record<string, Entry>;

const ARTICLES = new Set(["der", "die", "das"]);
const UMLAUTABLE = /[aouAOU]/;
const HAS_UMLAUT = /[äöüÄÖÜ]/;
/** Nouns whose plural is the same word with an umlaut and nothing added. */
const NO_ENDING_OK = /(el|er|en|chen|lein)$/;

const problems: string[] = [];
const say = (word: string, why: string) => problems.push(`${word.padEnd(18)} ${why}`);

for (const [word, entry] of Object.entries(words)) {
  if (!ARTICLES.has(entry.article)) {
    say(word, `article is "${entry.article}"`);
  }
  if (!entry.plural) continue;

  const printed = entry.src?.printed ?? "";
  const wantsUmlaut = /umlaut/i.test(printed);

  // "umlaut, no ending" is a real rule — der Apfel, die Äpfel — but only for
  // nouns already ending -el, -er, -en, -chen or -lein. Applied to anything
  // else it is a mis-parse, which is how "die Wört" got in.
  if (wantsUmlaut && /no ending/i.test(printed) && !NO_ENDING_OK.test(word)) {
    say(word, `"${printed}" does not apply to a noun ending -${word.slice(-2)} → "${entry.plural}"`);
  }
  if (wantsUmlaut && !HAS_UMLAUT.test(entry.plural)) {
    say(word, `"${printed}" but the plural "${entry.plural}" has no umlaut`);
  }
  if (!wantsUmlaut && printed && HAS_UMLAUT.test(entry.plural) && !HAS_UMLAUT.test(word)) {
    say(word, `"${printed}" but the plural "${entry.plural}" added an umlaut`);
  }
  if (wantsUmlaut && !UMLAUTABLE.test(word) && !HAS_UMLAUT.test(word)) {
    say(word, `"${printed}" but there is no a, o or u to change`);
  }
  // "plural only" nouns — Eltern, Leute, Möbel — are listed under the plural
  // form itself, so plural === word is right for them and only for them.
  if (entry.plural === word && !/no change|plural only/i.test(printed)) {
    say(word, `plural is the same as the singular, but the rule says "${printed}"`);
  }
  // The plural of a German noun keeps its stem. Compared with umlauts folded
  // out, so that Äpfel still counts as beginning with Apfel.
  const fold = (s: string) => s.toLowerCase()
    .replace(/ä/g, "a").replace(/ö/g, "o").replace(/ü/g, "u");
  if (!fold(entry.plural).startsWith(fold(word).slice(0, Math.min(4, word.length)))) {
    say(word, `the plural "${entry.plural}" does not start with the singular`);
  }
}

const total = Object.keys(words).length;
const checked = Object.values(words).filter((e) => e.checked).length;

console.log(`\n  ${total} words · ${checked} hand-checked · ${total - checked} not\n`);
if (problems.length) {
  console.log(`  ✗ ${problems.length} to look at:\n`);
  for (const p of problems) console.log(`     ${p}`);
  console.log("");
  process.exit(1);
}
console.log("  ✅ every plural keeps the promise its printed rule made.\n");
