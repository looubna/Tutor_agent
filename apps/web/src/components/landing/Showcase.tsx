"use client";

import Image from "next/image";
import { useState } from "react";
import { PlottedCurve } from "@/components/PlottedCurve";
import { useLanguage } from "@/lib/i18n";
import { landingCopy } from "@/lib/landingCopy";

/**
 * Photography for the four showcase cards, in card order. Drop files into
 * `public/marketing/` and put their paths here — anything left `null` renders
 * the drawn lesson mock below instead, so the section is never broken.
 *
 * Suggested crops: card 1 portrait (4:5), cards 2 and 3 landscape (16:10),
 * card 4 wide (21:9).
 */
const PHOTOS: (string | null)[] = [
  "/marketing/tutor-on-camera.jpg",
  "/marketing/shared-board-call.png",
  "/marketing/between-lessons.png",
  "/marketing/curriculum.png",
];

export function Showcase() {
  const { lang } = useLanguage();
  const copy = landingCopy(lang).showcase;

  // A bento: the video card leads at full height, the rest fill in around it.
  // `contain` cards are sized to their photograph's own ratio so the whole
  // frame shows — nothing cropped, no empty bands.
  const shapes = [
    { className: "lg:row-span-2 min-h-[26rem] lg:min-h-[34rem]", contain: false },
    { className: "", contain: true },
    { className: "min-h-[19rem]", contain: false },
    { className: "lg:col-span-2 min-h-[18rem]", contain: false },
  ];

  return (
    <section className="mx-auto w-full max-w-6xl px-5 pb-20 pt-6 sm:px-8">
      <h2 className="max-w-2xl text-3xl font-semibold tracking-tight text-foreground font-display sm:text-4xl">
        {copy.heading}
      </h2>
      <p className="mt-3 max-w-xl text-base leading-relaxed text-muted">{copy.body}</p>

      <div className="mt-10 grid gap-5 lg:grid-cols-2">
        {copy.cards.map((card, index) => (
          <ShowcaseCard
            key={card.line1}
            card={card}
            photo={PHOTOS[index]}
            variant={index}
            className={shapes[index].className}
            contain={shapes[index].contain}
            expand={copy.expand}
            collapse={copy.collapse}
          />
        ))}
      </div>
    </section>
  );
}

function ShowcaseCard({
  card,
  photo,
  variant,
  className,
  contain,
  expand,
  collapse,
}: {
  card: { line1: string; line2: string; body: string };
  photo: string | null;
  variant: number;
  className: string;
  contain: boolean;
  expand: string;
  collapse: string;
}) {
  const [open, setOpen] = useState(false);

  const heading = (
    <h3 className="text-xl font-semibold leading-snug font-display sm:text-2xl">
      <span className="block text-accent">{card.line1}</span>
      <span className="block text-board-foreground">{card.line2}</span>
    </h3>
  );

  const toggle = (
    <button
      type="button"
      onClick={() => setOpen(!open)}
      aria-expanded={open}
      className="flex h-10 w-10 shrink-0 items-center justify-center rounded-full bg-accent text-xl text-board transition-transform hover:scale-105"
    >
      <span aria-hidden="true" className={open ? "rotate-45" : undefined}>
        +
      </span>
      <span className="sr-only">{open ? collapse : expand}</span>
    </button>
  );

  const body = open && (
    <p className="animate-chalk-in max-w-md rounded-2xl bg-board/90 p-4 text-sm leading-relaxed text-board-foreground/85 backdrop-blur-sm">
      {card.body}
    </p>
  );

  // A full-frame card gives the heading its own band above the picture, so the
  // photograph is shown whole with nothing laid over it.
  if (contain && photo) {
    return (
      <article className={`flex flex-col overflow-hidden rounded-3xl bg-board ${className}`}>
        <div className="flex items-start justify-between gap-4 p-6 sm:p-7">
          {heading}
          {toggle}
        </div>
        {body && <div className="px-6 pb-5 sm:px-7">{body}</div>}
        <div className="relative aspect-3/2 w-full">
          <Image
            src={photo}
            alt=""
            fill
            quality={92}
            sizes="(min-width: 1024px) 50vw, 100vw"
            className="object-contain"
          />
        </div>
      </article>
    );
  }

  return (
    <article className={`relative flex flex-col overflow-hidden rounded-3xl bg-board ${className}`}>
      {photo ? (
        <>
          <Image
            src={photo}
            alt=""
            fill
            quality={92}
            sizes="(min-width: 1024px) 50vw, 100vw"
            className="object-cover"
          />
          {/* Two shallow gradients meeting at the top-left, so the heading stays
              readable over a bright frame while the rest keeps its colour. */}
          <div className="pointer-events-none absolute inset-x-0 top-0 h-1/2 bg-gradient-to-b from-board via-board/75 to-transparent" />
          <div className="pointer-events-none absolute inset-y-0 left-0 w-2/3 bg-gradient-to-r from-board/85 via-board/35 to-transparent" />
        </>
      ) : (
        <div className="bg-grid-paper pointer-events-none absolute inset-0" />
      )}

      <div className="relative p-6 sm:p-7">{heading}</div>

      {/* The drawn mock takes the space the heading leaves, never sits under it. */}
      {!photo && (
        <div className="relative flex min-h-0 flex-1 items-center justify-center px-6 py-4 sm:px-7">
          <LessonMock variant={variant} />
        </div>
      )}

      <div className="relative mt-auto p-6 pt-0 sm:p-7 sm:pt-0">
        {body && <div className="mb-4">{body}</div>}
        {toggle}
      </div>
    </article>
  );
}

