"use client";

import Link from "next/link";
import { useRef, useState } from "react";
import { RoadToSun } from "@/components/RoadToSun";
import { useLanguage, type Lang } from "@/lib/i18n";
import { landingCopy } from "@/lib/landingCopy";
import {
  LANGUAGE_SUBJECTS,
  SCIENCE_SUBJECTS,
  SUBJECTS,
  type Subject,
  type SubjectGroup,
} from "@/lib/subjects";

/**
 * The full subject catalogue as a picker: two groups behind tabs, and a board
 * that rewrites itself in the chosen subject's own notation.
 */
export function SubjectPicker() {
  const { lang } = useLanguage();
  const copy = landingCopy(lang).hero;
  const [group, setGroup] = useState<SubjectGroup>("language");
  const [subjectId, setSubjectId] = useState("english");
  const subject = SUBJECTS.find((s) => s.id === subjectId) ?? SUBJECTS[0];

  const groups = [
    { id: "language" as const, label: copy.languages, subjects: LANGUAGE_SUBJECTS },
    { id: "science" as const, label: copy.sciences, subjects: SCIENCE_SUBJECTS },
  ];
  const openGroup = groups.find((g) => g.id === group) ?? groups[0];

  return (
    <section
      id="subjects"
      className="mx-auto grid w-full max-w-6xl scroll-mt-20 gap-12 px-5 py-20 sm:px-8 lg:grid-cols-[minmax(0,1fr)_minmax(0,480px)] lg:items-start lg:gap-16"
    >
      <div>
        <h2 className="text-3xl font-semibold tracking-tight text-foreground font-display sm:text-4xl">
          {copy.pickLabel}
        </h2>

        <GroupTabs groups={groups} open={group} onOpen={setGroup} />

        <div
          id={`subject-panel-${openGroup.id}`}
          role="tabpanel"
          aria-labelledby={`subject-tab-${openGroup.id}`}
          className="mt-5 grid gap-2.5 sm:grid-cols-2"
        >
          {openGroup.subjects.map((item) => (
            <SubjectCard
              key={item.id}
              subject={item}
              lang={lang}
              selected={item.id === subjectId}
              onSelect={() => setSubjectId(item.id)}
            />
          ))}
        </div>

        {group === "language" && <PlacementTest copy={copy} />}

        <div className="mt-8 flex flex-wrap items-center gap-x-5 gap-y-3">
          <Link
            href="/signup"
            className="rounded-xl bg-primary px-6 py-3.5 text-sm font-semibold text-white transition-colors hover:bg-primary-hover"
          >
            {copy.cta} — {subject.name[lang]}
          </Link>
          <p className="text-sm text-muted">{copy.ctaNote}</p>
        </div>
      </div>

      <Board subject={subject} lang={lang} copy={copy} />
    </section>
  );
}

function GroupTabs({
  groups,
  open,
  onOpen,
}: {
  groups: { id: SubjectGroup; label: string }[];
  open: SubjectGroup;
  onOpen: (group: SubjectGroup) => void;
}) {
  const tabsRef = useRef<HTMLDivElement>(null);

  // Left/right arrows move between tabs, as the tab pattern expects.
  const onKeyDown = (event: React.KeyboardEvent) => {
    if (event.key !== "ArrowRight" && event.key !== "ArrowLeft") return;
    event.preventDefault();
    const step = event.key === "ArrowRight" ? 1 : -1;
    const index = groups.findIndex((g) => g.id === open);
    const next = groups[(index + step + groups.length) % groups.length];
    onOpen(next.id);
    tabsRef.current?.querySelectorAll("button")[groups.indexOf(next)]?.focus();
  };

  return (
    <div
      ref={tabsRef}
      role="tablist"
      onKeyDown={onKeyDown}
      className="mt-6 inline-flex rounded-xl border border-border bg-surface p-1"
    >
      {groups.map((group) => {
        const active = group.id === open;
        return (
          <button
            key={group.id}
            type="button"
            role="tab"
            id={`subject-tab-${group.id}`}
            aria-selected={active}
            aria-controls={`subject-panel-${group.id}`}
            tabIndex={active ? 0 : -1}
            onClick={() => onOpen(group.id)}
            className={`rounded-lg px-4 py-2 text-sm font-semibold transition-colors ${
              active ? "bg-primary text-white" : "text-muted hover:text-foreground"
            }`}
          >
            {group.label}
          </button>
        );
      })}
    </div>
  );
}

