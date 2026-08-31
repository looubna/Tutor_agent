"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { useLanguage, useT } from "@/lib/i18n";
import { LANGUAGE_SUBJECTS, SCIENCE_SUBJECTS, type Subject } from "@/lib/subjects";

/**
 * The subject list, kept alongside the course itself rather than on a page of
 * its own — so switching subject is one click, not a trip back and forward.
 */
export function CourseRail() {
  const t = useT();
  const { lang } = useLanguage();
  const pathname = usePathname();

  const groups = [
    { label: t("course.languages"), subjects: LANGUAGE_SUBJECTS },
    { label: t("course.sciences"), subjects: SCIENCE_SUBJECTS },
  ];

  const isActive = (subject: Subject) =>
    pathname === `/course/${subject.id}` || pathname.startsWith(`/course/${subject.id}/`);

  return (
    <nav
      aria-label={t("nav.course")}
      className="w-full shrink-0 lg:sticky lg:top-24 lg:w-64"
    >
      {/* Its own scroll area so twelve subjects never push the course down. */}
      <div className="max-h-[22rem] overflow-y-auto overscroll-contain rounded-xl border border-border bg-surface p-2 lg:max-h-[32rem]">
        {groups.map((group) => (
          <div key={group.label} className="mb-2 last:mb-0">
            <p className="px-2 py-1.5 text-[0.65rem] font-semibold uppercase tracking-wider text-muted font-mono">
              {group.label}
            </p>
            <ul>
              {group.subjects.map((subject) => {
                const active = isActive(subject);
                return (
                  <li key={subject.id}>
                    <Link
                      href={`/course/${subject.id}`}
                      aria-current={active ? "page" : undefined}
                      className={`flex items-center gap-2.5 rounded-lg px-2 py-2 text-sm transition-colors ${
                        active
                          ? "bg-primary-tint font-semibold text-primary"
                          : "text-foreground hover:bg-primary-tint/60"
                      }`}
                    >
                      <span aria-hidden="true" className="text-lg">
                        {subject.emoji}
                      </span>
                      <span className="min-w-0 truncate">{subject.name[lang]}</span>
                    </Link>
                  </li>
                );
              })}
            </ul>
          </div>
        ))}
      </div>
    </nav>
  );
}
