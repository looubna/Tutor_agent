/**
 * Put a lesson on the clock right now, so it can actually be opened.
 *
 *     npx tsx --env-file=.env --conditions=react-server scripts/lesson-now.ts \
 *       [email] [chapter] [lesson] [subject] [level]
 *
 * The lesson page only lets you in from ten minutes before a booking starts
 * until it ends (`START_WINDOW_MINUTES`), which is right for students and
 * useless for testing: anything you book through the UI is in the future, so
 * opening it redirects you to the dashboard.
 *
 * Cancels any other lesson that would overlap, so this can be run repeatedly.
 */
import { prisma } from "../src/lib/prisma";

const MINUTES = 60 * 1000;

async function main() {
  // The lesson matters: a chapter's first lesson is only one of its three, and
  // the paper and the prepared material are per lesson, not per chapter.
  const [
    email = "looubnaenakhli@gmail.com",
    chapter = "classroom",
    lesson = "l1",
    subject = "german",
    level = "a1-1",
  ] = process.argv.slice(2);

  const user = await prisma.user.findUnique({ where: { email } });
  if (!user) {
    const known = await prisma.user.findMany({ select: { email: true } });
    throw new Error(`No user ${email}. Known: ${known.map((u) => u.email).join(", ")}`);
  }

  const startTime = new Date(Date.now() - 2 * MINUTES);
  const endTime = new Date(Date.now() + 50 * MINUTES);

  await prisma.booking.updateMany({
    where: { studentId: user.id, status: "UPCOMING", endTime: { gte: startTime } },
    data: { status: "CANCELLED" },
  });

  const booking = await prisma.booking.create({
    data: {
      studentId: user.id, subject, level, chapter, lesson,
      kind: "LESSON", startTime, endTime,
    },
  });

  console.log(`\n  http://localhost:3000/lesson/${booking.id}\n`);
  console.log(`  ${user.name} · ${subject} ${level} · ${chapter}.${lesson} · open until ${endTime.toLocaleTimeString()}\n`);
}

main().catch((err) => { console.error(err.message); process.exit(1); });
