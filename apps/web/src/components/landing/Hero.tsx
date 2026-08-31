"use client";

import Image from "next/image";
import Link from "next/link";
import { useState } from "react";
import { useLanguage } from "@/lib/i18n";
import { landingCopy } from "@/lib/landingCopy";
import { LANGUAGE_SUBJECTS } from "@/lib/subjects";

export function Hero() {
  const { lang } = useLanguage();
  const copy = landingCopy(lang).heroMock;
  const [lessonLang, setLessonLang] = useState("english");
  const chosen = LANGUAGE_SUBJECTS.find((s) => s.id === lessonLang) ?? LANGUAGE_SUBJECTS[0];

  return (
    <section className="hero-mock relative isolate overflow-hidden bg-[var(--mock-bg)] text-[var(--mock-text)]">
      <div className="bg-dot-grid pointer-events-none absolute left-0 top-0 h-64 w-64 opacity-40" />

      <div className="relative grid lg:grid-cols-[minmax(0,1fr)_minmax(0,44%)]">
        <div className="px-5 py-14 sm:px-8 lg:py-20 lg:pl-[max(2rem,calc((100vw-76rem)/2))] lg:pr-10">
          <div className="grid gap-10 lg:grid-cols-[minmax(0,1fr)_14.5rem] lg:items-start lg:gap-8">
            <div>
              <p className="flex items-center gap-3">
                <span className="rounded-full bg-[var(--mock-lime)] px-3 py-1 text-xs font-bold uppercase tracking-wider text-[var(--mock-bg)]">
                  {copy.badge}
                </span>
                <span className="text-sm font-medium text-[var(--mock-muted)]">{copy.badgeLabel}</span>
              </p>

              <h1 className="mt-6 text-4xl font-bold leading-[1.06] tracking-tight font-display sm:text-5xl lg:text-[2.9rem] xl:text-[3.4rem]">
                <span className="block">{copy.headline1}</span>
                <span className="block text-[var(--mock-lime)]">{copy.headline2}</span>
              </h1>

              <p className="mt-6 max-w-lg text-base leading-relaxed text-[var(--mock-muted)]">
                {copy.body}
              </p>

              <ul className="mt-8 flex flex-wrap gap-2.5">
                {copy.pills.map((label, i) => (
                  <li
                    key={label}
                    className="flex items-center gap-2 rounded-xl border border-[var(--mock-border)] px-3.5 py-2.5 text-sm text-[var(--mock-text)]"
                  >
                    <PillIcon index={i} />
                    {label}
                  </li>
                ))}
              </ul>

              <div className="mt-8 flex flex-col gap-3 sm:flex-row sm:items-center">
                <div className="relative flex items-center gap-2 rounded-xl border border-[var(--mock-border)] bg-[var(--mock-surface)] pl-4 pr-3">
                  <span aria-hidden="true" className="text-lg">
                    {chosen.emoji}
                  </span>
                  <label htmlFor="lesson-language" className="sr-only">
                    {copy.selectLabel}
                  </label>
                  <select
                    id="lesson-language"
                    value={lessonLang}
                    onChange={(e) => setLessonLang(e.target.value)}
                    className="appearance-none bg-transparent py-3.5 pr-7 text-base font-medium text-[var(--mock-text)] outline-none"
                  >
                    {LANGUAGE_SUBJECTS.map((s) => (
                      <option key={s.id} value={s.id} className="text-black">
                        {s.name[lang]}
                      </option>
                    ))}
                  </select>
                  <ChevronDown className="pointer-events-none absolute right-3.5 h-4 w-4 text-[var(--mock-muted)]" />
                </div>

                <Link
                  href="/signup"
                  className="rounded-xl bg-[var(--mock-violet)] px-7 py-4 text-center text-base font-semibold text-white transition-colors hover:bg-[var(--mock-violet-hover)]"
                >
                  {copy.cta}
                </Link>
              </div>

              <p className="mt-5 flex items-center gap-2 text-sm text-[var(--mock-muted)]">
                <CheckCircle className="h-5 w-5 text-[var(--mock-muted)]" />
                {copy.trial}
                <span aria-hidden="true">·</span>
                {copy.cancel}
              </p>
            </div>

            <TutorCard copy={copy} />
          </div>

          <ul className="mt-14 grid gap-8 sm:grid-cols-2 lg:grid-cols-4 lg:gap-6">
            {copy.features.map((feature, i) => (
              <li key={feature.title}>
                <FeatureIcon index={i} />
                <p className="mt-4 text-base font-semibold">{feature.title}</p>
                <p className="mt-1.5 text-sm leading-relaxed text-[var(--mock-muted)]">{feature.body}</p>
              </li>
            ))}
          </ul>
        </div>

        <div className="relative min-h-[24rem] lg:min-h-full">
          <Image
            src="/marketing/hero-class.png"
            alt="A Zanoba tutor working through a linear equation on the whiteboard during a live class"
            fill
            priority
            quality={95}
            sizes="(min-width: 1024px) 44vw, 100vw"
            className="object-contain object-center"
          />
          {/* Blends the panel's edges into the background, as in the mockup. */}
          <div className="pointer-events-none absolute inset-y-0 left-0 w-16 bg-gradient-to-r from-[var(--mock-bg)] via-[var(--mock-bg)]/60 to-transparent" />
          <div className="pointer-events-none absolute inset-x-0 top-0 h-20 bg-gradient-to-b from-[var(--mock-bg)] to-transparent" />
          <div className="pointer-events-none absolute inset-x-0 bottom-0 h-20 bg-gradient-to-t from-[var(--mock-bg)] to-transparent" />
        </div>
      </div>
    </section>
  );
}

