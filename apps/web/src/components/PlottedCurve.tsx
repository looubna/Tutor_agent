"use client";

import { useEffect, useRef, useState } from "react";

const PATH_LENGTH = 340;
const CURVE_PATH = "M 4 96 C 40 96 46 70 78 62 C 118 52 122 20 158 12 C 190 5 200 16 236 8";

/**
 * The brand's signature mark: a single hand-plotted curve, like the line a
 * tutor traces through a student's worked graph. Draws itself in once on
 * mount; honors prefers-reduced-motion by skipping straight to fully drawn.
 */
export function PlottedCurve({
  className,
  animate = false,
}: {
  className?: string;
  animate?: boolean;
}) {
  const pathRef = useRef<SVGPathElement>(null);
  const [drawn, setDrawn] = useState(() => {
    if (!animate) return true;
    if (typeof window === "undefined") return false;
    return window.matchMedia("(prefers-reduced-motion: reduce)").matches;
  });

  useEffect(() => {
    if (drawn) return;
    const raf = requestAnimationFrame(() => setDrawn(true));
    return () => cancelAnimationFrame(raf);
  }, [drawn]);

  return (
    <svg
      viewBox="0 0 240 104"
      fill="none"
      className={className}
      role="presentation"
      aria-hidden="true"
    >
      {/* plotted points along the curve */}
      {[
        [4, 96],
        [78, 62],
        [158, 12],
        [236, 8],
      ].map(([cx, cy]) => (
        <circle key={`${cx}-${cy}`} cx={cx} cy={cy} r="3" fill="var(--accent)" opacity={drawn ? 1 : 0} style={{ transition: "opacity 0.4s ease 0.6s" }} />
      ))}
      <path
        ref={pathRef}
        d={CURVE_PATH}
        stroke="var(--accent)"
        strokeWidth="2.5"
        strokeLinecap="round"
        strokeDasharray={PATH_LENGTH}
        strokeDashoffset={drawn ? 0 : PATH_LENGTH}
        style={{ transition: animate ? "stroke-dashoffset 1.1s ease" : undefined }}
      />
    </svg>
  );
}
