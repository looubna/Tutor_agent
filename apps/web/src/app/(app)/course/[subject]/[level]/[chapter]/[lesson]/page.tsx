import Link from "next/link";
import { notFound } from "next/navigation";
import { verifySession } from "@/lib/dal";
import { findLesson } from "@/lib/curriculum";
import { SUBJECTS } from "@/lib/subjects";
import { T } from "@/components/T";
import { LessonMaterial } from "@/components/LessonMaterial";
import { currentDoc } from "@/lib/worksheet/store";
import { pdfFor } from "@/lib/worksheet/paper";
import { StartNowButton } from "@/components/StartNowButton";

export default async function Page({
  params,
}: {
  params: Promise<{ subject: string; level: string; chapter: string; lesson: string }>;
}) {
  await verifySession();
  const { subject: subjectId, level: levelId, chapter: chapterId, lesson: lessonId } = await params;

  const subject = SUBJECTS.find((s) => s.id === subjectId);
  const found = subject ? findLesson(subjectId, levelId, chapterId, lessonId) : null;
  if (!subject || !found) notFound();

  const { chapter, lesson } = found;
  const group = subject.group === "science" ? "sciences" : "languages";

  // One worksheet per lesson, written once and published. `lesson.material`
  // used to be a path to a publisher's PDF; those are gone (§5.0), and the
  // paper is now something we wrote and can serve to anybody studying it.
  // A generated maths lesson is a compiled PDF sitting in public/materials; a
  // language deck is a published LessonDoc rendered on request. Prefer the PDF
  // — it is the one somebody compiled and read before it was published.
  const worksheetId = `${subjectId}.${levelId}.${chapterId}.${lessonId}`;
  const pdf = pdfFor(worksheetId);
  const published = pdf ? null : await currentDoc(worksheetId);
  const paper = pdf
    ?? (published
      ? `/api/course/${subjectId}/${levelId}/${chapterId}/${lessonId}/paper`
      : null);

  return (
    <div>
      <Link
        href={`/course/${subject.id}`}
        className="inline-flex items-center gap-1.5 text-sm font-medium text-primary transition-colors hover:underline"
      >
        <span aria-hidden="true">←</span>
        <T k="course.back" />
      </Link>

      <article className="mt-6 rounded-xl border border-border bg-surface p-8">
        <p className="text-xs font-semibold uppercase tracking-wider text-muted font-mono">
          {chapter.title}
        </p>
        <h1 className="mt-2 text-2xl font-semibold text-foreground font-display">{lesson.title}</h1>
        {lesson.category && (
          <p className="mt-1 text-sm uppercase tracking-wider text-muted">{lesson.category}</p>
        )}

        {lesson.summary && (
          <p className="mt-5 text-base leading-relaxed text-foreground">{lesson.summary}</p>
        )}

        {lesson.objectives && lesson.objectives.length > 0 && (
          <>
            <p className="mt-6 text-sm font-semibold text-foreground">
              <T k="course.objectives" />
            </p>
            <ul className="mt-2 flex list-disc flex-col gap-1.5 pl-5">
              {lesson.objectives.map((objective) => (
                <li key={objective} className="text-sm leading-relaxed text-muted">
                  {objective}
                </li>
              ))}
            </ul>
          </>
        )}

        <div className="mt-8">
          <LessonMaterial material={paper} />
        </div>
      </article>

      <div className="mt-6 flex flex-wrap items-center gap-3">
        <StartNowButton
          context={{ subject: subject.id, level: levelId, chapter: chapter.id }}
          className="rounded-xl bg-primary px-6 py-3 text-sm font-semibold text-white transition-colors hover:bg-primary-hover disabled:opacity-60"
        />
        <Link
          href={`/book/${group}/${subject.id}`}
          className="rounded-xl border border-primary px-6 py-3 text-sm font-semibold text-primary transition-colors hover:bg-primary-tint"
        >
          <T k="course.book" />
        </Link>
      </div>
    </div>
  );
}
