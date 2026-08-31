"use client";

import { useCallback, useEffect, useRef, useState } from "react";
import { useT } from "@/lib/i18n";
import { TUTOR_NAME } from "@/lib/tutor";

/**
 * The lesson paper on the call's main stage, with the tutor writing on it.
 *
 * The paper is rendered by the server — the same renderer that makes the copy
 * a parent prints — so this component's whole job is to keep it current and to
 * follow the tutor down the page. It does that by polling the marks endpoint
 * for a count and the page the last mark landed on: when either changes, the
 * frame is reloaded and scrolled to that page.
 *
 * Polling rather than a socket. A mark is a rare event on a human timescale —
 * a tutor writes a line every half-minute, not thirty times a second — and a
 * socket held open for fifty minutes is a connection to lose, reconnect and
 * resynchronise for something two seconds of latency does not spoil.
 *
 * Reloading the frame rather than patching it is deliberate too. The marks are
 * drawn into the page by the renderer, not layered over it, so there is nothing
 * here that could drift out of alignment with the paper underneath.
 *
 * The student writes on it too. Their pen is a canvas injected INTO the frame's
 * own document rather than laid over the frame from outside: the paper scrolls,
 * and an overlay that does not scroll with it would leave every stroke in the
 * wrong place the moment the page moved. Same origin, so reaching in is
 * allowed. Their strokes are theirs — they are not sent anywhere, and they are
 * carried across the reloads that happen whenever the tutor writes.
 */
/**
 * The strokes on a white ground, which is what makes them readable.
 *
 * The pen's canvas is transparent, and a model handed a transparent PNG is
 * looking at black ink on a black field.
 */
function flatten(canvas: HTMLCanvasElement): string {
  const sheet = document.createElement("canvas");
  sheet.width = canvas.width;
  sheet.height = canvas.height;
  const context = sheet.getContext("2d");
  if (!context) return canvas.toDataURL();
  context.fillStyle = "#ffffff";
  context.fillRect(0, 0, sheet.width, sheet.height);
  context.drawImage(canvas, 0, 0);
  return sheet.toDataURL("image/png");
}

/** How long after the last character the writing hand stays on the page. */
const PEN_REST_MS = 500;

