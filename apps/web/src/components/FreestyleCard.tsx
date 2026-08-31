"use client";

import { useActionState } from "react";
import { useFormStatus } from "react-dom";
import { startLessonNow } from "@/app/actions/booking";
import { useT } from "@/lib/i18n";

/**
 * Opens a conversation with no chapter behind it — the practice a language
 * learner needs most and the one the syllabus can't schedule. The topic box is
 * optional on purpose: filling it in should feel like a shortcut, not a form to
 * get through, so leaving it empty simply lets the tutor open the conversation.
 */
export function FreestyleCard({ subject, levelId }: { subject: string; levelId: string }) {
  const t = useT();
  const [state, action] = useActionState(
    startLessonNow.bind(null, { subject, level: levelId, chapter: null, kind: "FREESTYLE" }),
    undefined,
  );

  return (
    <section className="rounded-xl border border-border bg-surface p-6 shadow-sm">
      <div className="flex items-center gap-3">
        <span
          aria-hidden="true"
          className="flex h-11 w-11 shrink-0 items-center justify-center rounded-full bg-primary-tint text-xl"
        >
          💬
        </span>
        <h2 className="text-base font-semibold text-foreground font-display">
          {t("course.freestyleTitle")}
        </h2>
      </div>

      <p className="mt-3 text-sm leading-relaxed text-muted">{t("course.freestyleBody")}</p>

      <form action={action} className="mt-5">
        <label htmlFor="freestyle-topic" className="block text-sm font-medium text-foreground">
          {t("course.freestyleTopicLabel")}{" "}
          <span className="font-normal text-muted">({t("course.freestyleOptional")})</span>
        </label>
        <input
          id="freestyle-topic"
          name="topic"
          type="text"
          maxLength={200}
          placeholder={t("course.freestyleTopicPlaceholder")}
          className="mt-2 w-full rounded-lg border border-border bg-background px-3 py-2 text-sm text-foreground outline-none placeholder:text-muted focus:border-primary"
        />
        <Submit />
        {state?.error && (
          <p role="alert" className="mt-2 text-xs leading-relaxed text-danger">
            {state.error}
          </p>
        )}
      </form>
    </section>
  );
}

function Submit() {
  const t = useT();
  const { pending } = useFormStatus();

  return (
    <button
      type="submit"
      disabled={pending}
      className="mt-3 w-full rounded-full bg-primary px-4 py-2 text-sm font-semibold text-white transition-colors hover:bg-primary-hover disabled:opacity-60"
    >
      {pending ? t("course.freestyleStarting") : t("course.freestyleStart")}
    </button>
  );
}
