import { verifySession } from "@/lib/dal";
import { SubjectChooser } from "@/components/SubjectChooser";
import { SCIENCE_SUBJECTS } from "@/lib/subjects";
import { T } from "@/components/T";

export default async function BookSciencePage() {
  await verifySession();

  return (
    <div className="mx-auto max-w-3xl">
      <T k="book.sciencesHeading" as="h1" className="text-2xl font-semibold text-foreground font-display" />
      <T k="book.sciencesSub" as="p" className="mt-1 text-sm text-muted" />
      <SubjectChooser subjects={SCIENCE_SUBJECTS} />
    </div>
  );
}
