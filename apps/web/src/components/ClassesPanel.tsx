"use client";

import { useState } from "react";
import { isSameDay, startOfDay } from "date-fns";
import { ClassTabs, type ClassRow, type TabId } from "@/components/ClassTabs";
import { MonthCalendar } from "@/components/MonthCalendar";
import { useT } from "@/lib/i18n";

/**
 * Owns the day picked in the calendar and which tab is open. Picking a day
 * narrows both lists to it and opens whichever tab actually holds something
 * that day, so clicking a future date lands on Scheduled and a past one on
 * Past without the learner having to switch by hand.
 *
 * This page only reviews classes — booking lives under its own nav entries.
 */
export function ClassesPanel({
  scheduled,
  past,
}: {
  scheduled: ClassRow[];
  past: ClassRow[];
}) {
  const t = useT();
  const [selectedDay, setSelectedDay] = useState<Date | null>(null);
  const [tab, setTab] = useState<TabId>("scheduled");

  const all = [...scheduled, ...past];

  function pickDay(day: Date | null) {
    setSelectedDay(day);
    if (!day) return;
    // Open the tab that actually has something on that day; if neither does,
    // fall back to which side of today the day sits on.
    const hasScheduled = scheduled.some((r) => isSameDay(r.startTime, day));
    const hasPast = past.some((r) => isSameDay(r.startTime, day));
    if (hasScheduled) setTab("scheduled");
    else if (hasPast) setTab("past");
    else setTab(startOfDay(day) < startOfDay(new Date()) ? "past" : "scheduled");
  }

  return (
    <div className="mx-auto flex max-w-6xl flex-col gap-8 lg:flex-row">
      <div className="flex-1">
        <h1 className="text-2xl font-semibold text-foreground font-display">
          {t("dashboard.heading")}
        </h1>

        <ClassTabs
          scheduled={scheduled}
          past={past}
          tab={tab}
          onTabChange={setTab}
          selectedDay={selectedDay}
          onClearDay={() => setSelectedDay(null)}
        />
      </div>

      <div className="flex w-full shrink-0 flex-col gap-5 lg:w-80">
        <MonthCalendar
          lessonDays={all.map((row) => row.startTime)}
          selectedDay={selectedDay}
          onSelectDay={pickDay}
        />

      </div>
    </div>
  );
}
