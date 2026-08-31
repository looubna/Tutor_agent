"use client";

import { LOCALES, useT } from "@/lib/i18n";

/**
 * Which language the tutor may explain in when the learner is stuck.
 *
 * Only meaningful for a language class — a physics lesson has no second
 * language to fall back to — so callers render it for language subjects only.
 * The value is saved onto the learner, not the booking, so it is asked once and
 * then holds for every class they take.
 */
export function HelpLanguageField({
  value,
  onChange,
  subjectName,
}: {
  value: string;
  onChange: (next: string) => void;
  /** The language being learnt, to make clear this is *not* it. */
  subjectName: string;
}) {
  const t = useT();

  return (
    <div className="rounded-xl border border-border bg-surface p-4">
      <label htmlFor="help-language" className="text-sm font-medium text-foreground">
        {t("book.helpLanguage")}
      </label>
      <select
        id="help-language"
        value={value}
        onChange={(e) => onChange(e.target.value)}
        className="mt-2 w-full rounded-lg border border-border bg-surface px-3 py-2 text-sm font-medium text-foreground outline-none focus:border-primary"
      >
        {LOCALES.map((l) => (
          <option key={l.code} value={l.code}>
            {l.label}
          </option>
        ))}
      </select>
      <p className="mt-2 text-xs text-muted">
        {t("book.helpLanguageHint", { subject: subjectName })}
      </p>
    </div>
  );
}
