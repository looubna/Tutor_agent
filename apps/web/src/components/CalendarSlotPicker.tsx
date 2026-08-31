"use client";

import { useMemo, useState } from "react";
import {
  addDays,
  addMonths,
  addWeeks,
  endOfMonth,
  endOfWeek,
  format,
  isSameDay,
  isSameMonth,
  startOfDay,
  startOfMonth,
  startOfWeek,
} from "date-fns";
import type { Locale } from "date-fns";
import { bookSlots, type BookingContext } from "@/app/actions/booking";
import { dateLocale } from "@/lib/dates";
import { useLanguage, useT } from "@/lib/i18n";

type IsoSlot = { startTime: string; endTime: string };
type CartEntry = { startTime: string; endTime: string };

const REPEAT_OPTIONS = [0, 4, 8, 12] as const;

function dayKey(date: Date) {
  return startOfDay(date).toISOString();
}

function buildMonthMatrix(month: Date): Date[] {
  const start = startOfWeek(startOfMonth(month), { weekStartsOn: 1 });
  const end = endOfWeek(endOfMonth(month), { weekStartsOn: 1 });
  const days: Date[] = [];
  for (let cursor = start; cursor <= end; cursor = addDays(cursor, 1)) {
    days.push(cursor);
  }
  return days;
}

