import { notFound, redirect } from "next/navigation";
import { isWithinInterval, subMinutes } from "date-fns";
import { verifySession } from "@/lib/dal";
import { prisma } from "@/lib/prisma";
import { CallScreen } from "@/components/CallScreen";

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

  return <CallScreen bookingId={booking.id} initialMessages={initialMessages} />;
}
