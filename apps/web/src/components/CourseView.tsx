"use client";

import Link from "next/link";
import { useState } from "react";
import { LiveLessonIcon } from "@/components/LiveLessonIcon";
import { StartNowButton } from "@/components/StartNowButton";
import { FreestyleCard } from "@/components/FreestyleCard";
import { useLanguage, useT } from "@/lib/i18n";
import { LevelMenu } from "@/components/LevelMenu";
import type { Level } from "@/lib/curriculum";
import type { Subject } from "@/lib/subjects";

/**
 * Hidden until the pointer is on the lesson, but still laid out — so the row
 * doesn't jump — and always shown where there is no hover to reveal it.
 */
const REVEAL =
  "invisible opacity-0 group-hover:visible group-hover:opacity-100 group-focus-within:visible group-focus-within:opacity-100 [@media(hover:none)]:visible [@media(hover:none)]:opacity-100";

/** A subject's syllabus: every chapter, and the lessons inside it. */
export function CourseView({ subject, levels }: { subject: Subject; levels: Level[] }) {
  const t = useT();
  const { lang } = useLanguage();
  const [levelId, setLevelId] = useState(levels[0]?.id ?? "");

  const level = levels.find((l) => l.id === levelId) ?? levels[0];
  if (!level) return null;

  const group = subject.group === "science" ? "sciences" : "languages";
  const lessonCount = level.chapters.reduce((n, c) => n + c.lessons.length, 0);

  return (
    <div>
      <header className="flex flex-wrap items-center gap-x-4 gap-y-3 border-b border-border pb-6">
        <span aria-hidden="true" className="text-3xl">
          {subject.emoji}
        </span>
        <h1 className="text-2xl font-semibold text-foreground font-display">{subject.name[lang]}</h1>

        <LevelMenu
          id="course-level"
          levels={levels}
          levelId={level.id}
          onChange={setLevelId}
          className="w-full sm:w-64"
        />

        <p className="ml-auto text-sm text-muted">
          {t("course.counts", { c: level.chapters.length, l: lessonCount })}
        </p>
      </header>

      {/* A freestyle chat sits beside the syllabus rather than inside it: it
          belongs to the level, not to any one chapter — and on the levels whose
          syllabus is still empty it is the only thing on offer. */}
      <div className="mt-8 grid gap-6 lg:grid-cols-[1fr_20rem] lg:items-start">
        <div className="flex flex-col gap-6">
          {level.chapters.length === 0 && (
            <p className="rounded-xl border border-dashed border-border bg-surface p-10 text-center text-sm text-muted">
              {t("course.soon")}
            </p>
          )}

          {level.chapters.map((chapter, index) => (
            <section key={chapter.id} className="overflow-hidden rounded-xl border border-border bg-surface">
              <div className="flex items-center gap-4 border-b border-border bg-primary-tint px-6 py-5">
                <span
                  aria-hidden="true"
                  className="flex h-11 w-11 shrink-0 items-center justify-center rounded-full bg-surface text-xl shadow-sm"
                >
                  {chapter.emoji ?? "📘"}
                </span>
                <div className="min-w-0">
                  <p className="text-xs font-semibold uppercase tracking-wider text-primary font-mono">
                    {t("book.chapterN", { n: index + 1 })}
                  </p>
                  <h2 className="mt-1 text-lg font-semibold text-foreground font-display">{chapter.title}</h2>
                </div>
              </div>

              <p className="px-6 pt-5 text-xs font-semibold uppercase tracking-wider text-muted font-mono">
                {t("course.lessons")}
              </p>

              <ul className="divide-y divide-border px-6 pb-2">
                {chapter.lessons.map((lesson) => (
                  <li key={lesson.id} className="group flex items-center gap-4 py-4">
                    <LiveLessonIcon className="h-10 w-10 shrink-0" />
                    <Link
                      href={`/course/${subject.id}/${level.id}/${chapter.id}/${lesson.id}`}
                      className="min-w-0 flex-1"
                    >
                      <span className="block truncate text-sm font-semibold text-foreground hover:text-primary">
                        {lesson.title}
                      </span>
                      {lesson.category && (
                        <span className="mt-0.5 block text-xs text-muted">{lesson.category}</span>
                      )}
                    </Link>
                    {/* Both kept out of the way until this lesson is hovered —
                        and always there for keyboard and touch, which have no
                        hover. */}
                    <StartNowButton
                      // This lesson, not the chapter: its paper and its
                      // prepared material are its own.
                      context={{ subject: subject.id, level: level.id,
                                 chapter: chapter.id, lesson: lesson.id }}
                      className={`${REVEAL} rounded-full bg-primary px-4 py-1.5 text-xs font-semibold text-white transition-[opacity,background-color] hover:bg-primary-hover disabled:opacity-60`}
                    />
                    <Link
                      href={`/book/${group}/${subject.id}`}
                      className={`${REVEAL} shrink-0 rounded-full border border-primary px-4 py-1.5 text-xs font-semibold text-primary transition-[opacity,background-color] hover:bg-primary-tint`}
                    >
                      {t("course.book")}
                    </Link>
                  </li>
                ))}
              </ul>
            </section>
          ))}
        </div>

        {subject.group === "language" && (
          <aside className="lg:sticky lg:top-6">
            <FreestyleCard subject={subject.id} levelId={level.id} />
          </aside>
        )}
      </div>
    </div>
  );
}
