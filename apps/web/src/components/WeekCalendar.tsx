"use client";

import { useMemo, useState } from "react";
import Link from "next/link";
import {
  addDays,
  addWeeks,
  format,
  isSameDay,
  isSameMonth,
  isWithinInterval,
  startOfDay,
  startOfWeek,
  subMinutes,
} from "date-fns";

type Booking = {
  id: string;
  startTime: string;
  endTime: string;
  status: "UPCOMING" | "COMPLETED";
};

const HOURS = Array.from({ length: 24 }, (_, i) => i);
const START_WINDOW_MINUTES = 10;

function cellKey(day: Date, hour: number) {
  return `${format(day, "yyyy-MM-dd")}-${hour}`;
}

function formatWeekLabel(weekStart: Date, weekEnd: Date) {
  const sameMonth = isSameMonth(weekStart, weekEnd);
  const sameYear = weekStart.getFullYear() === weekEnd.getFullYear();
  if (sameMonth) return `${format(weekStart, "d")} – ${format(weekEnd, "d MMMM yyyy")}`;
  if (sameYear) return `${format(weekStart, "d MMM")} – ${format(weekEnd, "d MMM yyyy")}`;
  return `${format(weekStart, "d MMM yyyy")} – ${format(weekEnd, "d MMM yyyy")}`;
}

export function WeekCalendar({ bookings }: { bookings: Booking[] }) {
  const today = useMemo(() => startOfDay(new Date()), []);
  const [weekStart, setWeekStart] = useState(() => startOfWeek(today, { weekStartsOn: 1 }));

  const weekDays = useMemo(() => Array.from({ length: 7 }, (_, i) => addDays(weekStart, i)), [weekStart]);
  const weekEnd = weekDays[6];

  const bookingByCell = useMemo(() => {
    const map = new Map<string, Booking>();
    for (const b of bookings) {
      const start = new Date(b.startTime);
      map.set(cellKey(startOfDay(start), start.getHours()), b);
    }
    return map;
  }, [bookings]);

  const now = useMemo(() => new Date(), []);

  return (
    <div className="rounded-xl border border-border bg-surface p-6 shadow-sm">
      <div className="flex items-center justify-between">
        <button
          type="button"
          onClick={() => setWeekStart((w) => addWeeks(w, -1))}
          aria-label="Previous week"
          className="flex h-8 w-8 items-center justify-center rounded-full text-foreground transition-colors hover:bg-primary-tint focus-visible:outline-2 focus-visible:outline-primary"
        >
          <ChevronIcon direction="left" />
        </button>
        <span className="font-display text-sm font-semibold text-foreground">
          {formatWeekLabel(weekStart, weekEnd)}
        </span>
        <button
          type="button"
          onClick={() => setWeekStart((w) => addWeeks(w, 1))}
          aria-label="Next week"
          className="flex h-8 w-8 items-center justify-center rounded-full text-foreground transition-colors hover:bg-primary-tint focus-visible:outline-2 focus-visible:outline-primary"
        >
          <ChevronIcon direction="right" />
        </button>
      </div>

      <div className="mt-4 overflow-x-auto">
        <div className="min-w-[720px]">
          <div className="grid grid-cols-[56px_repeat(7,1fr)]">
            <div />
            {weekDays.map((day) => (
              <div key={day.toISOString()} className="flex flex-col items-center gap-0.5 pb-2">
                <span
                  className={`text-xs font-semibold ${isSameDay(day, today) ? "text-primary" : "text-foreground"}`}
                >
                  {format(day, "EEE")}
                </span>
                <span className="font-mono text-[11px] text-muted">{format(day, "d.M")}</span>
              </div>
            ))}
          </div>

          <div className="grid grid-cols-[56px_repeat(7,1fr)]">
            {HOURS.flatMap((hour) => [
              <div
                key={`label-${hour}`}
                className="border-t border-border py-1 pr-2 text-right font-mono text-[11px] text-muted"
              >
                {String(hour).padStart(2, "0")}:00
              </div>,
              ...weekDays.map((day) => {
                const booking = bookingByCell.get(cellKey(day, hour));
                return (
                  <Cell
                    key={cellKey(day, hour)}
                    booking={booking}
                    now={now}
                  />
                );
              }),
            ])}
          </div>
        </div>
      </div>

      <div className="mt-4 flex items-center gap-2 text-xs text-muted">
        <span className="inline-block h-0.5 w-4 rounded-full bg-primary" aria-hidden="true" />
        booked lesson
      </div>
    </div>
  );
}

function Cell({ booking, now }: { booking: Booking | undefined; now: Date }) {
  if (!booking) {
    return <div className="min-h-[52px] border-t border-l border-border bg-background" />;
  }

  const isUpcoming = booking.status === "UPCOMING";
  const start = new Date(booking.startTime);
  const canJoin =
    isUpcoming &&
    isWithinInterval(now, { start: subMinutes(start, START_WINDOW_MINUTES), end: new Date(booking.endTime) });

  const content = (
    <div
      className={`flex min-h-[52px] flex-col items-center justify-center gap-1 border-t border-l border-border px-1 py-2 text-center ${
        isUpcoming ? "border-l-2 border-l-primary bg-primary-tint" : "bg-board/10"
      }`}
    >
      <span
        className={`flex h-6 w-6 items-center justify-center rounded-full font-display text-xs font-semibold ${
          isUpcoming ? "bg-primary text-white" : "bg-board text-board-foreground"
        }`}
        aria-hidden="true"
      >
        ∑
      </span>
      <span className="text-[11px] font-medium leading-tight text-foreground">AI Math Tutor</span>
      <span className="rounded bg-surface px-1 text-[10px] text-muted">Math</span>
    </div>
  );

  if (canJoin) {
    return (
      <Link href={`/lesson/${booking.id}`} className="block focus-visible:outline-2 focus-visible:outline-primary">
        {content}
      </Link>
    );
  }

  return content;
}

function ChevronIcon({ direction }: { direction: "left" | "right" }) {
  return (
    <svg viewBox="0 0 20 20" fill="none" className="h-4 w-4" aria-hidden="true">
      <path
        d={direction === "left" ? "M12.5 5L7.5 10l5 5" : "M7.5 5l5 5-5 5"}
        stroke="currentColor"
        strokeWidth="1.7"
        strokeLinecap="round"
        strokeLinejoin="round"
      />
    </svg>
  );
}