function TutorCard({ copy }: { copy: ReturnType<typeof landingCopy>["heroMock"] }) {
  return (
    <div className="rounded-2xl border border-[var(--mock-border)] bg-[var(--mock-surface)] p-5 lg:max-w-[14.5rem]">
      <p className="flex items-center gap-2 text-sm font-semibold">
        <Sparkle className="h-4 w-4 text-[var(--mock-lime)]" />
        {copy.tutorCardTitle}
      </p>

      <Image
        src="/marketing/tutor-luna.png"
        alt=""
        width={256}
        height={256}
        className="mx-auto mt-4 h-32 w-32 rounded-full object-cover"
      />

      <p className="mt-4 flex items-center gap-2">
        <span className="text-xl font-semibold font-display">{copy.tutorName}</span>
        <span className="rounded-full bg-[var(--mock-violet)] px-2 py-0.5 text-[0.65rem] font-bold uppercase tracking-wider text-white">
          AI
        </span>
      </p>

      <ul className="mt-3 flex flex-col gap-2">
        {copy.tutorTraits.map((trait) => (
          <li key={trait} className="flex gap-2 text-xs leading-snug text-[var(--mock-muted)]">
            <span aria-hidden="true" className="text-[var(--mock-lime)]">
              ✓
            </span>
            {trait}
          </li>
        ))}
      </ul>

      <p className="mt-4 flex items-center gap-1.5 rounded-full bg-[var(--mock-lime)]/10 px-3 py-1.5 text-[0.7rem] font-medium text-[var(--mock-lime)]">
        <span className="h-1.5 w-1.5 rounded-full bg-[var(--mock-lime)]" />
        {copy.tutorStatus}
      </p>
    </div>
  );
}

const ICON = {
  className: "h-4 w-4",
  fill: "none",
  stroke: "currentColor",
  strokeWidth: 1.7,
  strokeLinecap: "round" as const,
  strokeLinejoin: "round" as const,
  "aria-hidden": true,
};

function PillIcon({ index }: { index: number }) {
  const tone = index % 2 === 0 ? "text-[var(--mock-lime)]" : "text-[var(--mock-violet)]";
  const paths = [
    // microphone
    "M12 3a2.5 2.5 0 0 1 2.5 2.5v5a2.5 2.5 0 0 1-5 0v-5A2.5 2.5 0 0 1 12 3ZM6 11a6 6 0 0 0 12 0M12 17v4",
    // pen
    "M4 20l4-1 10-10a2.1 2.1 0 0 0-3-3L5 16l-1 4Z",
    // book
    "M4 5.5A2.5 2.5 0 0 1 6.5 3H19v15H6.5A2.5 2.5 0 0 0 4 20.5V5.5ZM19 18v3H6.5",
    // smile
    "M12 21a9 9 0 1 0 0-18 9 9 0 0 0 0 18ZM9 10h.01M15 10h.01M8.5 14.5a4.5 4.5 0 0 0 7 0",
  ];
  return (
    <svg viewBox="0 0 24 24" {...ICON} className={`${ICON.className} ${tone}`}>
      <path d={paths[index]} />
    </svg>
  );
}

function FeatureIcon({ index }: { index: number }) {
  const tone = index % 2 === 0 ? "text-[var(--mock-violet)]" : "text-[var(--mock-lime)]";
  const paths = [
    // graduation cap
    "M12 4 2.5 8.5 12 13l9.5-4.5L12 4ZM6.5 10.8V16c0 1.7 2.5 3 5.5 3s5.5-1.3 5.5-3v-5.2",
    // speech bubble
    "M4 5.5A1.5 1.5 0 0 1 5.5 4h13A1.5 1.5 0 0 1 20 5.5v9a1.5 1.5 0 0 1-1.5 1.5H9l-5 4V5.5Z",
    // rising chart
    "M4 20V6M4 20h16M7.5 16.5v-4M12 16.5v-7M16.5 16.5v-3M20 7l-4.5 4-3-2.5L8 13",
    // shield
    "M12 3.5 5 6v6c0 4 3 7.2 7 8.5 4-1.3 7-4.5 7-8.5V6l-7-2.5ZM9.5 12l1.8 1.8L15 10",
  ];
  return (
    <svg viewBox="0 0 24 24" {...ICON} className={`h-7 w-7 ${tone}`}>
      <path d={paths[index]} />
    </svg>
  );
}

function ChevronDown({ className }: { className?: string }) {
  return (
    <svg viewBox="0 0 24 24" {...ICON} className={className}>
      <path d="m6 9 6 6 6-6" />
    </svg>
  );
}

function CheckCircle({ className }: { className?: string }) {
  return (
    <svg viewBox="0 0 24 24" {...ICON} className={className}>
      <circle cx="12" cy="12" r="9" />
      <path d="m8.5 12 2.5 2.5 4.5-5" />
    </svg>
  );
}

function Sparkle({ className }: { className?: string }) {
  return (
    <svg viewBox="0 0 24 24" {...ICON} className={className}>
      <path d="M12 3.5 13.8 9l5.7 1.8-5.7 1.8L12 18.5 10.2 12.6 4.5 10.8 10.2 9 12 3.5Z" />
    </svg>
  );
}