export function CalendarSlotPicker({
  availableSlots,
  existingBookings,
  context,
  stackSummary = false,
}: {
  availableSlots: IsoSlot[];
  existingBookings: IsoSlot[];
  /** What the booked class covers, recorded with each lesson. */
  context: BookingContext;
  /**
   * Put the basket under the calendar instead of beside it. Needed when the
   * picker sits in a column rather than across the page — the side-by-side
   * split keys off the viewport, not the space actually available.
   */
  stackSummary?: boolean;
}) {
  const t = useT();
  const { lang } = useLanguage();
  const locale = dateLocale(lang);
  /** Every date-fns call in this component needs the same locale. */
  const fmt = (date: Date | string, pattern: string) =>
    format(typeof date === "string" ? new Date(date) : date, pattern, { locale });

  const today = useMemo(() => startOfDay(new Date()), []);

  const slotsByDay = useMemo(() => {
    const map = new Map<string, IsoSlot[]>();
    for (const slot of availableSlots) {
      const key = dayKey(new Date(slot.startTime));
      const existing = map.get(key) ?? [];
      existing.push(slot);
      map.set(key, existing);
    }
    for (const list of map.values()) {
      list.sort((a, b) => a.startTime.localeCompare(b.startTime));
    }
    return map;
  }, [availableSlots]);

  const bookedDayKeys = useMemo(
    () => new Set(existingBookings.map((b) => dayKey(new Date(b.startTime)))),
    [existingBookings]
  );

  const availableTimeSet = useMemo(() => new Set(availableSlots.map((s) => s.startTime)), [availableSlots]);

  const firstAvailableDay = useMemo(() => {
    if (slotsByDay.has(dayKey(today))) return today;
    const sorted = [...availableSlots].sort((a, b) => a.startTime.localeCompare(b.startTime));
    return sorted.length > 0 ? startOfDay(new Date(sorted[0].startTime)) : null;
  }, [slotsByDay, today, availableSlots]);

  const [selectedDate, setSelectedDate] = useState<Date | null>(firstAvailableDay);
  const [focusMonth, setFocusMonth] = useState<Date>(startOfMonth(firstAvailableDay ?? today));
  const [cart, setCart] = useState<CartEntry[]>([]);
  const [repeatWeeks, setRepeatWeeks] = useState<(typeof REPEAT_OPTIONS)[number]>(0);
  const [skippedNote, setSkippedNote] = useState<string | null>(null);
  const [pending, setPending] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const cartKeys = useMemo(() => new Set(cart.map((c) => c.startTime)), [cart]);

  /**
   * Times start every half hour but a lesson runs 50 minutes, so picking 1:00
   * rules out 1:30. Those neighbours stay visible and go dim rather than
   * disappearing, so the row of times doesn't reshuffle under the cursor.
   */
  const cartRanges = useMemo(
    () => cart.map((c) => [Date.parse(c.startTime), Date.parse(c.endTime)] as const),
    [cart]
  );

  const clashesWithCart = (slot: IsoSlot) => {
    const start = Date.parse(slot.startTime);
    const end = Date.parse(slot.endTime);
    return cartRanges.some(([cartStart, cartEnd]) => start < cartEnd && cartStart < end);
  };

  const maxDay = addDays(today, 59);
  const atEarliestMonth = isSameMonth(focusMonth, today);
  const atLatestMonth = focusMonth >= startOfMonth(maxDay);

  const goPrevMonth = () => !atEarliestMonth && setFocusMonth((m) => addMonths(m, -1));
  const goNextMonth = () => !atLatestMonth && setFocusMonth((m) => addMonths(m, 1));

  const toggleCartSlot = (slot: IsoSlot) => {
    setError(null);
    setCart((prev) =>
      prev.some((c) => c.startTime === slot.startTime)
        ? prev.filter((c) => c.startTime !== slot.startTime)
        : [...prev, slot]
    );
  };

  const removeFromCart = (startTime: string) => {
    setCart((prev) => prev.filter((c) => c.startTime !== startTime));
  };

  const handleRepeatChange = (weeks: (typeof REPEAT_OPTIONS)[number]) => {
    setRepeatWeeks(weeks);
    setSkippedNote(null);
    if (weeks === 0 || cart.length === 0) return;

    const anchor = cart[cart.length - 1];
    const anchorStart = new Date(anchor.startTime);
    const additions: CartEntry[] = [];
    const skipped: string[] = [];
    const alreadyStaged = new Set(cart.map((c) => c.startTime));

    for (let w = 1; w <= weeks; w++) {
      const candidateStart = addWeeks(anchorStart, w);
      const key = candidateStart.toISOString();
      if (alreadyStaged.has(key)) continue;
      const lessonMs = new Date(anchor.endTime).getTime() - new Date(anchor.startTime).getTime();
      const candidateEnd = new Date(candidateStart.getTime() + lessonMs);
      const overlapsStaged = [...cart, ...additions].some(
        (entry) =>
          candidateStart.getTime() < Date.parse(entry.endTime) &&
          Date.parse(entry.startTime) < candidateEnd.getTime()
      );
      if (availableTimeSet.has(key) && !overlapsStaged) {
        additions.push({ startTime: key, endTime: candidateEnd.toISOString() });
        alreadyStaged.add(key);
      } else {
        skipped.push(fmt(candidateStart, "MMM d"));
      }
    }

    if (additions.length > 0) setCart((prev) => [...prev, ...additions]);
    if (skipped.length > 0) setSkippedNote(t("book.skipped", { days: skipped.join(", ") }));
  };

  const handleContinue = async () => {
    if (cart.length === 0) return;
    setPending(true);
    setError(null);
    const result = await bookSlots(cart.map((c) => c.startTime), context);
    if (result?.error) {
      setError(result.error);
      setPending(false);
    }
  };

  const selectedDaySlots = selectedDate ? (slotsByDay.get(dayKey(selectedDate)) ?? []) : [];
  const lastAdded = cart[cart.length - 1];

  return (
    <div className={`flex flex-col gap-8 ${stackSummary ? "" : "lg:flex-row"}`}>
      <div className="bg-grid-paper-light flex-1 rounded-xl border border-border bg-surface p-6 shadow-sm">
        <div className="flex items-center justify-between">
          <button
            type="button"
            onClick={goPrevMonth}
            disabled={atEarliestMonth}
            aria-label={t("book.prevMonth")}
            className="flex h-8 w-8 items-center justify-center rounded-full text-foreground transition-colors hover:bg-primary-tint disabled:cursor-not-allowed disabled:opacity-30 disabled:hover:bg-transparent focus-visible:outline-2 focus-visible:outline-primary"
          >
            <ChevronIcon direction="left" />
          </button>
          <div className="flex flex-1 justify-around px-2">
            <span className="font-display text-sm font-semibold text-foreground">
              {fmt(focusMonth, "MMMM yyyy")}
            </span>
            <span className="hidden font-display text-sm font-semibold text-foreground md:inline">
              {fmt(addMonths(focusMonth, 1), "MMMM yyyy")}
            </span>
          </div>
          <button
            type="button"
            onClick={goNextMonth}
            disabled={atLatestMonth}
            aria-label={t("book.nextMonth")}
            className="flex h-8 w-8 items-center justify-center rounded-full text-foreground transition-colors hover:bg-primary-tint disabled:cursor-not-allowed disabled:opacity-30 disabled:hover:bg-transparent focus-visible:outline-2 focus-visible:outline-primary"
          >
            <ChevronIcon direction="right" />
          </button>
        </div>

        <div className="mt-4 grid grid-cols-1 gap-8 md:grid-cols-2">
          <MonthGrid
            month={focusMonth}
            today={today}
            selectedDate={selectedDate}
            slotsByDay={slotsByDay}
            bookedDayKeys={bookedDayKeys}
            onSelectDay={setSelectedDate}
            locale={locale}
          />
          <MonthGrid
            month={addMonths(focusMonth, 1)}
            today={today}
            selectedDate={selectedDate}
            slotsByDay={slotsByDay}
            bookedDayKeys={bookedDayKeys}
            onSelectDay={setSelectedDate}
            locale={locale}
            className="hidden md:block"
          />
        </div>

        <div className="mt-4 flex items-center gap-2 text-xs text-muted">
          <span className="inline-block h-0.5 w-4 rounded-full bg-accent-ink" aria-hidden="true" />
          {t("book.bookedLesson")}
        </div>

        <div className="mt-8 border-t border-border pt-6">
          {selectedDate ? (
            <>
              <h2 className="font-display text-lg font-semibold text-foreground">
                {fmt(selectedDate, "EEEE, MMMM d")}
              </h2>
              <p className="mt-1 text-xs text-muted">{t("book.lessonLength")}</p>

              {selectedDaySlots.length === 0 ? (
                <p className="mt-4 text-sm text-muted">{t("book.noTimesLeft")}</p>
              ) : (
                <div className="mt-4 grid grid-cols-3 gap-2 sm:grid-cols-4 md:grid-cols-5">
                  {selectedDaySlots.map((slot) => {
                    const inCart = cartKeys.has(slot.startTime);
                    const clashes = !inCart && clashesWithCart(slot);
                    return (
                      <button
                        key={slot.startTime}
                        type="button"
                        onClick={() => toggleCartSlot(slot)}
                        disabled={clashes}
                        title={clashes ? t("book.slotClash") : undefined}
                        aria-pressed={inCart}
                        className={`rounded-lg border px-3 py-2 font-mono text-sm font-medium transition-colors focus-visible:outline-2 focus-visible:outline-primary ${
                          inCart
                            ? "border-primary bg-primary text-white"
                            : clashes
                              ? "cursor-not-allowed border-border/60 bg-surface text-muted/40"
                              : "border-border bg-surface text-foreground hover:border-primary"
                        }`}
                      >
                        {fmt(slot.startTime, "p")}
                      </button>
                    );
                  })}
                </div>
              )}
            </>
          ) : (
            <p className="text-sm text-muted">{t("book.noSlots")}</p>
          )}
        </div>
      </div>

      <div className={`w-full shrink-0 ${stackSummary ? "" : "lg:w-80"}`}>
        <div className="rounded-xl border border-border bg-surface p-5 shadow-sm">
          <div className="flex items-center justify-between">
            <h2 className="font-display text-sm font-semibold text-foreground">{t("book.selected")}</h2>
            <span className="rounded-full bg-primary-tint px-2 py-0.5 font-mono text-xs font-semibold text-primary">
              {cart.length}
            </span>
          </div>

          {cart.length === 0 ? (
            <p className="mt-4 text-sm text-muted">{t("book.emptyCart")}</p>
          ) : (
            <ul className="mt-4 flex flex-col gap-2">
              {cart.map((entry) => (
                <li
                  key={entry.startTime}
                  className="flex items-center justify-between gap-2 rounded-lg border border-border px-3 py-2"
                >
                  <div>
                    <p className="text-sm font-medium text-foreground">
                      {fmt(entry.startTime, "EEE, MMM d")}
                    </p>
                    <p className="font-mono text-xs text-muted">
                      {fmt(entry.startTime, "p")} – {fmt(entry.endTime, "p")}
                    </p>
                  </div>
                  <button
                    type="button"
                    onClick={() => removeFromCart(entry.startTime)}
                    aria-label={t("book.removeSlot", { when: fmt(entry.startTime, "EEEE, MMMM d, p") })}
                    className="shrink-0 rounded-md p-1.5 text-muted transition-colors hover:bg-danger/10 hover:text-danger focus-visible:outline-2 focus-visible:outline-primary"
                  >
                    <TrashIcon />
                  </button>
                </li>
              ))}
            </ul>
          )}

          {cart.length > 0 && lastAdded && (
            <div className="mt-4 border-t border-border pt-4">
              <label htmlFor="repeat" className="mb-1 block text-xs font-medium text-muted">
                {t("book.repeatsOn", { day: fmt(lastAdded.startTime, "EEEE") })}
              </label>
              <select
                id="repeat"
                value={repeatWeeks}
                onChange={(e) => handleRepeatChange(Number(e.target.value) as (typeof REPEAT_OPTIONS)[number])}
                className="w-full rounded-lg border border-border bg-surface px-3 py-2 text-sm text-foreground outline-none focus:border-primary"
              >
                {REPEAT_OPTIONS.map((weeks) => (
                  <option key={weeks} value={weeks}>
                    {weeks === 0 ? t("book.noRepeat") : t("book.repeatWeeks", { n: weeks })}
                  </option>
                ))}
              </select>
              {skippedNote && <p className="mt-2 text-xs text-muted">{skippedNote}</p>}
            </div>
          )}

          {error && <p className="mt-4 text-sm text-danger">{error}</p>}

          <button
            type="button"
            onClick={handleContinue}
            disabled={cart.length === 0 || pending}
            className="mt-4 w-full rounded-lg bg-primary py-2.5 text-sm font-semibold text-white transition-colors hover:bg-primary-hover disabled:cursor-not-allowed disabled:opacity-50"
          >
            {pending ? t("book.booking") : t("book.continue")}
          </button>
        </div>
      </div>
    </div>
  );
}

