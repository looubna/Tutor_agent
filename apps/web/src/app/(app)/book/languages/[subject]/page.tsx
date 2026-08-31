import { notFound } from "next/navigation";
import { verifySession } from "@/lib/dal";
import { prisma } from "@/lib/prisma";
import { generateAvailableSlots } from "@/lib/slots";
import { ChapterPicker } from "@/components/ChapterPicker";
import { levelsFor } from "@/lib/curriculum";
import { LANGUAGE_SUBJECTS } from "@/lib/subjects";

export default async function Page({ params }: { params: Promise<{ subject: string }> }) {
  const { userId } = await verifySession();
  const { subject: id } = await params;
  const subject = LANGUAGE_SUBJECTS.find((s) => s.id === id);
  if (!subject) notFound();

  const existingBookings = await prisma.booking.findMany({
    where: { studentId: userId, status: "UPCOMING" },
    select: { startTime: true, endTime: true },
  });
  const slots = generateAvailableSlots(existingBookings);
  const iso = (d: { startTime: Date; endTime: Date }) => ({
    startTime: d.startTime.toISOString(),
    endTime: d.endTime.toISOString(),
  });

  return (
    <div className="mx-auto max-w-7xl">
      <ChapterPicker
        subject={subject}
        levels={levelsFor(subject.id)}
        availableSlots={slots.map(iso)}
        existingBookings={existingBookings.map(iso)}
      />
    </div>
  );
}
