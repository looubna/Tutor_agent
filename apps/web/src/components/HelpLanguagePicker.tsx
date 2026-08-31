"use client";

import { useActionState } from "react";
import { useFormStatus } from "react-dom";
import { updateSupportLanguage } from "@/app/actions/preferences";
import { LOCALES } from "@/lib/i18n";
import { useT } from "@/lib/i18n";

/**
 * The language the tutor may fall back to when the student is stuck. It is not
 * the language of the lesson — that comes from the subject — so the copy has to
 * be clear that picking one does not turn the class into that language.
 */
export function HelpLanguagePicker({ current }: { current: string | null }) {
  const t = useT();
  const [state, action] = useActionState(updateSupportLanguage, undefined);

  return (
    <form action={action} className="mt-4 flex flex-wrap items-center gap-3">
      <label htmlFor="supportLanguage" className="sr-only">
        {t("settings.helpLanguageHeading")}
      </label>
      <select
        id="supportLanguage"
        name="supportLanguage"
        defaultValue={current ?? "en"}
        className="rounded-lg border border-border bg-surface px-3 py-2 text-sm font-medium text-foreground outline-none focus:border-primary"
      >
        {LOCALES.map((l) => (
          <option key={l.code} value={l.code}>
            {l.label}
          </option>
        ))}
      </select>

      <Submit />

      {state?.saved && <span className="text-xs text-primary">{t("settings.helpLanguageSaved")}</span>}
      {state?.error && (
        <span role="alert" className="text-xs text-danger">
          {state.error}
        </span>
      )}
    </form>
  );
}

function Submit() {
  const t = useT();
  const { pending } = useFormStatus();

  return (
    <button
      type="submit"
      disabled={pending}
      className="rounded-lg bg-primary px-4 py-2 text-sm font-semibold text-white transition-colors hover:bg-primary-hover disabled:opacity-60"
    >
      {t("settings.helpLanguageSave")}
    </button>
  );
}
