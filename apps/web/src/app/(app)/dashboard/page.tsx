import Link from "next/link";
import { format } from "date-fns";
import { verifySession } from "@/lib/dal";
import { prisma } from "@/lib/prisma";
import { generateAvailableSlots } from "@/lib/slots";
import { LessonCard } from "@/components/LessonCard";
import { PlottedCurve } from "@/components/PlottedCurve";
import { T } from "@/components/T";

export default async function DashboardPage() {
  const { userId } = await verifySession();

  const bookings = await prisma.booking.findMany({
    where: { studentId: userId },
    orderBy: { startTime: "asc" },
  });

  const sessionNumbers = new Map(bookings.map((b, i) => [b.id, i + 1]));

  const upcoming = bookings.filter((b) => b.status === "UPCOMING");
  const past = bookings.filter((b) => b.status === "COMPLETED");

  const nextSlots = generateAvailableSlots(
    upcoming.map((b) => ({ startTime: b.startTime, endTime: b.endTime }))
  ).slice(0, 5);

  return (
    <div className="mx-auto flex max-w-6xl gap-8">
      <div className="flex-1">
        <T k="dashboard.heading" as="h1" className="text-2xl font-semibold text-foreground font-display" />

        <div className="mt-6 flex flex-col gap-4">
          {upcoming.length === 0 ? (
            <div className="flex flex-col items-center gap-4 rounded-xl border border-dashed border-border bg-surface p-8 text-center">
              <PlottedCurve className="h-16 w-40 text-accent" />
              <T k="dashboard.emptyMessage" as="p" className="text-sm text-muted" />
              <Link
                href="/book"
                className="inline-block rounded-lg bg-primary px-4 py-2 text-sm font-semibold text-white hover:bg-primary-hover"
              >
                <T k="dashboard.emptyCta" />
              </Link>
            </div>
          ) : (
            upcoming.map((b) => (
              <LessonCard
                key={b.id}
                id={b.id}
                startTime={b.startTime}
                endTime={b.endTime}
                status={b.status}
                sessionNumber={sessionNumbers.get(b.id)!}
              />
            ))
          )}
        </div>

        {past.length > 0 && (
          <div className="mt-10">
            <h2 className="text-lg font-semibold text-foreground font-display">Previous lessons</h2>
            <div className="mt-4 flex flex-col gap-4">
              {past.map((b) => (
                <LessonCard
                  key={b.id}
                  id={b.id}
                  startTime={b.startTime}
                  endTime={b.endTime}
                  status={b.status}
                  sessionNumber={sessionNumbers.get(b.id)!}
                />
              ))}
            </div>
          </div>
        )}
      </div>

      <div className="w-80 shrink-0">
        <div className="rounded-xl border border-border bg-surface p-5 shadow-sm">
          <h2 className="text-sm font-semibold text-foreground">My next available slots</h2>
          <div className="mt-3 flex flex-col gap-3">
            {nextSlots.map((slot) => (
              <div key={slot.startTime.toISOString()}>
                <p className="text-xs font-medium text-muted">{format(slot.startTime, "EEE, M/d")}</p>
                <p className="text-sm text-foreground font-mono">
                  {format(slot.startTime, "h:mm")} – {format(slot.endTime, "h:mm a")}
                </p>
              </div>
            ))}
          </div>
          <Link
            href="/book"
            className="mt-4 block w-full rounded-lg bg-primary py-2 text-center text-sm font-semibold text-white hover:bg-primary-hover"
          >
            Book a lesson
          </Link>
        </div>
      </div>
    </div>
  );
}
