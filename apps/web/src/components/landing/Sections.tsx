"use client";

import Link from "next/link";
import { Logo } from "@/components/Logo";
import { useLanguage, type Lang } from "@/lib/i18n";
import { landingCopy } from "@/lib/landingCopy";
import { LANGUAGE_SUBJECTS, SCIENCE_SUBJECTS, type Subject } from "@/lib/subjects";

const SECTION = "mx-auto w-full max-w-6xl px-5 sm:px-8";

export function Facts() {
  const { lang } = useLanguage();
  const facts = landingCopy(lang).facts;

  return (
    <section className="border-y border-border bg-surface">
      <div className={`${SECTION} grid gap-8 py-10 sm:grid-cols-3`}>
        {facts.map((fact) => (
          <div key={fact.label} className="flex items-baseline gap-4">
            <span className="text-3xl font-semibold text-primary font-display">{fact.value}</span>
            <span className="text-sm leading-snug text-muted">{fact.label}</span>
          </div>
        ))}
      </div>
    </section>
  );
}

export function Benefits() {
  const { lang } = useLanguage();
  const copy = landingCopy(lang).benefits;

  return (
    <section className={`${SECTION} py-20`}>
      <h2 className="max-w-2xl text-3xl font-semibold tracking-tight text-foreground font-display sm:text-4xl">
        {copy.heading}
      </h2>
      <div className="mt-10 grid gap-5 md:grid-cols-3">
        {copy.items.map((item) => (
          <article key={item.title} className="rounded-2xl border border-border bg-surface p-6">
            <PlottedTick />
            <h3 className="mt-5 text-lg font-semibold text-foreground font-display">{item.title}</h3>
            <p className="mt-2.5 text-sm leading-relaxed text-muted">{item.body}</p>
          </article>
        ))}
      </div>
    </section>
  );
}

function PlottedTick() {
  return (
    <span className="flex h-10 w-10 items-center justify-center rounded-xl bg-accent-tint">
      <svg viewBox="0 0 24 24" fill="none" className="h-5 w-5" aria-hidden="true">
        <path
          d="M3 19C6 19 7 13 10 10s5-4 9-4"
          stroke="var(--accent-ink)"
          strokeWidth="2.2"
          strokeLinecap="round"
        />
        <circle cx="19" cy="6" r="2.4" fill="var(--accent-ink)" />
      </svg>
    </span>
  );
}

export function Subjects() {
  const { lang } = useLanguage();
  const copy = landingCopy(lang).subjects;

  return (
    <section className="border-y border-border bg-surface">
      <div className={`${SECTION} py-20`}>
        <h2 className="text-3xl font-semibold tracking-tight text-foreground font-display sm:text-4xl">
          {copy.heading}
        </h2>
        <p className="mt-3 max-w-xl text-base leading-relaxed text-muted">{copy.body}</p>

        <div className="mt-10 grid gap-10 lg:grid-cols-2">
          <SubjectColumn label={copy.languages} subjects={LANGUAGE_SUBJECTS} lang={lang} />
          <SubjectColumn label={copy.sciences} subjects={SCIENCE_SUBJECTS} lang={lang} />
        </div>

        <Link
          href="/signup"
          className="mt-10 inline-block rounded-xl border border-primary px-5 py-3 text-sm font-semibold text-primary transition-colors hover:bg-primary-tint"
        >
          {copy.cta}
        </Link>
      </div>
    </section>
  );
}

function SubjectColumn({ label, subjects, lang }: { label: string; subjects: Subject[]; lang: Lang }) {
  return (
    <div>
      <h3 className="mb-4 text-[0.7rem] font-semibold uppercase tracking-[0.14em] text-muted font-mono">{label}</h3>
      <ul className="grid gap-2.5 sm:grid-cols-2">
        {subjects.map((subject) => (
          <li
            key={subject.id}
            className="flex items-center gap-3 rounded-xl border border-border bg-background px-4 py-3"
          >
            <span
              aria-hidden="true"
              className="flex h-9 w-9 shrink-0 items-center justify-center rounded-lg bg-surface text-lg"
            >
              {subject.emoji}
            </span>
            <span className="min-w-0">
              <span className="block truncate text-sm font-medium text-foreground">{subject.name[lang]}</span>
              <span className="block truncate text-xs text-muted">{subject.note[lang]}</span>
            </span>
          </li>
        ))}
      </ul>
    </div>
  );
}

export function HowItWorks() {
  const { lang } = useLanguage();
  const copy = landingCopy(lang).how;

  return (
    <section id="how" className={`${SECTION} scroll-mt-20 py-20`}>
      <h2 className="text-3xl font-semibold tracking-tight text-foreground font-display sm:text-4xl">
        {copy.heading}
      </h2>
      <ol className="mt-10 grid gap-5 md:grid-cols-3">
        {copy.steps.map((step, index) => (
          <li key={step.title} className="rounded-2xl border border-border bg-surface p-6">
            <span className="text-sm font-semibold text-accent-ink font-mono">
              {String(index + 1).padStart(2, "0")}
            </span>
            <h3 className="mt-3 text-lg font-semibold text-foreground font-display">{step.title}</h3>
            <p className="mt-2.5 text-sm leading-relaxed text-muted">{step.body}</p>
          </li>
        ))}
      </ol>
    </section>
  );
}

