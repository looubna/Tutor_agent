import { verifySession } from "@/lib/dal";
import { prisma } from "@/lib/prisma";
import { WeekCalendar } from "@/components/WeekCalendar";
import { T } from "@/components/T";

export default async function CalendarPage() {
  const { userId } = await verifySession();

  const bookings = await prisma.booking.findMany({
    where: { studentId: userId, status: { not: "CANCELLED" } },
    orderBy: { startTime: "asc" },
  });

  return (
    <div className="mx-auto max-w-5xl">
      <T k="calendar.heading" as="h1" className="text-2xl font-semibold text-foreground font-display" />
      <T k="calendar.subheading" as="p" className="mt-1 text-sm text-muted" />

      <div className="mt-6">
        <WeekCalendar
          bookings={bookings.map((b) => ({
            id: b.id,
            startTime: b.startTime.toISOString(),
            endTime: b.endTime.toISOString(),
            status: b.status as "UPCOMING" | "COMPLETED",
          }))}
        />
      </div>
    </div>
  );
}
