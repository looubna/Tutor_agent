import { verifySession } from "@/lib/dal";
import { prisma } from "@/lib/prisma";
import { generateAvailableSlots } from "@/lib/slots";
import { CalendarSlotPicker } from "@/components/CalendarSlotPicker";
import { T } from "@/components/T";

export default async function BookPage() {
  const { userId } = await verifySession();

  const existingBookings = await prisma.booking.findMany({
    where: { studentId: userId, status: "UPCOMING" },
    select: { startTime: true, endTime: true },
  });

  const slots = generateAvailableSlots(existingBookings);

  return (
    <div className="mx-auto max-w-5xl">
      <T k="book.heading" as="h1" className="text-2xl font-semibold text-foreground font-display" />
      <T k="book.subheading" as="p" className="mt-1 text-sm text-muted" />

      <div className="mt-6">
        <CalendarSlotPicker
          availableSlots={slots.map((s) => ({
            startTime: s.startTime.toISOString(),
            endTime: s.endTime.toISOString(),
          }))}
          existingBookings={existingBookings.map((b) => ({
            startTime: b.startTime.toISOString(),
            endTime: b.endTime.toISOString(),
          }))}
        />
      </div>
    </div>
  );
}
