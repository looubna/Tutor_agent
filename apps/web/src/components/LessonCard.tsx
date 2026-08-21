"use client";

import Link from "next/link";
import { useActionState } from "react";
import { format, isWithinInterval, subMinutes } from "date-fns";
import { cancelBooking } from "@/app/actions/booking";
import { useT } from "@/lib/i18n";

const START_WINDOW_MINUTES = 10;

export function LessonCard({
  id,
  startTime,
  endTime,
  status,
  sessionNumber,
}: {
  id: string;
  startTime: Date;
  endTime: Date;
  status: "UPCOMING" | "COMPLETED" | "CANCELLED";
  sessionNumber: number;
}) {
  const t = useT();
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
        <div className="flex h-12 w-12 shrink-0 items-center justify-center rounded-full bg-primary-tint text-lg font-semibold text-primary font-display">
          ∑
        </div>
        <div>
          <span className="inline-flex items-center gap-1.5 text-xs font-medium text-muted">
            <span className="font-mono tracking-tight">
              {t("lesson.number", { n: String(sessionNumber).padStart(2, "0") })}
            </span>
            <span aria-hidden="true">·</span>
            <span className="rounded-md bg-primary-tint px-1.5 py-0.5 text-primary">Math</span>
          </span>
          <p className="mt-1 text-base font-semibold text-foreground font-mono">{format(startTime, "h:mm a")}</p>
          <p className="text-sm text-muted">{format(startTime, "EEEE, MMMM d, yyyy")}</p>
          <p className="text-sm text-muted">AI Math Tutor</p>
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
