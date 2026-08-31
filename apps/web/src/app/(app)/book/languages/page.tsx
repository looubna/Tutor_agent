import { verifySession } from "@/lib/dal";
import { SubjectChooser } from "@/components/SubjectChooser";
import { LANGUAGE_SUBJECTS } from "@/lib/subjects";
import { T } from "@/components/T";

export default async function BookLanguagePage() {
  await verifySession();

  return (
    <div className="mx-auto max-w-3xl">
      <T k="book.languagesHeading" as="h1" className="text-2xl font-semibold text-foreground font-display" />
      <T k="book.languagesSub" as="p" className="mt-1 text-sm text-muted" />
      <SubjectChooser subjects={LANGUAGE_SUBJECTS} />
    </div>
  );
}
