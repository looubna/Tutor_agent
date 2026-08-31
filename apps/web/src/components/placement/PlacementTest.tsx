"use client";

import Link from "next/link";
import { useState } from "react";
import { useLanguage } from "@/lib/i18n";
import { placementCopy, fill } from "@/lib/placement/copy";
import { PLACEMENT_QUESTIONS, levelForScore } from "@/lib/placement/questions";
import { LANGUAGE_SUBJECTS, type Subject } from "@/lib/subjects";
import { emailPlacementResult } from "@/app/actions/placement";

type Stage = "choose" | "intro" | "quiz" | "details" | "result";
const LETTERS = ["A", "B", "C"] as const;

export function PlacementTest() {
  const { lang } = useLanguage();
  const copy = placementCopy(lang);

  const [stage, setStage] = useState<Stage>("choose");
  const [subject, setSubject] = useState<Subject | null>(null);
  const [index, setIndex] = useState(0);
  const [answers, setAnswers] = useState<(number | null)[]>([]);
  const [emailState, setEmailState] = useState<"idle" | "sending" | "sent" | "failed">("idle");

  const questions = subject ? PLACEMENT_QUESTIONS[subject.id] : [];
  const total = questions.length;
  const score = answers.reduce<number>(
    (n, a, i) => (a !== null && a === questions[i]?.answer ? n + 1 : n),
    0,
  );

  function choose(next: Subject) {
    setSubject(next);
    setAnswers(new Array(PLACEMENT_QUESTIONS[next.id].length).fill(null));
    setIndex(0);
    setEmailState("idle");
    setStage("intro");
  }

  function answer(option: number) {
    setAnswers((prev) => prev.map((a, i) => (i === index ? option : a)));
  }

  function advance() {
    if (index + 1 < total) setIndex(index + 1);
    else setStage("details");
  }

  async function submitDetails(formData: FormData) {
    const email = String(formData.get("email") ?? "").trim();
    if (!email || !subject) {
      setStage("result");
      return;
    }
    setEmailState("sending");
    const res = await emailPlacementResult({
      subjectId: subject.id,
      subjectName: subject.name[lang],
      score,
      firstName: String(formData.get("firstName") ?? "").trim() || undefined,
      email,
      lang,
    });
    setEmailState(res.ok ? "sent" : "failed");
    setStage("result");
  }

  const progress =
    stage === "quiz" ? (index / total) * 100 : stage === "choose" || stage === "intro" ? 0 : 100;

  return (
    <div className="mx-auto w-full max-w-3xl px-5 py-14 sm:px-8 sm:py-20">
      {stage !== "choose" && (
        <div className="mb-10 h-1 w-full overflow-hidden rounded-full bg-border">
          <div
            className="h-full rounded-full bg-accent transition-[width] duration-300"
            style={{ width: `${progress}%` }}
          />
        </div>
      )}

      {stage === "choose" && (
        <section>
          <h1 className="text-3xl font-semibold tracking-tight text-foreground font-display sm:text-4xl">
            {copy.chooseHeading}
          </h1>
          <p className="mt-3 max-w-xl text-base leading-relaxed text-muted">{copy.chooseBody}</p>

          <ul className="mt-10 grid gap-2.5 sm:grid-cols-2">
            {LANGUAGE_SUBJECTS.map((item) => (
              <li key={item.id}>
                <button
                  type="button"
                  onClick={() => choose(item)}
                  className="flex w-full items-center gap-3 rounded-xl border border-border bg-surface px-4 py-3.5 text-left transition-colors hover:border-primary"
                >
                  <span aria-hidden="true" className="text-xl">
                    {item.emoji}
                  </span>
                  <span className="flex-1 text-sm font-semibold text-foreground">
                    {item.name[lang]}
                  </span>
                  <span className="text-xs text-muted">{item.level?.[lang]}</span>
                </button>
              </li>
            ))}
          </ul>
        </section>
      )}

      {stage === "intro" && subject && (
        <section>
          <p className="text-4xl" aria-hidden="true">
            {subject.emoji}
          </p>
          <h1 className="mt-4 text-3xl font-semibold tracking-tight text-foreground font-display sm:text-4xl">
            {fill(copy.introHeading, { language: subject.name[lang] })}
          </h1>
          <p className="mt-4 max-w-xl text-base leading-relaxed text-muted">{copy.introBody}</p>
          <p className="mt-2 max-w-xl text-sm text-muted">{copy.introNote}</p>

          <div className="mt-9 flex flex-wrap items-center gap-3">
            <button
              type="button"
              onClick={() => setStage("quiz")}
              className="rounded-xl bg-primary px-6 py-3.5 text-sm font-semibold text-white transition-colors hover:bg-primary-hover"
            >
              {copy.start}
            </button>
            <button
              type="button"
              onClick={() => setStage("choose")}
              className="rounded-xl px-4 py-3.5 text-sm font-medium text-muted transition-colors hover:text-foreground"
            >
              {copy.back}
            </button>
          </div>
        </section>
      )}

      {stage === "quiz" && subject && (
        <section>
          <p className="flex items-center gap-2.5">
            <span className="rounded-md bg-accent px-2 py-0.5 text-xs font-bold text-board">
              {index + 1}
            </span>
            <span className="text-sm text-muted font-mono">
              {index + 1}/{total}
            </span>
          </p>

          <p
            dir={subject.rtl ? "rtl" : "ltr"}
            className="mt-6 text-2xl leading-snug text-foreground font-display sm:text-3xl"
          >
            {questions[index].prompt}
          </p>

          <div className="mt-8 grid gap-2.5 sm:grid-cols-3">
            {questions[index].options.map((option, i) => {
              const picked = answers[index] === i;
              return (
                <button
                  key={option}
                  type="button"
                  onClick={() => answer(i)}
                  aria-pressed={picked}
                  dir={subject.rtl ? "rtl" : "ltr"}
                  className={`flex items-center gap-2.5 rounded-xl border px-4 py-3 text-left transition-colors ${
                    picked
                      ? "border-primary bg-primary-tint"
                      : "border-border bg-surface hover:border-primary"
                  }`}
                >
                  <span
                    aria-hidden="true"
                    className={`flex h-6 w-6 shrink-0 items-center justify-center rounded-full text-[0.65rem] font-bold ${
                      picked ? "bg-primary text-white" : "bg-background text-muted"
                    }`}
                  >
                    {LETTERS[i]}
                  </span>
                  <span className="text-sm text-foreground">{option}</span>
                </button>
              );
            })}
          </div>

          <div className="mt-9 flex flex-wrap items-center gap-3">
            <button
              type="button"
              onClick={advance}
              disabled={answers[index] === null}
              className="rounded-xl bg-primary px-6 py-3.5 text-sm font-semibold text-white transition-colors hover:bg-primary-hover disabled:opacity-40"
            >
              {index + 1 === total ? copy.seeResults : copy.next}
            </button>
            {index > 0 && (
              <button
                type="button"
                onClick={() => setIndex(index - 1)}
                className="rounded-xl px-4 py-3.5 text-sm font-medium text-muted transition-colors hover:text-foreground"
              >
                {copy.back}
              </button>
            )}
          </div>
        </section>
      )}

      {stage === "details" && (
        <section>
          <h1 className="text-3xl font-semibold tracking-tight text-foreground font-display sm:text-4xl">
            {copy.detailsHeading}
          </h1>
          <p className="mt-3 max-w-xl text-base leading-relaxed text-muted">{copy.detailsBody}</p>

          <form action={submitDetails} className="mt-9 flex max-w-md flex-col gap-4">
            <div>
              <label htmlFor="firstName" className="mb-1 block text-sm font-medium text-foreground">
                {copy.firstName}
              </label>
              <input
                id="firstName"
                name="firstName"
                type="text"
                autoComplete="given-name"
                placeholder={copy.firstNamePlaceholder}
                className="w-full rounded-lg border border-border bg-surface px-3 py-2.5 text-sm outline-none focus:border-primary"
              />
            </div>
            <div>
              <label htmlFor="email" className="mb-1 block text-sm font-medium text-foreground">
                {copy.email}
              </label>
              <input
                id="email"
                name="email"
                type="email"
                autoComplete="email"
                placeholder={copy.emailPlaceholder}
                className="w-full rounded-lg border border-border bg-surface px-3 py-2.5 text-sm outline-none focus:border-primary"
              />
              <p className="mt-1.5 text-xs text-muted">{copy.emailOptional}</p>
            </div>

            <div className="mt-2 flex flex-wrap items-center gap-3">
              <button
                type="submit"
                disabled={emailState === "sending"}
                className="rounded-xl bg-primary px-6 py-3.5 text-sm font-semibold text-white transition-colors hover:bg-primary-hover disabled:opacity-60"
              >
                {emailState === "sending" ? copy.sending : copy.seeResults}
              </button>
              <button
                type="button"
                onClick={() => setStage("result")}
                className="rounded-xl px-4 py-3.5 text-sm font-medium text-muted transition-colors hover:text-foreground"
              >
                {copy.skip}
              </button>
            </div>
          </form>
        </section>
      )}

      {stage === "result" && subject && (
        <section>
          <h1 className="text-3xl font-semibold tracking-tight text-foreground font-display sm:text-4xl">
            {fill(copy.resultHeading, { language: subject.name[lang] })}
          </h1>
          <p className="mt-3 text-base text-muted">
            {fill(copy.resultScore, { score, total })}
          </p>

          <div className="mt-8 flex flex-col gap-4 rounded-2xl border border-border bg-surface p-6 sm:flex-row sm:items-center sm:gap-6">
            <div className="flex flex-col items-center justify-center rounded-xl bg-accent-tint px-6 py-4">
              <span className="text-xs uppercase tracking-[0.14em] text-muted font-mono">
                {copy.resultLevelLabel}
              </span>
              <span className="text-4xl font-semibold text-accent-ink font-display">
                {levelForScore(score)}
              </span>
            </div>
            <div>
              <p className="text-lg font-semibold text-foreground font-display">
                {copy.levels[levelForScore(score)].name}
              </p>
              <p className="mt-1.5 text-sm leading-relaxed text-muted">
                {copy.levels[levelForScore(score)].blurb}
              </p>
            </div>
          </div>

          {emailState === "sent" && <p className="mt-4 text-sm text-success">{copy.emailSent}</p>}
          {emailState === "failed" && <p className="mt-4 text-sm text-muted">{copy.emailFailed}</p>}

          <div className="mt-9 flex flex-wrap items-center gap-3">
            <Link
              href="/signup"
              className="rounded-xl bg-primary px-6 py-3.5 text-sm font-semibold text-white transition-colors hover:bg-primary-hover"
            >
              {fill(copy.resultCta, {
                language: subject.name[lang],
                level: levelForScore(score),
              })}
            </Link>
            <button
              type="button"
              onClick={() => choose(subject)}
              className="rounded-xl px-4 py-3.5 text-sm font-medium text-muted transition-colors hover:text-foreground"
            >
              {copy.resultRetake}
            </button>
          </div>
        </section>
      )}
    </div>
  );
}
