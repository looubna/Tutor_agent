"use client";

import { useState } from "react";
import { useT, useLanguage } from "@/lib/i18n";
import {
  addMonths,
  eachDayOfInterval,
  endOfMonth,
  endOfWeek,
  format,
  isSameDay,
  isSameMonth,
  startOfMonth,
  startOfWeek,
} from "date-fns";
import { dateLocale } from "@/lib/dates";

const WEEK_STARTS_ON = 1; // Monday, matching the booking calendar

/**
 * A month grid for the dashboard: which days already hold a lesson, with today
 * ringed. Picking a day filters the list beside it; picking it again clears
 * the filter. Navigation is free — a learner can look ahead or back.
 */
export function MonthCalendar({
  lessonDays,
  selectedDay,
  onSelectDay,
}: {
  lessonDays: Date[];
  selectedDay: Date | null;
  onSelectDay: (day: Date | null) => void;
}) {
  const t = useT();
  const { lang } = useLanguage();
  const locale = dateLocale(lang);
  const label = t("dashboard.calendar");
  const today = new Date();
  const [month, setMonth] = useState(() => startOfMonth(today));

  const days = eachDayOfInterval({
    start: startOfWeek(startOfMonth(month), { weekStartsOn: WEEK_STARTS_ON }),
    end: endOfWeek(endOfMonth(month), { weekStartsOn: WEEK_STARTS_ON }),
  });

  const weekdays = days.slice(0, 7);

  return (
    <section
      aria-label={label}
      className="rounded-xl border border-border bg-surface p-5 shadow-sm"
    >
      <header className="flex items-center justify-between">
        <button
          type="button"
          onClick={() => setMonth((m) => addMonths(m, -1))}
          aria-label={`${label} — ${format(addMonths(month, -1), "MMMM yyyy", { locale })}`}
          className="flex h-7 w-7 items-center justify-center rounded-full text-muted transition-colors hover:bg-primary-tint hover:text-foreground"
        >
          <Chevron direction="left" />
        </button>
        <h2 className="text-sm font-semibold text-foreground">{format(month, "MMMM yyyy", { locale })}</h2>
        <button
          type="button"
          onClick={() => setMonth((m) => addMonths(m, 1))}
          aria-label={`${label} — ${format(addMonths(month, 1), "MMMM yyyy", { locale })}`}
          className="flex h-7 w-7 items-center justify-center rounded-full text-muted transition-colors hover:bg-primary-tint hover:text-foreground"
        >
          <Chevron direction="right" />
        </button>
      </header>

      <div className="mt-4 grid grid-cols-7 gap-y-1 text-center">
        {weekdays.map((day) => (
          <abbr
            key={`h-${day.toISOString()}`}
            title={format(day, "EEEE", { locale })}
            className="text-[0.65rem] font-semibold uppercase tracking-wider text-muted no-underline"
          >
            {format(day, "EEEEE", { locale })}
          </abbr>
        ))}

        {days.map((day) => {
          const outside = !isSameMonth(day, month);
          const isToday = isSameDay(day, today);
          const hasLesson = lessonDays.some((d) => isSameDay(d, day));
          const isSelected = selectedDay !== null && isSameDay(day, selectedDay);
          return (
            <div key={day.toISOString()} className="flex justify-center py-0.5">
              <button
                type="button"
                onClick={() => onSelectDay(isSelected ? null : day)}
                aria-pressed={isSelected}
                aria-label={`${format(day, "d MMMM yyyy", { locale })} — ${
                  hasLesson ? t("dashboard.dayBooked") : t("dashboard.dayFree")
                }`}
                className={`relative flex h-8 w-8 items-center justify-center rounded-full text-sm transition-colors ${
                  outside ? "text-muted/40" : "text-foreground"
                } ${isToday && !isSelected ? "border border-primary font-semibold" : ""} ${
                  isSelected
                    ? "bg-primary font-semibold text-white"
                    : hasLesson && !outside
                      ? "bg-primary-tint font-semibold text-primary hover:bg-primary-tint/70"
                      : "hover:bg-primary-tint/60"
                }`}
              >
                {format(day, "d", { locale })}
                {hasLesson && !outside && (
                  <span
                    aria-hidden="true"
                    className={`absolute bottom-0.5 h-1 w-1 rounded-full ${
                      isSelected ? "bg-white" : "bg-primary"
                    }`}
                  />
                )}
              </button>
            </div>
          );
        })}
      </div>
    </section>
  );
}

function Chevron({ direction }: { direction: "left" | "right" }) {
  return (
    <svg viewBox="0 0 24 24" fill="none" className="h-4 w-4" aria-hidden="true">
      <path
        d={direction === "left" ? "m15 6-6 6 6 6" : "m9 6 6 6-6 6"}
        stroke="currentColor"
        strokeWidth="1.8"
        strokeLinecap="round"
        strokeLinejoin="round"
      />
    </svg>
  );
}