/**
 * The levels note that sits with the language list, so a learner who doesn't
 * know their CEFR level has somewhere to go before booking.
 */
function PlacementTest({ copy }: { copy: ReturnType<typeof landingCopy>["hero"] }) {
  return (
    <div className="mt-4 flex flex-col gap-3 rounded-xl border border-dashed border-border bg-surface px-4 py-4 sm:flex-row sm:items-center sm:justify-between">
      <div>
        <p className="text-sm font-semibold text-foreground">{copy.levelsHeading}</p>
        <p className="mt-1 max-w-md text-xs leading-relaxed text-muted">{copy.levelsBody}</p>
      </div>
      <Link
        href="/placement-test"
        className="shrink-0 rounded-full border border-primary px-4 py-2 text-center text-xs font-semibold text-primary transition-colors hover:bg-primary-tint"
      >
        {copy.levelsCta}
      </Link>
    </div>
  );
}

/**
 * One subject, shown the way a prospectus lists them: a flag for a language,
 * an instrument for a science, and the level or unit the tutor would open on.
 */
function SubjectCard({
  subject,
  lang,
  selected,
  onSelect,
}: {
  subject: Subject;
  lang: Lang;
  selected: boolean;
  onSelect: () => void;
}) {
  return (
    <button
      type="button"
      onClick={onSelect}
      aria-pressed={selected}
      className={`flex items-center gap-3 rounded-xl border px-3.5 py-3 text-left transition-colors ${
        selected ? "border-primary bg-primary-tint" : "border-border bg-surface hover:border-primary"
      }`}
    >
      <span
        aria-hidden="true"
        className="flex h-10 w-10 shrink-0 items-center justify-center rounded-lg bg-background text-xl"
      >
        {subject.emoji}
      </span>
      <span className="min-w-0">
        <span className="block truncate text-sm font-semibold text-foreground">{subject.name[lang]}</span>
        <span className="block truncate text-xs text-muted">
          {(subject.level ?? subject.note)[lang]}
        </span>
      </span>
    </button>
  );
}

/** Choosing a subject rewrites the chalk in that subject's own notation. */
function Board({
  subject,
  lang,
  copy,
}: {
  subject: Subject;
  lang: Lang;
  copy: ReturnType<typeof landingCopy>["hero"];
}) {
  return (
    <div className="relative overflow-hidden rounded-3xl border border-border bg-chalk text-chalk-ink shadow-xl lg:sticky lg:top-24">
      <div className="bg-grid-chalk pointer-events-none absolute inset-0" />

      <div className="relative flex items-center justify-between px-6 pt-5">
        <span className="text-xs uppercase tracking-[0.14em] text-chalk-ink/50 font-mono">
          {copy.boardLabel}
        </span>
        <span className="flex items-center gap-1.5 rounded-full bg-chalk-ink/10 px-2.5 py-1 text-[0.7rem] font-semibold uppercase tracking-wider text-chalk-ink/80">
          <span className="h-1.5 w-1.5 rounded-full bg-success" />
          {copy.live}
        </span>
      </div>

      <div className="relative flex min-h-[15rem] flex-col justify-center px-6 py-10 sm:px-8">
        <div key={subject.id} className="animate-chalk-in">
          <p
            dir={subject.rtl ? "rtl" : "ltr"}
            className={`text-2xl leading-snug text-chalk-ink sm:text-[1.75rem] ${
              subject.rtl ? "font-sans" : "font-mono"
            }`}
          >
            {subject.chalk}
          </p>
          <p className="mt-3 text-sm text-accent-ink">{subject.note[lang]}</p>
        </div>
        {/* keyed on the subject so picking a new one redraws the road, the
            way the chalk above it gets rewritten */}
        <RoadToSun key={`road-${subject.id}`} animate className="mt-6 h-28 w-full max-w-[17rem] text-accent-ink" />
      </div>

      <div className="relative flex items-center gap-3 border-t border-chalk-ink/10 px-6 py-4">
        <span className="flex h-8 w-8 items-center justify-center rounded-full bg-accent-ink/15 text-xs text-accent-ink font-mono">
          {subject.tag}
        </span>
        <p className="text-sm text-chalk-ink/70">
          {copy.tutorLine} · {subject.name[lang]}
        </p>
      </div>
    </div>
  );
}