export function LessonPaper({
  bookingId,
  onClose,
  onInk,
  writing,
  writingOn,
  writingStep = 0,
  writingBusy = false,
  writingRun = 0,
  page,
  hold = false,
}: {
  bookingId: string;
  onClose: () => void;
  /**
   * Hands the student's handwriting up, so it can be sent with their next
   * turn. A student who answers by writing on the page has answered, and a
   * tutor that cannot see the page is marking blind.
   */
  onInk?: (png: string | null) => void;
  /**
   * The line the tutor is writing right now, revealed a character at a time
   * while it says it. Null between steps.
   */
  writing?: string | null;
  /** Which page that line is being written on. */
  writingOn?: string | null;
  /**
   * Which step of the explanation it belongs to. Each step gets its own line,
   * so a four-step explanation leaves four lines rather than one that four
   * steps took turns overwriting.
   */
  writingStep?: number;
  /** Still being written, so the page shows a nib at the end of the line. */
  writingBusy?: boolean;
  /**
   * Which explanation this is. When it changes, the previous one's lines are
   * cleared — otherwise they stay under the new ones and the tutor looks like
   * it has written the same thing twice.
   */
  writingRun?: number;
  /**
   * The page the explanation has reached. It overrides the page the marks say
   * we are on: the tutor's page turns all land server-side at once, and
   * following those would jump the paper to the last one while the student is
   * still hearing about the first.
   */
  page?: string | null;
  /**
   * Hold the page still while the tutor is explaining.
   *
   * Every mark it makes changes the mark count, and the frame reloads on that —
   * so a four-step explanation reloaded the paper four times, mid-sentence,
   * each one a visible flash. The marks are already being drawn live as they
   * are spoken; the reload that makes them permanent can wait for the end.
   */
  hold?: boolean;
}) {
  const t = useT();
  // Two counts: what the poll has seen, and what the frame is built from. They
  // are the same except while the tutor is explaining, when the second is held
  // back so the page does not reload under the words being spoken.
  const [marks, setMarks] = useState(0);
  const [settled, setSettled] = useState(0);
  const held = useRef(hold);
  useEffect(() => { held.current = hold; }, [hold]);
  const [showing, setShowing] = useState<string | null>(null);
  const [problem, setProblem] = useState<string | null>(null);
  const [justMarked, setJustMarked] = useState(false);
  const previous = useRef(0);

  const frame = useRef<HTMLIFrameElement>(null);
  const [pen, setPen] = useState<"off" | "draw" | "erase">("off");
  /** Lifts the writing hand once the line has stopped growing. */
  const penUp = useRef<number | undefined>(undefined);
  useEffect(() => () => window.clearTimeout(penUp.current), []);
  const penRef = useRef(pen);
  useEffect(() => { penRef.current = pen; }, [pen]);
  /** The student's strokes, kept across the reloads the tutor's marks cause. */
  const kept = useRef<string | null>(null);

  useEffect(() => {
    let live = true;
    const tick = async () => {
      try {
        const response = await fetch(`/api/lesson/${bookingId}/marks`, { cache: "no-store" });
        if (!live) return;
        if (!response.ok) {
          setProblem((await response.json())?.error ?? null);
          return;
        }
        const body = (await response.json()) as { marks: number; showing: string | null };
        setProblem(null);
        setMarks(body.marks);
        if (!held.current) setSettled(body.marks);
        setShowing(body.showing);
      } catch {
        // A dropped poll is not worth telling the student about; the next one
        // is two seconds away.
      }
    };
    tick();
    const id = setInterval(tick, 2000);
    return () => {
      live = false;
      clearInterval(id);
    };
  }, [bookingId]);

  // "Luna is writing" is shown from the mark arriving, not from a status the
  // agent claims: the mark is the evidence.
  useEffect(() => {
    if (marks === previous.current) return;
    previous.current = marks;
    setJustMarked(true);
    const id = setTimeout(() => setJustMarked(false), 2500);
    return () => clearTimeout(id);
  }, [marks]);

  /**
   * Put a drawing surface inside the paper, once it has loaded.
   *
   * Sized to the whole scrollable document, not the window, so a stroke stays
   * on the line it was drawn on. `pointer-events` follows the pen: with the pen
   * down the canvas takes the input, and with it up the paper scrolls normally.
   */
  const dressTheFrame = useCallback(() => {
    const doc = frame.current?.contentDocument;
    if (!doc?.body) return;

    const width = doc.documentElement.scrollWidth;
    const height = doc.documentElement.scrollHeight;

    // One pen per document. The frame reloads on every mark the tutor makes,
    // and appending a fresh canvas each time buries the previous strokes under
    // a stack of transparent layers.
    doc.querySelectorAll('[data-role="student-pen"]').forEach((old) => old.remove());

    const canvas = doc.createElement("canvas");
    canvas.width = width;
    canvas.height = height;
    Object.assign(canvas.style, {
      position: "absolute", top: "0", left: "0", zIndex: "50",
      width: `${width}px`, height: `${height}px`, touchAction: "none",
      pointerEvents: penRef.current === "off" ? "none" : "auto",
    });
    canvas.dataset.role = "student-pen";
    doc.body.style.position = doc.body.style.position || "relative";
    doc.body.appendChild(canvas);

    const context = canvas.getContext("2d");
    if (!context) return;
    context.lineCap = "round";
    context.lineJoin = "round";

    // Whatever they had drawn before the tutor's last mark reloaded the page.
    if (kept.current) {
      const previousInk = new Image();
      previousInk.onload = () => context.drawImage(previousInk, 0, 0);
      previousInk.src = kept.current;
    }

    let drawing = false;
    const at = (e: PointerEvent) => {
      const box = canvas.getBoundingClientRect();
      return { x: e.clientX - box.left, y: e.clientY - box.top };
    };
    canvas.addEventListener("pointerdown", (e) => {
      canvas.setPointerCapture(e.pointerId);
      drawing = true;
      const { x, y } = at(e);
      context.globalCompositeOperation =
        penRef.current === "erase" ? "destination-out" : "source-over";
      context.strokeStyle = "#1d4ed8";   // the student's ink, not the tutor's red
      context.lineWidth = penRef.current === "erase" ? 26 : 2.5;
      context.beginPath();
      context.moveTo(x, y);
    });
    canvas.addEventListener("pointermove", (e) => {
      if (!drawing) return;
      const { x, y } = at(e);
      context.lineTo(x, y);
      context.stroke();
    });
    const finish = () => {
      if (!drawing) return;
      drawing = false;
      kept.current = canvas.toDataURL();
      onInk?.(flatten(canvas));
    };
    canvas.addEventListener("pointerup", finish);
    canvas.addEventListener("pointerleave", finish);
  }, [onInk]);

  /**
   * Type the line into the paper itself, where it is going to stay.
   *
   * It used to be a floating box over the middle of the frame: a second piece
   * of text, above the page, in a different place from the mark — and it
   * vanished when the step ended, so the writing appeared and then went away
   * again. This puts the words into the page's own marks block, styled the way
   * the renderer styles them, so what streams in is what stays. The reload at
   * the end of the explanation replaces it with the real mark in the same
   * place, which is why nothing moves.
   */
  useEffect(() => {
    const doc = frame.current?.contentDocument;
    if (!doc || writing == null) return;

    const slide = (writingOn && doc.getElementById(writingOn))
      ?? doc.querySelector(".slide");
    if (!slide) return;

    // The hand needs a rule to move by, and the paper is a separate document
    // with its own stylesheet. Checked here rather than injected once on load,
    // because the frame reloads on every mark and takes the rule with it.
    if (!doc.getElementById("lesson-nib-style")) {
      const style = doc.createElement("style");
      style.id = "lesson-nib-style";
      style.textContent = `
        .lesson-nib {
          display: inline-block; margin-left: .18em; font-size: .95em;
          line-height: 1; transform-origin: 20% 80%;
          animation: lesson-nib-write .85s ease-in-out infinite;
        }
        @keyframes lesson-nib-write {
          0%, 100% { transform: translate(0, 0) rotate(-4deg); }
          30%      { transform: translate(.08em, -.07em) rotate(3deg); }
          65%      { transform: translate(-.05em, .05em) rotate(-7deg); }
        }
        @media (prefers-reduced-motion: reduce) {
          .lesson-nib { animation: none; }
        }`;
      doc.head.appendChild(style);
    }

    // A new explanation wipes the last one's lines wherever they were left.
    doc.querySelectorAll('[data-role="live-ink"]').forEach((block) => {
      if ((block as HTMLElement).dataset.run !== String(writingRun)) block.remove();
    });

    let live = slide.querySelector<HTMLElement>('[data-role="live-ink"]');
    if (!live) {
      const block = doc.createElement("div");
      block.className = "marks below";
      block.dataset.role = "live-ink";
      block.dataset.run = String(writingRun);
      // Before the page number, which is where the renderer puts its marks.
      slide.insertBefore(block, slide.querySelector("footer.pg"));
      live = block;
    }

    let line = live.querySelector<HTMLElement>(`[data-step="${writingStep}"]`);
    if (!line) {
      line = doc.createElement("p");
      line.className = "hand hand";
      line.dataset.step = String(writingStep);
      live.appendChild(line);
    }
    // The hand: it sits at the end of the line while it is still being written
    // and goes once the line is finished. Without it the text simply grows,
    // which does not read as somebody writing — and a blinking block, which is
    // what used to be here, reads as a terminal rather than as a person with a
    // pen. It is decoration over text that is already there, so it is hidden
    // from anything reading the page aloud.
    line.textContent = writing;

    // The hand shows while the line is still growing, and is taken off shortly
    // after it stops. Driven by the writing itself rather than by a flag from
    // the call screen: the flag has to be raised and lowered by whichever code
    // path is doing the writing, and there are two of them — the written
    // lesson's beats and the spoken lesson's marks — so it was only ever
    // correct in one. A line that is still changing is a line still being
    // written, and that is knowable right here.
    const hand = doc.createElement("span");
    hand.className = "lesson-nib";
    hand.setAttribute("aria-hidden", "true");
    hand.textContent = "✍️";
    line.appendChild(hand);
    window.clearTimeout(penUp.current);
    penUp.current = window.setTimeout(() => hand.remove(), PEN_REST_MS);
  }, [writing, writingOn, writingStep, writingBusy, writingRun]);

  // Follow the explanation to its page without reloading the frame: a reload
  // would wipe the student's pen and restart the paper mid-sentence.
  useEffect(() => {
    if (!page) return;
    frame.current?.contentDocument
      ?.getElementById(page)
      ?.scrollIntoView({ behavior: "smooth", block: "start" });
  }, [page]);

  // The pen can be picked up and put down without redrawing anything.
  useEffect(() => {
    const canvas = frame.current?.contentDocument
      ?.querySelector<HTMLCanvasElement>('[data-role="student-pen"]');
    if (canvas) canvas.style.pointerEvents = pen === "off" ? "none" : "auto";
  }, [pen]);

  const clearInk = () => {
    const canvas = frame.current?.contentDocument
      ?.querySelector<HTMLCanvasElement>('[data-role="student-pen"]');
    const context = canvas?.getContext("2d");
    if (canvas && context) context.clearRect(0, 0, canvas.width, canvas.height);
    kept.current = null;
    onInk?.(null);
  };

  // The cache-buster is the mark count, so the frame reloads exactly when there
  // is something new on the paper and at no other time. The hash scrolls to the
  // page the tutor is working on.
  const at = page ?? showing;
  const src = `/api/lesson/${bookingId}/paper?v=live&marks=${settled}${at ? `#${at}` : ""}`;

  if (problem) {
    return (
      <div className="flex h-full w-full flex-col items-center justify-center gap-3 p-6 text-center">
        <p className="max-w-sm text-sm text-[#9a9ca5]">{problem}</p>
        <button
          onClick={onClose}
          className="rounded-lg px-3 py-1.5 text-xs font-medium text-[#c9cbd2] transition-colors hover:bg-white/10"
        >
          {t("lesson.closePaper")}
        </button>
      </div>
    );
  }

  return (
    <div className="relative h-full w-full bg-[#f4f2ef]">
      <iframe
        ref={frame}
        key={src}
        src={src}
        onLoad={dressTheFrame}
        title={t("lesson.paper")}
        className="h-full w-full border-0"
      />

      {/* The student's own pen, in the same place the board keeps its tools. */}
      <div className="absolute bottom-3 left-1/2 flex -translate-x-1/2 items-center gap-1 rounded-full bg-[#1c1d22] p-1 shadow-lg">
        <PaperTool active={pen === "draw"} label={t("lesson.write")}
                   onClick={() => setPen((p) => (p === "draw" ? "off" : "draw"))} />
        <PaperTool active={pen === "erase"} label={t("lesson.erase")}
                   onClick={() => setPen((p) => (p === "erase" ? "off" : "erase"))} />
        <PaperTool label={t("lesson.clearBoard")} onClick={clearInk} />
      </div>
      {justMarked && (
        <span className="pointer-events-none absolute left-3 top-3 flex items-center gap-2 rounded-md bg-black/70 px-2.5 py-1 text-[11px] text-white">
          <span aria-hidden="true">✍️</span>
          {t("lesson.paperWriting", { name: TUTOR_NAME })}
        </span>
      )}
    </div>
  );
}


function PaperTool({
  active = false,
  onClick,
  label,
}: {
  active?: boolean;
  onClick: () => void;
  label: string;
}) {
  return (
    <button
      onClick={onClick}
      aria-pressed={active}
      className={`rounded-full px-3 py-1.5 text-xs font-medium transition-colors ${
        active ? "bg-white text-[#1c1d22]" : "text-[#e8e9ed] hover:bg-white/10"
      }`}
    >
      {label}
    </button>
  );
}
