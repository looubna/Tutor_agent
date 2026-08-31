import { test } from "node:test";
import assert from "node:assert/strict";

import { speechLocale } from "./locales";

/**
 * Which language a class is spoken aloud in. The bug this exists for: a French
 * maths lesson was read with an English voice, because the tag was looked up
 * from the subject id and "mathematics" is not a language.
 */
test("a language lesson is spoken in the language being taught", () => {
  // The student's own language is irrelevant here — that is what the lesson is
  // for.
  assert.equal(speechLocale("de-DE", undefined, "fr"), "de-DE");
});

test("a science lesson is spoken in its programme's language", () => {
  assert.equal(speechLocale(undefined, "fr-FR", "en"), "fr-FR");
});

test("a programme that names no language falls back to the student's", () => {
  assert.equal(speechLocale(undefined, undefined, "fr"), "fr-FR");
  assert.equal(speechLocale(undefined, undefined, "ko"), "ko-KR");
});

test("and to English when the student has not said", () => {
  assert.equal(speechLocale(undefined, undefined, null), "en-GB");
  assert.equal(speechLocale(undefined, undefined, "klingon"), "en-GB");
});
