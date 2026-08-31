import { addDays, addMinutes, setHours, setMinutes, startOfDay, isBefore } from "date-fns";

export const LESSON_DURATION_MINUTES = 50;
/**
 * Lessons start on the hour and on the half hour. Because a lesson runs longer
 * than the step, two offered slots can overlap each other — 1:00 and 1:30 are
 * both bookable, but only one of them at a time. Callers that let a student
 * pick several slots at once must reject overlapping picks themselves;
 * `generateAvailableSlots` only knows about bookings already made.
 */
export const SLOT_STEP_MINUTES = 30;
const DAY_START_HOUR = 0;
const DAY_END_HOUR = 24;
const DAYS_AHEAD = 60;

export type Slot = {
  startTime: Date;
  endTime: Date;
};

type Booking = { startTime: Date; endTime: Date };

function overlaps(a: Slot, b: Booking) {
  return a.startTime < b.endTime && b.startTime < a.endTime;
}

/**
 * The Math tutor is an AI with no real capacity limit, so "availability" is
 * generated on the fly rather than stored: a fixed daily window split into
 * lesson slots, minus anything that overlaps the given student's own bookings.
 */
export function generateAvailableSlots(existingBookings: Booking[], now: Date = new Date()): Slot[] {
  const slots: Slot[] = [];

  for (let dayOffset = 0; dayOffset < DAYS_AHEAD; dayOffset++) {
    const day = addDays(startOfDay(now), dayOffset);
    let cursor = setMinutes(setHours(day, DAY_START_HOUR), 0);
    const dayEnd = setMinutes(setHours(day, DAY_END_HOUR), 0);

    while (isBefore(addMinutes(cursor, LESSON_DURATION_MINUTES), dayEnd) || +addMinutes(cursor, LESSON_DURATION_MINUTES) === +dayEnd) {
      const slot: Slot = { startTime: cursor, endTime: addMinutes(cursor, LESSON_DURATION_MINUTES) };

      const inThePast = isBefore(slot.startTime, now);
      const conflicts = existingBookings.some((b) => overlaps(slot, b));

      if (!inThePast && !conflicts) slots.push(slot);

      cursor = addMinutes(cursor, SLOT_STEP_MINUTES);
    }
  }

  return slots;
}

export function groupSlotsByDay(slots: Slot[]) {
  const groups = new Map<string, Slot[]>();
  for (const slot of slots) {
    const key = startOfDay(slot.startTime).toISOString();
    const existing = groups.get(key) ?? [];
    existing.push(slot);
    groups.set(key, existing);
  }
  return Array.from(groups.entries()).map(([day, daySlots]) => ({
    day: new Date(day),
    slots: daySlots,
  }));
}
