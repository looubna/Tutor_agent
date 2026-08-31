"use client";

import { useEffect, useId, useState } from "react";

/* The road is a tapered ribbon along a rising S-curve — the same left-to-right
   climb the old plotted line made — sampled to two verges that narrow as they
   go, so it reads as distance. It runs off the near edge of the frame and ends
   under the sun. */
const LEFT_VERGE =
  "M-29.7 120 L-21.7 119.3 L-14.1 118.2 L-6.9 116.8 L-0.1 115.2 L6.4 113.3 L12.6 111.3 L18.5 109.1 L24.2 106.7 L29.6 104.3 L34.9 101.8 L40 99.3 L45 96.8 L49.9 94.3 L54.7 91.9 L59.6 89.6 L64.4 87.4 L69.4 85.3 L74.4 83.5 L79.6 81.8 L84.9 80.3 L90.6 78.7 L96.2 77 L101.6 75.1 L106.8 73 L112 70.9 L117.1 68.6 L122.1 66.3 L127.1 63.8 L132.2 61.4 L137.2 58.9 L142.3 56.4 L147.6 53.9 L152.9 51.5 L158.4 49.1 L164.1 46.7 L170 44.5 L176.1 42.3 L182.5 40.3 L189.2 38.5 L196.2 36.8";
const RIGHT_VERGE =
  "M-30.3 102 L-23.1 101.8 L-16.3 101.3 L-9.8 100.5 L-3.6 99.5 L2.4 98.3 L8.1 96.9 L13.7 95.3 L19.1 93.5 L24.4 91.7 L29.6 89.7 L34.8 87.7 L39.9 85.6 L45 83.5 L50.2 81.5 L55.4 79.5 L60.7 77.6 L66 75.9 L71.6 74.3 L77.2 72.9 L83.1 71.7 L88.6 70.7 L94 69.4 L99.2 68 L104.4 66.4 L109.6 64.7 L114.7 62.8 L119.8 60.9 L124.9 58.8 L130.1 56.7 L135.3 54.6 L140.6 52.4 L146 50.3 L151.5 48.1 L157.2 46 L163.1 44 L169.1 42 L175.4 40.1 L182 38.3 L188.7 36.7 L195.8 35.2";
const ROAD = `${LEFT_VERGE} L195.8 35.2 L188.7 36.7 L182 38.3 L175.4 40.1 L169.1 42 L163.1 44 L157.2 46 L151.5 48.1 L146 50.3 L140.6 52.4 L135.3 54.6 L130.1 56.7 L124.9 58.8 L119.8 60.9 L114.7 62.8 L109.6 64.7 L104.4 66.4 L99.2 68 L94 69.4 L88.6 70.7 L83.1 71.7 L77.2 72.9 L71.6 74.3 L66 75.9 L60.7 77.6 L55.4 79.5 L50.2 81.5 L45 83.5 L39.9 85.6 L34.8 87.7 L29.6 89.7 L24.4 91.7 L19.1 93.5 L13.7 95.3 L8.1 96.9 L2.4 98.3 L-3.6 99.5 L-9.8 100.5 L-16.3 101.3 L-23.1 101.8 L-30.3 102 Z`;
const VERGE_LENGTH = 250;

/** Centre line: each dash shorter and thinner than the last. */
const DASHES = [
  { d: "M-25.4 110.8 L-9.8 108.9", w: 3.9 },
  { d: "M1.8 106.5 L14.2 102.8", w: 3.4 },
  { d: "M23.7 99.3 L34.2 94.9", w: 3.0 },
  { d: "M42.5 91.2 L52.1 86.9", w: 2.7 },
  { d: "M60 83.5 L69.4 80", w: 2.3 },
  { d: "M77.5 77.6 L87.3 75.3", w: 2.0 },
  { d: "M95.3 73.1 L104 70.3", w: 1.8 },
  { d: "M111.3 67.6 L119.3 64.3", w: 1.4 },
  { d: "M126.1 61.3 L133.8 57.8", w: 1.2 },
  { d: "M140.5 54.8 L148.2 51.5", w: 1.0 },
  { d: "M155 48.6 L162.9 45.6", w: 0.7 },
  { d: "M170 43.1 L178.2 40.5", w: 0.6 },
];

/** Milestones already passed, standing at the verge — the plotted points of
 *  the old curve, now markers along the way. */