/**
 * Stands in for photography: a drawn sketch of the thing each card describes,
 * in the same graph-paper language as the hero board.
 */
function LessonMock({ variant }: { variant: number }) {
  if (variant === 0) return <VideoCallMock />;
  if (variant === 1) return <BoardMock />;
  if (variant === 2) return <CurriculumMock />;
  return <ChatMock />;
}

/** The tutor on camera, with the student's own tile tucked into the corner. */
function VideoCallMock() {
  return (
    <div className="w-full max-w-[19rem]">
      <div className="relative aspect-[4/3] overflow-hidden rounded-2xl border border-board-foreground/15 bg-gradient-to-b from-board-foreground/[0.10] to-board-foreground/[0.03]">
        <ChalkPortrait className="absolute inset-x-0 bottom-0 mx-auto h-[76%] w-auto text-accent" />
        <span className="absolute left-3 top-3 flex items-center gap-1.5 rounded-full bg-board/70 px-2.5 py-1 text-[0.65rem] font-semibold uppercase tracking-wider text-board-foreground/85">
          <span className="h-1.5 w-1.5 rounded-full bg-success" />
          Live
        </span>
        <div className="absolute bottom-3 right-3 h-14 w-[4.5rem] overflow-hidden rounded-lg border border-board-foreground/20 bg-board">
          <ChalkPortrait className="absolute inset-x-0 bottom-0 mx-auto h-[80%] w-auto text-board-foreground/30" />
        </div>
      </div>
      <div className="mt-3 flex items-end justify-center gap-1" aria-hidden="true">
        {[6, 12, 20, 14, 26, 16, 9, 18, 11, 22, 7].map((h, i) => (
          <span key={i} style={{ height: `${h}px` }} className="w-1 rounded-full bg-accent/60" />
        ))}
      </div>
    </div>
  );
}

/** The tutor sketched the way the rest of the page draws — in chalk line. */
function ChalkPortrait({ className }: { className?: string }) {
  return (
    <svg
      viewBox="0 0 64 64"
      fill="none"
      className={className}
      stroke="currentColor"
      strokeWidth="1.8"
      strokeLinecap="round"
      strokeLinejoin="round"
      aria-hidden="true"
    >
      <circle cx="32" cy="20" r="12.5" />
      <path d="M27.5 18.5h.02M36.5 18.5h.02" strokeWidth="2.6" />
      <path d="M27 25.5c1.6 2 3.6 3 5 3s3.4-1 5-3" />
      <path d="M29 32.5v5M35 32.5v5" />
      <path d="M12 64c0-14 9-25.5 20-25.5S52 50 52 64" />
    </svg>
  );
}

function BoardMock() {
  return (
    <div className="w-full max-w-sm">
      <p className="text-lg text-board-foreground/90 font-mono">x² + 6x + 9</p>
      <p className="mt-2 text-lg text-accent font-mono">= (x + 3)²</p>
      <PlottedCurve className="mt-6 h-16 w-full text-accent" />
    </div>
  );
}

function CurriculumMock() {
  const units = [
    { label: "Unit 3 · Perfect tenses", done: true },
    { label: "Unit 4 · The subjunctive", done: true },
    { label: "Unit 5 · Reported speech", done: false },
  ];
  return (
    <div className="flex w-full max-w-sm flex-col gap-2">
      {units.map((unit) => (
        <div
          key={unit.label}
          className="flex items-center gap-3 rounded-xl border border-board-foreground/12 bg-board-foreground/5 px-3.5 py-2.5"
        >
          <span
            aria-hidden="true"
            className={`flex h-5 w-5 shrink-0 items-center justify-center rounded-full text-[0.6rem] ${
              unit.done ? "bg-success text-board" : "border border-board-foreground/30 text-transparent"
            }`}
          >
            ✓
          </span>
          <span className="truncate text-xs text-board-foreground/80 font-mono">{unit.label}</span>
        </div>
      ))}
    </div>
  );
}

function ChatMock() {
  return (
    <div className="flex w-full max-w-sm flex-col gap-2.5">
      <p className="ml-auto max-w-[80%] rounded-2xl rounded-br-sm bg-primary px-3.5 py-2.5 text-xs text-white">
        Why is question 7 minus and not plus?
      </p>
      <p className="max-w-[85%] rounded-2xl rounded-bl-sm bg-board-foreground/10 px-3.5 py-2.5 text-xs text-board-foreground/85">
        Because you factored out the −1 in line two. Try writing that step out and see what happens to the sign.
      </p>
    </div>
  );
}
