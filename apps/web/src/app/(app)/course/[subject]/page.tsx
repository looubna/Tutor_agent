import { notFound } from "next/navigation";
import { CourseView } from "@/components/CourseView";
import { levelsFor } from "@/lib/curriculum";
import { SUBJECTS } from "@/lib/subjects";
import { verifySession } from "@/lib/dal";

export default async function Page({ params }: { params: Promise<{ subject: string }> }) {
  await verifySession();
  const { subject: id } = await params;
  const subject = SUBJECTS.find((s) => s.id === id);
  if (!subject) notFound();

  return (
    <div>
      <CourseView subject={subject} levels={levelsFor(subject.id)} />
    </div>
  );
}