function MonthGrid({
  month,
  today,
  selectedDate,
  slotsByDay,
  bookedDayKeys,
  onSelectDay,
  locale,
  className,
}: {
  month: Date;
  today: Date;
  selectedDate: Date | null;
  slotsByDay: Map<string, IsoSlot[]>;
  bookedDayKeys: Set<string>;
  onSelectDay: (day: Date) => void;
  locale: Locale;
  className?: string;
}) {
  const days = useMemo(() => buildMonthMatrix(month), [month]);
  // Monday-first row of weekday initials, named in the interface language.
  const weekdays = useMemo(
    () => buildMonthMatrix(month).slice(0, 7).map((day) => format(day, "EEEEEE", { locale })),
    [month, locale]
  );

  return (
    <div className={className}>
      <div className="grid grid-cols-7 text-center text-xs font-medium text-muted">
        {weekdays.map((label, i) => (
          <span key={i}>{label}</span>
        ))}
      </div>
      <div className="mt-1 grid grid-cols-7 gap-y-1">
        {days.map((day) => {
          if (!isSameMonth(day, month)) {
            return <div key={day.toISOString()} className="h-9 w-9" />;
          }

          const key = dayKey(day);
          const hasSlots = slotsByDay.has(key);
          const isBooked = bookedDayKeys.has(key);
          const isSelected = !!selectedDate && isSameDay(day, selectedDate);
          const isToday = isSameDay(day, today);

          return (
            <div key={day.toISOString()} className="flex justify-center py-0.5">
              <button
                type="button"
                disabled={!hasSlots}
                onClick={() => onSelectDay(day)}
                aria-pressed={isSelected}
                className={`relative flex h-9 w-9 items-center justify-center rounded-full text-sm transition-colors focus-visible:outline-2 focus-visible:outline-primary ${
                  !hasSlots
                    ? "cursor-not-allowed text-muted/40"
                    : isSelected
                      ? "bg-primary font-semibold text-white"
                      : isToday
                        ? "border border-primary font-semibold text-primary hover:bg-primary-tint"
                        : "text-foreground hover:bg-primary-tint"
                }`}
              >
                {format(day, "d", { locale })}
                {isBooked && (
                  <span
                    className={`absolute bottom-0.5 h-0.5 w-4 rounded-full ${isSelected ? "bg-white" : "bg-accent-ink"}`}
                    aria-hidden="true"
                  />
                )}
              </button>
            </div>
          );
        })}
      </div>
    </div>
  );
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

function TrashIcon() {
  return (
    <svg viewBox="0 0 20 20" fill="none" className="h-4 w-4" aria-hidden="true">
      <path
        d="M4.5 6h11M8.5 6V4.5h3V6M6 6l.6 9a1 1 0 0 0 1 .9h4.8a1 1 0 0 0 1-.9L14 6"
        stroke="currentColor"
        strokeWidth="1.5"
        strokeLinecap="round"
        strokeLinejoin="round"
      />
    </svg>
  );
}
