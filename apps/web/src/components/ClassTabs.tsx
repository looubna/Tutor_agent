"use client";

import { useRef } from "react";
import { format, isSameDay } from "date-fns";
import { LessonCard } from "@/components/LessonCard";
import { EmptyCalendar } from "@/components/EmptyCalendar";
import { useT, useLanguage } from "@/lib/i18n";
import { dateLocale } from "@/lib/dates";

export type ClassRow = {
  id: string;
  startTime: Date;
  endTime: Date;
  status: "UPCOMING" | "COMPLETED" | "CANCELLED";
  sessionNumber: number;
  subject: string;
  level: string | null;
  chapter: string | null;
  kind: "LESSON" | "FREESTYLE";
};

export type TabId = "scheduled" | "past";

/**
 * Scheduled and past lessons behind tabs. Picking a day in the calendar narrows
 * both lists to that day — the tabs stay put, so it stays obvious whether the
 * day holds an upcoming class, a finished one, or nothing.
 */
export function ClassTabs({
  scheduled,
  past,
  tab,
  onTabChange,
  selectedDay,
  onClearDay,
}: {
  scheduled: ClassRow[];
  past: ClassRow[];
  tab: TabId;
  onTabChange: (tab: TabId) => void;
  selectedDay: Date | null;
  onClearDay: () => void;
}) {
  const t = useT();
  const { lang } = useLanguage();
  const locale = dateLocale(lang);
  const tabsRef = useRef<HTMLDivElement>(null);

  const onDay = (rows: ClassRow[]) =>
    selectedDay ? rows.filter((r) => isSameDay(r.startTime, selectedDay)) : rows;

  const tabs = [
    { id: "scheduled" as const, label: t("dashboard.tabScheduled"), rows: onDay(scheduled) },
    { id: "past" as const, label: t("dashboard.tabPast"), rows: onDay(past) },
  ];
  const open = tabs.find((x) => x.id === tab) ?? tabs[0];

  const onKeyDown = (event: React.KeyboardEvent) => {
    if (event.key !== "ArrowRight" && event.key !== "ArrowLeft") return;
    event.preventDefault();
    const step = event.key === "ArrowRight" ? 1 : -1;
    const i = tabs.findIndex((x) => x.id === tab);
    const next = tabs[(i + step + tabs.length) % tabs.length];
    onTabChange(next.id);
    tabsRef.current?.querySelectorAll("button")[tabs.indexOf(next)]?.focus();
  };

  return (
    <>
      {selectedDay && (
        <div className="mt-6 flex flex-wrap items-center gap-3">
          <span className="rounded-full bg-primary-tint px-3 py-1.5 text-sm font-medium text-primary">
            {format(selectedDay, "EEEE, d MMMM yyyy", { locale })}
          </span>
          <button
            type="button"
            onClick={onClearDay}
            className="text-sm font-medium text-muted transition-colors hover:text-foreground"
          >
            {t("dashboard.showAll")}
          </button>
        </div>
      )}

      <div
        ref={tabsRef}
        role="tablist"
        onKeyDown={onKeyDown}
        className={`flex gap-6 border-b border-border ${selectedDay ? "mt-4" : "mt-6"}`}
      >
        {tabs.map((item) => {
          const active = item.id === tab;
          return (
            <button
              key={item.id}
              type="button"
              role="tab"
              id={`class-tab-${item.id}`}
              aria-selected={active}
              aria-controls={`class-panel-${item.id}`}
              tabIndex={active ? 0 : -1}
              onClick={() => onTabChange(item.id)}
              className={`-mb-px border-b-2 px-1 pb-3 text-sm font-medium transition-colors ${
                active
                  ? "border-primary text-primary"
                  : "border-transparent text-muted hover:text-foreground"
              }`}
            >
              {item.label}
              <span className="ml-1.5 text-xs text-muted">{item.rows.length}</span>
            </button>
          );
        })}
      </div>

      <div
        id={`class-panel-${open.id}`}
        role="tabpanel"
        aria-labelledby={`class-tab-${open.id}`}
        className="mt-6 flex flex-col gap-4"
      >
        {open.rows.length === 0 ? (
          <div className="flex flex-col items-center gap-4 rounded-xl border border-dashed border-border bg-surface p-8 text-center">
            <EmptyCalendar width={180} />
            <p className="text-sm text-muted">
              {selectedDay
                ? t("dashboard.dayEmpty")
                : tab === "scheduled"
                  ? t("dashboard.emptyMessage")
                  : t("dashboard.pastEmpty")}
            </p>
          </div>
        ) : (
          open.rows.map((row) => (
            <LessonCard
              key={row.id}
              id={row.id}
              startTime={row.startTime}
              endTime={row.endTime}
              status={row.status}
              sessionNumber={row.sessionNumber}
              subject={row.subject}
              level={row.level}
              chapter={row.chapter}
              kind={row.kind}
            />
          ))
        )}
      </div>
    </>
  );
}
