"use client";

import Link from "next/link";
import { useActionState } from "react";
import { login } from "@/app/actions/auth";
import { useT } from "@/lib/i18n";

export default function LoginPage() {
  const [state, action, pending] = useActionState(login, undefined);
  const t = useT();

  return (
    <>
      <h1 className="text-xl font-semibold text-foreground font-display">{t("auth.loginHeading")}</h1>
      <p className="mt-1 text-sm text-muted">{t("auth.loginSubheading")}</p>

      <form action={action} className="mt-6 flex flex-col gap-4">
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
          {state?.errors?.password && <p className="mt-1 text-xs text-danger">{state.errors.password[0]}</p>}
        </div>

        {state?.message && <p className="text-sm text-danger">{state.message}</p>}

        <button
          type="submit"
          disabled={pending}
          className="mt-2 rounded-lg bg-primary px-4 py-2.5 text-sm font-semibold text-white transition-colors hover:bg-primary-hover disabled:opacity-60"
        >
          {pending ? t("auth.loginSubmitPending") : t("auth.loginSubmit")}
        </button>
      </form>

      <p className="mt-6 text-center text-sm text-muted">
        {t("auth.newToBrand")}{" "}
        <Link href="/signup" className="font-medium text-primary hover:underline">
          {t("auth.createAccount")}
        </Link>
      </p>
    </>
  );
}
