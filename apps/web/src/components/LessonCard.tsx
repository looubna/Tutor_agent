"use client";

import Link from "next/link";
import { useActionState } from "react";
import { format, isWithinInterval, subMinutes } from "date-fns";
import { cancelBooking } from "@/app/actions/booking";
import { useLanguage, useT } from "@/lib/i18n";
import { findChapter } from "@/lib/curriculum";
import { SUBJECTS } from "@/lib/subjects";
import { TUTOR_NAME } from "@/lib/tutor";
import { dateLocale } from "@/lib/dates";

const START_WINDOW_MINUTES = 10;

export function LessonCard({
  id,
  startTime,
  endTime,
  status,
  sessionNumber,
  subject: subjectId,
  level,
  chapter,
  kind,
}: {
  id: string;
  startTime: Date;
  endTime: Date;
  status: "UPCOMING" | "COMPLETED" | "CANCELLED";
  sessionNumber: number;
  subject: string;
  level: string | null;
  chapter: string | null;
  kind: "LESSON" | "FREESTYLE";
}) {
  const t = useT();
  const { lang } = useLanguage();
  const locale = dateLocale(lang);
  // Classes booked before subjects existed carry a name we can't resolve;
  // those simply show no subject rather than a wrong one.
  const subject = SUBJECTS.find((s) => s.id === subjectId) ?? null;
  const chapterInfo = findChapter(subjectId, level, chapter);
  const [cancelState, cancelAction, cancelPending] = useActionState(cancelBooking.bind(null, id), undefined);
  const now = new Date();
  const canStart =
    status === "UPCOMING" &&
    isWithinInterval(now, { start: subMinutes(startTime, START_WINDOW_MINUTES), end: endTime });
  const isPast = status !== "UPCOMING" || now > endTime;

  return (
    <div
      className={`flex items-center justify-between gap-4 rounded-xl border-l-4 border-y border-r border-y-border border-r-border bg-surface p-5 shadow-sm ${
        status === "UPCOMING" ? "border-l-primary" : "border-l-border"
      }`}
    >
      <div className="flex items-center gap-4">
        <div
          aria-hidden="true"
          className="flex h-12 w-12 shrink-0 items-center justify-center rounded-full bg-primary-tint text-2xl"
        >
          {subject?.emoji ?? "\u2211"}
        </div>
        <div>
          <span className="inline-flex flex-wrap items-center gap-1.5 text-xs font-medium text-muted">
            <span className="font-mono tracking-tight">
              {t("lesson.number", { n: String(sessionNumber).padStart(2, "0") })}
            </span>
            {subject && (
              <>
                <span aria-hidden="true">·</span>
                <span className="rounded-md bg-primary-tint px-1.5 py-0.5 text-primary">
                  {subject.name[lang]}
                </span>
              </>
            )}
          </span>
          <p className="mt-1 text-base font-semibold text-foreground font-mono">{format(startTime, "p", { locale })}</p>
          <p className="text-sm text-muted">{format(startTime, "PPPP", { locale })}</p>
          {/* A freestyle class follows no chapter, so it names itself. */}
          {kind === "FREESTYLE" ? (
            <p className="text-sm text-foreground">{t("lesson.freestyle")}</p>
          ) : (
            chapterInfo && <p className="text-sm text-foreground">{chapterInfo.title}</p>
          )}
          <p className="text-sm text-muted">{TUTOR_NAME}</p>
        </div>
      </div>

      <div className="flex shrink-0 flex-col items-end gap-2">
        {status === "UPCOMING" ? (
          <>
            <Link
              href={`/lesson/${id}`}
              aria-disabled={!canStart}
              className={`rounded-lg px-4 py-2 text-sm font-semibold transition-colors ${
                canStart
                  ? "bg-primary text-white hover:bg-primary-hover"
                  : "pointer-events-none bg-border text-muted"
              }`}
            >
              {t("lesson.startLesson")}
            </Link>
            {!isPast && (
              <form action={cancelAction} className="flex flex-col items-end">
                <button
                  type="submit"
                  disabled={cancelPending}
                  className="text-xs font-medium text-muted hover:text-danger disabled:cursor-not-allowed disabled:opacity-60"
                >
                  {cancelPending ? t("lesson.cancelling") : t("lesson.cancel")}
                </button>
                {cancelState?.error && <p className="mt-1 text-xs text-danger">{cancelState.error}</p>}
              </form>
            )}
          </>
        ) : (
          <span className="rounded-lg bg-border px-3 py-1 text-xs font-medium text-muted">
            {status === "COMPLETED" ? t("lesson.completed") : t("lesson.cancelled")}
          </span>
        )}
      </div>
    </div>
  );
}