export function Pricing() {
  const { lang } = useLanguage();
  const copy = landingCopy(lang).pricing;

  return (
    <section id="pricing" className="scroll-mt-20 border-y border-border bg-surface">
      <div className={`${SECTION} py-20`}>
        <h2 className="text-3xl font-semibold tracking-tight text-foreground font-display sm:text-4xl">
          {copy.heading}
        </h2>
        <p className="mt-3 max-w-xl text-base leading-relaxed text-muted">{copy.body}</p>

        <div className="mt-10 grid gap-5 md:grid-cols-2 lg:max-w-3xl">
          {copy.plans.map((plan, index) => {
            const featured = index === 1;
            return (
              <article
                key={plan.name}
                className={`relative flex flex-col rounded-2xl border bg-background p-7 ${
                  featured ? "border-primary" : "border-border"
                }`}
              >
                {featured && (
                  <span className="absolute -top-2.5 left-7 rounded-full bg-primary px-2.5 py-0.5 text-[0.7rem] font-semibold uppercase tracking-wider text-white">
                    {copy.badge}
                  </span>
                )}
                <h3 className="text-sm font-semibold uppercase tracking-[0.12em] text-muted font-mono">
                  {plan.name}
                </h3>
                <p className="mt-4 flex items-baseline gap-2">
                  <span className="text-4xl font-semibold text-foreground font-display">{plan.price}</span>
                  <span className="text-sm text-muted">{plan.cadence}</span>
                </p>
                <p className="mt-3 text-sm text-muted">{plan.body}</p>
                <ul className="mt-6 flex flex-1 flex-col gap-2.5">
                  {plan.features.map((feature) => (
                    <li key={feature} className="flex gap-2.5 text-sm text-foreground">
                      <span aria-hidden="true" className="text-success">
                        ✓
                      </span>
                      {feature}
                    </li>
                  ))}
                </ul>
                <Link
                  href="/signup"
                  className={`mt-7 rounded-xl px-5 py-3 text-center text-sm font-semibold transition-colors ${
                    featured
                      ? "bg-primary text-white hover:bg-primary-hover"
                      : "border border-border text-foreground hover:border-primary hover:text-primary"
                  }`}
                >
                  {plan.cta}
                </Link>
              </article>
            );
          })}
        </div>

        <p className="mt-6 text-sm text-muted">{copy.note}</p>
      </div>
    </section>
  );
}

export function Testimonials() {
  const { lang } = useLanguage();
  const copy = landingCopy(lang).testimonials;

  return (
    <section className={`${SECTION} py-20`}>
      <h2 className="text-3xl font-semibold tracking-tight text-foreground font-display sm:text-4xl">
        {copy.heading}
      </h2>
      <div className="mt-10 grid gap-5 md:grid-cols-3">
        {copy.items.map((item) => (
          <figure key={item.name} className="flex flex-col rounded-2xl border border-border bg-surface p-6">
            <blockquote className="flex-1 text-sm leading-relaxed text-foreground">“{item.quote}”</blockquote>
            <figcaption className="mt-5 border-t border-border pt-4">
              <span className="block text-sm font-semibold text-foreground">{item.name}</span>
              <span className="block text-xs text-muted font-mono">{item.detail}</span>
            </figcaption>
          </figure>
        ))}
      </div>
    </section>
  );
}

export function Faq() {
  const { lang } = useLanguage();
  const copy = landingCopy(lang).faq;

  return (
    <section className="border-t border-border bg-surface">
      <div className={`${SECTION} py-20`}>
        <h2 className="text-3xl font-semibold tracking-tight text-foreground font-display sm:text-4xl">
          {copy.heading}
        </h2>
        <div className="mt-10 max-w-3xl divide-y divide-border border-y border-border">
          {copy.items.map((item) => (
            <details key={item.q} className="group py-4">
              <summary className="flex cursor-pointer list-none items-center justify-between gap-4 text-base font-medium text-foreground">
                {item.q}
                <span
                  aria-hidden="true"
                  className="shrink-0 text-muted transition-transform group-open:rotate-45"
                >
                  +
                </span>
              </summary>
              <p className="mt-3 max-w-2xl text-sm leading-relaxed text-muted">{item.a}</p>
            </details>
          ))}
        </div>
      </div>
    </section>
  );
}

export function LandingFooter() {
  const { lang } = useLanguage();
  const copy = landingCopy(lang).footer;

  return (
    <footer className="relative overflow-hidden bg-board text-board-foreground">
      <div className="bg-grid-paper pointer-events-none absolute inset-0" />
      <div className={`${SECTION} relative grid gap-10 py-14 lg:grid-cols-[minmax(0,1.4fr)_repeat(3,minmax(0,1fr))]`}>
        <div>
          <div className="flex items-center">
            <Logo size={38} />
          </div>
          <p className="mt-4 max-w-xs text-sm leading-relaxed text-board-foreground/70">{copy.tagline}</p>
        </div>

        {copy.columns.map((column) => (
          <div key={column.heading}>
            <h3 className="text-[0.7rem] font-semibold uppercase tracking-[0.14em] text-board-foreground/50 font-mono">
              {column.heading}
            </h3>
            <ul className="mt-4 flex flex-col gap-2.5">
              {column.links.map((link) => (
                <li key={link.label}>
                  {link.href ? (
                    <Link
                      href={link.href}
                      className="text-sm text-board-foreground/75 transition-colors hover:text-board-foreground"
                    >
                      {link.label}
                    </Link>
                  ) : (
                    <span className="text-sm text-board-foreground/75">{link.label}</span>
                  )}
                </li>
              ))}
            </ul>
          </div>
        ))}
      </div>
      <div className={`${SECTION} relative border-t border-board-foreground/10 py-5`}>
        <p className="text-xs text-board-foreground/50">{copy.legal}</p>
      </div>
    </footer>
  );
}
