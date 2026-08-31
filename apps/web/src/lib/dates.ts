import { enUS, fr, es, de, it, arSA, zhCN, ko } from "date-fns/locale";
import type { Locale } from "date-fns";
import type { Lang } from "@/lib/i18n";

/**
 * date-fns needs its own locale object to render month and weekday names, and
 * to know whether a time reads as "1:30 PM" or "13:30". Keyed by our own `Lang`
 * so calendars follow the interface language rather than the browser's.
 */
const DATE_LOCALES: Record<Lang, Locale> = {
  en: enUS,
  fr,
  es,
  de,
  it,
  ar: arSA,
  zh: zhCN,
  ko,
};

export function dateLocale(lang: Lang): Locale {
  return DATE_LOCALES[lang] ?? enUS;
}
