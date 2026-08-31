/**
 * Language identity: the codes, their labels, and the guards for them.
 *
 * Deliberately NOT a client module. `i18n.tsx` is "use client", so anything
 * defined there is unreachable from a server action — importing `isLang` from
 * it threw "Attempted to call isLang() from the server" and took booking down
 * with it. Both sides import from here instead.
 */
export type Lang = "en" | "fr" | "es" | "de" | "it" | "ar" | "zh" | "ko";

export type Locale = {
  code: Lang;
  /** The language's name in itself, the way a language menu should read. */
  label: string;
  /** Two letters for the compact switcher in the nav. */
  short: string;
  dir: "ltr" | "rtl";
};

/**
 * One interface language per language Zanoba teaches, so a student can work in
 * the language they already speak rather than in English by default.
 */
export const LOCALES: Locale[] = [
  { code: "en", label: "English", short: "EN", dir: "ltr" },
  { code: "fr", label: "Français", short: "FR", dir: "ltr" },
  { code: "es", label: "Español", short: "ES", dir: "ltr" },
  { code: "de", label: "Deutsch", short: "DE", dir: "ltr" },
  { code: "it", label: "Italiano", short: "IT", dir: "ltr" },
  { code: "ar", label: "العربية", short: "AR", dir: "rtl" },
  { code: "zh", label: "中文", short: "ZH", dir: "ltr" },
  { code: "ko", label: "한국어", short: "KO", dir: "ltr" },
];

export function isLang(value: unknown): value is Lang {
  return typeof value === "string" && LOCALES.some((l) => l.code === value);
}

export function localeFor(lang: Lang): Locale {
  return LOCALES.find((l) => l.code === lang) ?? LOCALES[0];
}

/**
 * The BCP-47 tag a class is actually spoken in.
 *
 * Three sources, most specific first, and the middle one is the one that was
 * missing. A language lesson is spoken in the language being taught, which is
 * the subject's own `locale`. A science lesson has no target language — but it
 * is not therefore spoken in the interface language either: the French maths
 * programme is taught in French to a student whose interface may be in English,
 * and reading "Je sais comparer deux nombres décimaux" aloud with an `en-GB`
 * voice is what a French lesson in an English mouth sounds like. So a level may
 * declare the language its programme is taught in. Only when neither says
 * anything does the student's own language decide.
 */
const TAGS: Record<Lang, string> = {
  en: "en-GB", fr: "fr-FR", es: "es-ES", de: "de-DE",
  it: "it-IT", ar: "ar-SA", zh: "zh-CN", ko: "ko-KR",
};

export function speechLocale(
  subjectLocale: string | undefined,
  levelLocale: string | undefined,
  supportLanguage: string | null | undefined,
): string {
  if (subjectLocale) return subjectLocale;
  if (levelLocale) return levelLocale;
  return isLang(supportLanguage) ? TAGS[supportLanguage] : TAGS.en;
}
