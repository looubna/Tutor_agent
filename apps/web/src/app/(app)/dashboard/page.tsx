import { verifySession } from "@/lib/dal";
import { prisma } from "@/lib/prisma";
import { ClassesPanel } from "@/components/ClassesPanel";

export default async function DashboardPage() {
  const { userId } = await verifySession();

  const bookings = await prisma.booking.findMany({
    where: { studentId: userId },
    orderBy: { startTime: "asc" },
  });

  const sessionNumbers = new Map(bookings.map((b, i) => [b.id, i + 1]));
  const row = (b: (typeof bookings)[number]) => ({
    id: b.id,
    startTime: b.startTime,
    endTime: b.endTime,
    status: b.status as "UPCOMING" | "COMPLETED" | "CANCELLED",
    sessionNumber: sessionNumbers.get(b.id)!,
    subject: b.subject,
    level: b.level,
    chapter: b.chapter,
    kind: b.kind as "LESSON" | "FREESTYLE",
  });

  const upcoming = bookings.filter((b) => b.status === "UPCOMING");
  const past = bookings.filter((b) => b.status === "COMPLETED");


  return (
    <ClassesPanel
      scheduled={upcoming.map(row)}
      past={past.map(row).reverse()}
    />
  );
}
