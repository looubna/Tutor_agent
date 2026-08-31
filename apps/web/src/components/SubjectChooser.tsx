"use client";

import Link from "next/link";
import { useLanguage } from "@/lib/i18n";
import type { Subject } from "@/lib/subjects";

/**
 * The catalogue for one group — what a learner can actually book. Picking a
 * subject carries it through to the slot picker.
 */
export function SubjectChooser({
  subjects,
  linkTo = "book",
}: {
  subjects: Subject[];
  /**
   * Where a subject leads. A plain string rather than a callback, because a
   * Server Component cannot hand a function across to a Client Component.
   */
  linkTo?: "book" | "course";
}) {
  const { lang } = useLanguage();

  return (
    <ul className="mt-8 grid gap-3 sm:grid-cols-2">
      {subjects.map((subject) => (
        <li key={subject.id}>
          <Link
            href={
              linkTo === "course"
                ? `/course/${subject.id}`
                : `/book/${subject.group === "science" ? "sciences" : "languages"}/${subject.id}`
            }
            className="flex items-center gap-4 rounded-xl border border-border bg-surface px-4 py-4 transition-colors hover:border-primary"
          >
            <span
              aria-hidden="true"
              className="flex h-11 w-11 shrink-0 items-center justify-center rounded-lg bg-background text-2xl"
            >
              {subject.emoji}
            </span>
            <span className="min-w-0 flex-1">
              <span className="block truncate text-sm font-semibold text-foreground">
                {subject.name[lang]}
              </span>
              <span className="block truncate text-xs text-muted">
                {(subject.level ?? subject.note)[lang]}
              </span>
            </span>
            <span aria-hidden="true" className="shrink-0 text-muted">
              <svg viewBox="0 0 24 24" fill="none" className="h-4 w-4">
                <path
                  d="m9 6 6 6-6 6"
                  stroke="currentColor"
                  strokeWidth="1.8"
                  strokeLinecap="round"
                  strokeLinejoin="round"
                />
              </svg>
            </span>
          </Link>
        </li>
      ))}
    </ul>
  );
}
