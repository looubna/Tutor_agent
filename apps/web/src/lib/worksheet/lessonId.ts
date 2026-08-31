import { findChapter, findLesson } from "@/lib/curriculum";

/**
 * The lesson a worksheet belongs to.
 *
 * One paper per lesson, not per chapter: "Hello and goodbye", "Spelling my name
 * out loud" and "der, die, das" are three lessons with three different jobs, and
 * one sheet covering all of them is a sheet that fits none of them. The specs
 * were written per lesson too — this is the id they are named by.
 */
export function worksheetIdFor(
  subject: string,
  level: string | null,
  chapter: string | null,
  lesson: string,
): string | null {
  if (!level || !chapter) return null;
  return findLesson(subject, level, chapter, lesson)
    ? `${subject}.${level}.${chapter}.${lesson}`
    : null;
}

/**
 * Which lesson a booked class is working on. A booking names a chapter, so
 * until it names a lesson too the class starts at the first one.
 */
export function lessonIdFor(booking: {
  subject: string;
  level: string | null;
  chapter: string | null;
  lesson?: string | null;
}): string | null {
  if (!booking.level || !booking.chapter) return null;
  const found = findChapter(booking.subject, booking.level, booking.chapter);
  if (!found) return null;
  const lesson = booking.lesson ?? found.lessons[0]?.id;
  return lesson ? `${booking.subject}.${booking.level}.${booking.chapter}.${lesson}` : null;
}
