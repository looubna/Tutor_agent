"use client";

import { useT } from "@/lib/i18n";

/**
 * Empty-state illustration: a desk calendar with nothing pencilled in, sitting
 * on its stand. Drawn in the app's own tokens so it follows light and dark.
 */
export function EmptyCalendar({ width = 190, className }: { width?: number; className?: string }) {
  const t = useT();

  return (
    <svg
      viewBox="0 0 200 196"
      width={width}
      height={(width * 196) / 200}
      className={className}
      role="img"
      aria-label={t("empty.calendarLabel")}
    >
      {/* the stand it rests on */}
      <path
        d="M34 150h132a7 7 0 0 1 7 7v22a7 7 0 0 1-7 7H34a7 7 0 0 1-7-7v-22a7 7 0 0 1 7-7Z"
        fill="var(--primary-tint)"
        stroke="var(--primary)"
        strokeWidth="3"
      />
      <path d="M28 162h144" stroke="var(--primary)" strokeWidth="3" strokeLinecap="round" />
      <rect
        x="80" y="169" width="40" height="9" rx="4.5"
        fill="var(--accent)" stroke="var(--primary)" strokeWidth="2.5"
      />

      {/* the calendar, propped at a slight angle */}
      <g transform="rotate(-3 100 84)">
        <rect
          x="44" y="28" width="112" height="118" rx="11"
          fill="var(--surface)" stroke="var(--primary)" strokeWidth="3"
        />
        <path
          d="M44 39a11 11 0 0 1 11-11h90a11 11 0 0 1 11 11v14H44V39Z"
          fill="var(--primary)"
        />
        <path d="M44 53h112" stroke="var(--primary)" strokeWidth="3" />

        {/* binding rings */}
        {[60, 80, 100, 120, 140].map((x) => (
          <path
            key={x}
            d={`M${x} 32V18a5.5 5.5 0 0 1 11 0v14`}
            fill="none"
            stroke="var(--primary)"
            strokeWidth="3"
            strokeLinecap="round"
          />
        ))}

        {/* an empty month — every day open, none of them booked */}
        {[76, 100, 124].map((y) => (
          <g key={y}>
            {[62, 81, 100, 119, 138].map((x) => (
              <circle key={x} cx={x} cy={y} r="5" fill="var(--muted)" opacity="0.28" />
            ))}
          </g>
        ))}
        <circle cx="100" cy="100" r="11" fill="none" stroke="var(--accent)" strokeWidth="3.5" />
      </g>
    </svg>
  );
}
