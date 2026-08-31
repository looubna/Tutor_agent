"use client";

import Link from "next/link";
import { useState } from "react";
import { CalendarSlotPicker } from "@/components/CalendarSlotPicker";
import { useLanguage, useT } from "@/lib/i18n";
import { LevelMenu } from "@/components/LevelMenu";
import type { Level } from "@/lib/curriculum";
import type { Subject } from "@/lib/subjects";

type IsoSlot = { startTime: string; endTime: string };

/**
 * The syllabus on the left, the calendar beside it. The chapter rail scrolls on
 * its own so a long curriculum — chapters and their lessons — never pushes the
 * booking calendar off the screen.
 */
export function ChapterPicker({
  subject,
  levels,
  availableSlots,
  existingBookings,
}: {
  subject: Subject;
  levels: Level[];
  availableSlots: IsoSlot[];
  existingBookings: IsoSlot[];
}) {
  const t = useT();
  const { lang } = useLanguage();
  const [levelId, setLevelId] = useState(levels[0]?.id ?? "");
  const [openChapter, setOpenChapter] = useState<string | null>(levels[0]?.chapters[0]?.id ?? null);
  const [chosen, setChosen] = useState<string | null>(null);

  const level = levels.find((l) => l.id === levelId) ?? levels[0];
  const chosenChapter = level?.chapters.find((c) => c.id === chosen) ?? null;
  if (!level) return null;

  const group = subject.group === "science" ? "sciences" : "languages";

  return (
    <div className="flex flex-col gap-8 lg:flex-row lg:items-start">
      <aside className="w-full shrink-0 lg:sticky lg:top-24 lg:w-72">
        <div className="flex flex-wrap items-center gap-2.5">
          <span aria-hidden="true" className="text-2xl">
            {subject.emoji}
          </span>
          <h1 className="text-xl font-semibold text-foreground font-display">{subject.name[lang]}</h1>
        </div>

        <LevelMenu
          id="level"
          levels={levels}
          levelId={level.id}
          onChange={(next) => {
            setLevelId(next);
            setChosen(null);
            setOpenChapter(levels.find((l) => l.id === next)?.chapters[0]?.id ?? null);
          }}
          className="mt-3"
        />

        <p className="mt-3 text-xs text-muted">{t("book.chapterCount", { n: level.chapters.length })}</p>

        {level.chapters.length === 0 && (
          <p className="mt-3 rounded-xl border border-dashed border-border bg-surface p-5 text-xs leading-relaxed text-muted">
            {t("course.soon")}
          </p>
        )}

        {/* Its own scroll area, so the syllabus can grow without moving the calendar. */}
        <ul className="mt-3 max-h-[26rem] divide-y divide-border overflow-y-auto overscroll-contain rounded-xl border border-border bg-surface lg:max-h-[30rem]">
          {level.chapters.map((chapter, index) => {
            const open = openChapter === chapter.id;
            const picked = chosen === chapter.id;
            return (
              <li key={chapter.id} className={picked ? "bg-primary-tint" : ""}>
                <div className="flex items-start gap-2.5 p-3.5">
                  <input
                    type="radio"
                    name="chapter"
                    id={`chapter-${chapter.id}`}
                    checked={picked}
                    onChange={() => setChosen(chapter.id)}
                    className="mt-1 h-4 w-4 shrink-0 accent-[var(--primary)]"
                  />
                  <span
                    aria-hidden="true"
                    className="mt-0.5 flex h-8 w-8 shrink-0 items-center justify-center rounded-full bg-background text-base"
                  >
                    {chapter.emoji ?? "📘"}
                  </span>

                  <div className="min-w-0 flex-1">
                    <label htmlFor={`chapter-${chapter.id}`} className="block cursor-pointer">
                      <span className="block text-[0.65rem] font-medium uppercase tracking-wider text-muted font-mono">
                        {t("book.chapterN", { n: index + 1 })}
                      </span>
                      <span className="mt-0.5 block text-sm font-semibold leading-snug text-foreground">
                        {chapter.title}
                      </span>
                    </label>

                    {open && (
                      <ul className="mt-2.5 flex flex-col gap-1.5 border-l border-border pl-3">
                        {chapter.lessons.map((lesson) => (
                          <li key={lesson.id} className="text-xs leading-snug text-muted">
                            {lesson.title}
                          </li>
                        ))}
                      </ul>
                    )}
                  </div>

                  <button
                    type="button"
                    onClick={() => setOpenChapter(open ? null : chapter.id)}
                    aria-expanded={open}
                    className="shrink-0 rounded-full p-1 text-muted transition-colors hover:bg-background hover:text-foreground"
                  >
                    <span className="sr-only">{chapter.title}</span>
                    <svg viewBox="0 0 24 24" fill="none" className="h-4 w-4" aria-hidden="true">
                      <path
                        d={open ? "m6 15 6-6 6 6" : "m6 9 6 6 6-6"}
                        stroke="currentColor"
                        strokeWidth="1.8"
                        strokeLinecap="round"
                        strokeLinejoin="round"
                      />
                    </svg>
                  </button>
                </div>
              </li>
            );
          })}
        </ul>

        <Link
          href={`/book/${group}`}
          className="mt-4 inline-block text-sm font-medium text-muted transition-colors hover:text-foreground"
        >
          {t("book.backToSubjects")}
        </Link>
      </aside>

      <section className="min-w-0 flex-1">
        <h2 className="text-lg font-semibold text-foreground font-display">{t("book.chooseTime")}</h2>

        {chosenChapter ? (
          <>
            <p className="mt-1 text-sm text-primary">{chosenChapter.title}</p>
            <div className="mt-5">
              <CalendarSlotPicker
                availableSlots={availableSlots}
                existingBookings={existingBookings}
                context={{ subject: subject.id, level: level.id, chapter: chosenChapter.id }}
                stackSummary
              />
            </div>
          </>
        ) : (
          <p className="mt-2 text-sm text-muted">{t("book.pickChapterFirst")}</p>
        )}
      </section>
    </div>
  );
}
