"use client";

import Link from "next/link";
import { useActionState } from "react";
import { signup } from "@/app/actions/auth";
import { useLanguage, useT } from "@/lib/i18n";
import { LOCALES } from "@/lib/locales";

export default function SignupPage() {
  const [state, action, pending] = useActionState(signup, undefined);
  const t = useT();
  const { lang } = useLanguage();

  return (
    <>
      <h1 className="text-xl font-semibold text-foreground font-display">{t("auth.signupHeading")}</h1>
      <p className="mt-1 text-sm text-muted">{t("auth.signupSubheading")}</p>

      <form action={action} className="mt-6 flex flex-col gap-4">
        <div>
          <label htmlFor="name" className="mb-1 block text-sm font-medium text-foreground">
            {t("auth.nameLabel")}
          </label>
          <input
            id="name"
            name="name"
            type="text"
            required
            className="w-full rounded-lg border border-border bg-surface px-3 py-2 text-sm outline-none focus:border-primary"
          />
          {state?.errors?.name && <p className="mt-1 text-xs text-danger">{state.errors.name[0]}</p>}
        </div>

        <div>
          <label htmlFor="email" className="mb-1 block text-sm font-medium text-foreground">
            {t("auth.emailLabel")}
          </label>
          <input
            id="email"
            name="email"
            type="email"
            required
            className="w-full rounded-lg border border-border bg-surface px-3 py-2 text-sm outline-none focus:border-primary"
          />
          {state?.errors?.email && <p className="mt-1 text-xs text-danger">{state.errors.email[0]}</p>}
        </div>

        <div>
          <label htmlFor="password" className="mb-1 block text-sm font-medium text-foreground">
            {t("auth.passwordLabel")}
          </label>
          <input
            id="password"
            name="password"
            type="password"
            required
            className="w-full rounded-lg border border-border bg-surface px-3 py-2 text-sm outline-none focus:border-primary"
          />
          {state?.errors?.password && (
            <ul className="mt-1 list-disc pl-4 text-xs text-danger">
              {state.errors.password.map((error) => (
                <li key={error}>{error}</li>
              ))}
            </ul>
          )}
        </div>

        <div>
          <label htmlFor="supportLanguage" className="mb-1 block text-sm font-medium text-foreground">
            {t("auth.supportLanguageLabel")}
          </label>
          <select
            id="supportLanguage"
            name="supportLanguage"
            defaultValue={lang}
            className="w-full rounded-lg border border-border bg-surface px-3 py-2 text-sm outline-none focus:border-primary"
          >
            {LOCALES.map((l) => (
              <option key={l.code} value={l.code}>
                {l.label}
              </option>
            ))}
          </select>
          <p className="mt-1 text-xs text-muted">{t("auth.supportLanguageHint")}</p>
          {state?.errors?.supportLanguage && (
            <p className="mt-1 text-xs text-danger">{state.errors.supportLanguage[0]}</p>
          )}
        </div>

        {state?.message && <p className="text-sm text-danger">{state.message}</p>}

        <button
          type="submit"
          disabled={pending}
          className="mt-2 rounded-lg bg-primary px-4 py-2.5 text-sm font-semibold text-white transition-colors hover:bg-primary-hover disabled:opacity-60"
        >
          {pending ? t("auth.signupSubmitPending") : t("auth.signupSubmit")}
        </button>
      </form>

      <p className="mt-6 text-center text-sm text-muted">
        {t("auth.alreadyHaveAccount")}{" "}
        <Link href="/login" className="font-medium text-primary hover:underline">
          {t("auth.login")}
        </Link>
      </p>
    </>
  );
}
