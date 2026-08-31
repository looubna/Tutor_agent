"use client";

import { useEffect, useRef, useState } from "react";
import { useT } from "@/lib/i18n";

/**
 * A shared surface for the things speech can't carry — a spelling, a table of
 * articles, a sentence pulled apart. Drawing is kept to one pen and an eraser
 * on purpose: a lesson stalls while someone hunts for a colour picker.
 *
 * The tutor writes here too, and its lines are text rather than strokes: they
 * arrive from the lesson as words, one line at a time, so they are laid out as
 * words. Drawing them into the canvas would make them un-selectable, un-
 * scalable and impossible to correct — and would mean holding a bitmap in sync
 * with a list, which is two copies of the same truth.
 *
 * So the board is two layers with one appearance: the tutor's lines underneath,
 * the student's pen on the canvas above. The student draws over the tutor's
 * working the way you would on a real board.
 */
export function Whiteboard({
  tutorLines = [],
  onClose,
}: {
  /** What the tutor has written, in the order it was written. */
  tutorLines?: string[];
  onClose: () => void;
}) {
  const t = useT();
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const drawing = useRef(false);
  const [erasing, setErasing] = useState(false);

  // The canvas is sized in device pixels so strokes stay crisp, and redrawn on
  // resize — a bitmap resize would smear whatever is already on it.
  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;

    const fit = () => {
      const { width, height } = canvas.getBoundingClientRect();
      const ratio = window.devicePixelRatio || 1;
      const snapshot = canvas.toDataURL();
      canvas.width = width * ratio;
      canvas.height = height * ratio;
      const ctx = canvas.getContext("2d");
      if (!ctx) return;
      ctx.scale(ratio, ratio);
      ctx.lineCap = "round";
      ctx.lineJoin = "round";
      const img = new Image();
      img.onload = () => ctx.drawImage(img, 0, 0, width, height);
      img.src = snapshot;
    };

    fit();
    window.addEventListener("resize", fit);
    return () => window.removeEventListener("resize", fit);
  }, []);

  const point = (e: React.PointerEvent<HTMLCanvasElement>) => {
    const rect = e.currentTarget.getBoundingClientRect();
    return { x: e.clientX - rect.left, y: e.clientY - rect.top };
  };

  const begin = (e: React.PointerEvent<HTMLCanvasElement>) => {
    e.currentTarget.setPointerCapture(e.pointerId);
    const ctx = canvasRef.current?.getContext("2d");
    if (!ctx) return;
    const { x, y } = point(e);
    drawing.current = true;
    ctx.globalCompositeOperation = erasing ? "destination-out" : "source-over";
    ctx.strokeStyle = "#1f2937";
    ctx.lineWidth = erasing ? 24 : 3;
    ctx.beginPath();
    ctx.moveTo(x, y);
  };

  const extend = (e: React.PointerEvent<HTMLCanvasElement>) => {
    if (!drawing.current) return;
    const ctx = canvasRef.current?.getContext("2d");
    if (!ctx) return;
    const { x, y } = point(e);
    ctx.lineTo(x, y);
    ctx.stroke();
  };

  const end = () => {
    drawing.current = false;
  };

  const clear = () => {
    const canvas = canvasRef.current;
    const ctx = canvas?.getContext("2d");
    if (!canvas || !ctx) return;
    ctx.clearRect(0, 0, canvas.width, canvas.height);
  };

  return (
    <div className="absolute inset-0 flex flex-col bg-white">
      {/* The tutor's working, underneath the canvas. `pointer-events-none` so
          the student can draw straight over it — a real board does not stop
          you writing next to what the teacher wrote. */}
      {tutorLines.length > 0 && (
        <div className="pointer-events-none absolute inset-0 overflow-y-auto p-8 sm:p-12">
          <ol className="space-y-3">
            {tutorLines.map((line, i) => (
              <li
                key={`${i}-${line}`}
                className="whitespace-pre-wrap font-mono text-lg leading-snug text-[#17181c] sm:text-2xl"
              >
                {line}
              </li>
            ))}
          </ol>
        </div>
      )}
      <canvas
        ref={canvasRef}
        onPointerDown={begin}
        onPointerMove={extend}
        onPointerUp={end}
        onPointerLeave={end}
        className="flex-1 touch-none"
      />
      <div className="absolute bottom-3 left-1/2 flex -translate-x-1/2 items-center gap-1 rounded-full bg-[#1c1d22] p-1 shadow-lg">
        <BoardTool active={!erasing} onClick={() => setErasing(false)} label="Pen" />
        <BoardTool active={erasing} onClick={() => setErasing(true)} label="Eraser" />
        <BoardTool onClick={clear} label={t("lesson.clearBoard")} />
        <BoardTool onClick={onClose} label={t("lesson.closeBoard")} />
      </div>
    </div>
  );
}

function BoardTool({
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