const MILESTONES = [
  { cx: 8.2, cy: 89.8, r: 2.9 },
  { cx: 70.2, cy: 90.9, r: 2.2 },
  { cx: 111, cy: 59.5, r: 1.6 },
  { cx: 159.6, cy: 52.2, r: 1.1 },
];

/** Rays, kept clear of the side the road arrives from. */
const RAYS = ["M200 10v-7", "M214 15.5 219 10", "M186 15.5 181 10", "M218 30h7", "M214.5 44 219.5 49.5"];

/**
 * The brand's signature mark: a road climbing out of the frame to a sun on the
 * horizon — the ground a student covers, and where it gets them. Draws itself
 * in once on mount; honors prefers-reduced-motion by skipping straight to
 * fully drawn.
 */
export function RoadToSun({
  className,
  animate = false,
}: {
  className?: string;
  animate?: boolean;
}) {
  const uid = useId();
  const glow = `road-glow-${uid}`;
  const disc = `road-disc-${uid}`;
  const surface = `road-surface-${uid}`;

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

  const fadeIn = (delay: number) => ({
    transition: animate ? `opacity 0.6s ease ${delay}s, transform 0.8s ease ${delay}s` : undefined,
  });

  return (
    <svg
      viewBox="0 0 240 120"
      fill="none"
      className={className}
      role="presentation"
      aria-hidden="true"
    >
      <defs>
        <radialGradient id={glow}>
          <stop offset="0%" stopColor="#ffd166" stopOpacity="0.65" />
          <stop offset="55%" stopColor="#f4a13c" stopOpacity="0.17" />
          <stop offset="100%" stopColor="#f4a13c" stopOpacity="0" />
        </radialGradient>
        <linearGradient id={disc} x1="0" y1="0" x2="0" y2="1">
          <stop offset="0%" stopColor="#ffdf8a" />
          <stop offset="100%" stopColor="#f0972f" />
        </linearGradient>
        {/* the surface warms as it nears the sun */}
        <linearGradient id={surface} x1="0" y1="1" x2="1" y2="0">
          <stop offset="0%" stopColor="#fff8e6" stopOpacity="0.55" />
          <stop offset="100%" stopColor="#ffe0a3" stopOpacity="0.8" />
        </linearGradient>
      </defs>

      {/* the light the road is headed for, laid down before the road itself so
          the far end runs in behind the disc */}
      <g opacity={drawn ? 1 : 0} transform={drawn ? undefined : "translate(0 10)"} style={fadeIn(0.15)}>
        <circle cx="200" cy="30" r="36" fill={`url(#${glow})`} />
        <g stroke="#f0972f" strokeWidth="1.8" strokeLinecap="round" opacity="0.6">
          {RAYS.map((d) => (
            <path key={d} d={d} />
          ))}
        </g>
      </g>

      <path d={ROAD} fill={`url(#${surface})`} opacity={drawn ? 1 : 0} style={fadeIn(0.25)} />
      {[LEFT_VERGE, RIGHT_VERGE].map((d) => (
        <path
          key={d}
          d={d}
          stroke="currentColor"
          strokeWidth="2"
          strokeLinecap="round"
          strokeLinejoin="round"
          strokeDasharray={VERGE_LENGTH}
          strokeDashoffset={drawn ? 0 : VERGE_LENGTH}
          style={{ transition: animate ? "stroke-dashoffset 1.2s ease" : undefined }}
        />
      ))}

      {DASHES.map((dash, i) => (
        <path
          key={dash.d}
          d={dash.d}
          stroke="currentColor"
          strokeWidth={dash.w}
          strokeLinecap="round"
          opacity={drawn ? 0.45 : 0}
          style={fadeIn(0.5 + i * 0.05)}
        />
      ))}

      {MILESTONES.map((m, i) => (
        <circle
          key={m.cx}
          cx={m.cx}
          cy={m.cy}
          r={m.r}
          fill="currentColor"
          opacity={drawn ? 0.85 : 0}
          style={fadeIn(0.65 + i * 0.12)}
        />
      ))}

      {/* the sun's disc sits over the road's far end */}
      <circle
        cx="200"
        cy="30"
        r="12"
        fill={`url(#${disc})`}
        opacity={drawn ? 1 : 0}
        style={fadeIn(0.15)}
      />
    </svg>
  );
}
