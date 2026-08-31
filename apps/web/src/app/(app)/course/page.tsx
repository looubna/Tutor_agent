import { verifySession } from "@/lib/dal";
import { T } from "@/components/T";

export default async function CoursePage() {
  await verifySession();

  return (
    <div className="rounded-xl border border-dashed border-border bg-surface p-10 text-center">
      <T k="course.chooseHeading" as="h1" className="text-lg font-semibold text-foreground font-display" />
      <T k="course.pickSubject" as="p" className="mt-2 text-sm text-muted" />
    </div>
  );
}
