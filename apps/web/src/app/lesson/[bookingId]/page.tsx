import { notFound, redirect } from "next/navigation";
import { isWithinInterval, subMinutes } from "date-fns";
import { getCurrentUser, verifySession } from "@/lib/dal";
import { prisma } from "@/lib/prisma";
import { CallScreen } from "@/components/CallScreen";
import { SUBJECTS } from "@/lib/subjects";
import { HelpLanguageGate } from "@/components/HelpLanguageGate";
import { lessonIdFor } from "@/lib/worksheet/lessonId";
import { levelsFor } from "@/lib/curriculum";
import { speechLocale } from "@/lib/locales";
import { currentDoc } from "@/lib/worksheet/store";

const START_WINDOW_MINUTES = 10;

export default async function LessonPage({
  params,
}: {
  params: Promise<{ bookingId: string }>;
}) {
  const { bookingId } = await params;
  const { userId } = await verifySession();

  const booking = await prisma.booking.findFirst({
    where: { id: bookingId, studentId: userId },
    include: { messages: { orderBy: { createdAt: "asc" } } },
  });

  if (!booking) {
    notFound();
  }

  if (booking.status !== "UPCOMING") {
    redirect("/dashboard");
  }

  const now = new Date();
  const canJoin = isWithinInterval(now, {
    start: subMinutes(booking.startTime, START_WINDOW_MINUTES),
    end: booking.endTime,
  });

  if (!canJoin) {
    redirect("/dashboard");
  }

  const initialMessages = booking.messages.map((m) => ({
    role: m.role,
    content: m.content,
  }));

  // English here rather than the viewer's language: it labels the tutor's video
  // beside a lesson that is itself in one fixed language.
  const subject = SUBJECTS.find((s) => s.id === booking.subject);

  // The tutor needs to know which language it may rescue in before it says its
  // first word, and someone who started a class straight from the course page
  // was never asked. Ask now rather than guessing English.
  const user = await getCurrentUser();
  if (subject?.group === "language" && !user?.supportLanguage) {
    return <HelpLanguageGate subjectName={subject.name.en} />;
  }

  // Whether this class has a paper at all, so the call can open on it instead
  // of on an apology. A freestyle conversation follows no chapter and has none.
  const lessonId = lessonIdFor(booking);
  const hasPaper = lessonId ? Boolean(await currentDoc(lessonId)) : false;

  // What the class is spoken in. A German lesson is German because the subject
  // says so; a Sixième maths lesson is French because its programme is, not
  // because the student's interface happens to be.
  const level = levelsFor(booking.subject).find((l) => l.id === booking.level);
  const voiceTag = speechLocale(subject?.locale, level?.locale, user?.supportLanguage);

  return (
    <CallScreen
      bookingId={booking.id}
      initialMessages={initialMessages}
      subjectName={subject?.name.en ?? null}
      studentName={user?.name ?? ""}
      studentImage={user?.image ?? null}
      hasPaper={hasPaper}
      voiceTag={voiceTag}
    />
  );
}
