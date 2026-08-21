/**
 * The Learnora mark: an "L" spine that curves up into the brand's signature
 * plotted curve, ending on a small "solved point" dot — the same visual
 * language as PlottedCurve, condensed into a badge-sized glyph.
 */
export function Logo({
  size = 32,
  variant = "dark",
  className,
}: {
  size?: number;
  variant?: "dark" | "light";
  className?: string;
}) {
  const bg = variant === "dark" ? "var(--accent)" : "var(--primary-tint)";
  const glyph = variant === "dark" ? "var(--board-foreground)" : "var(--primary)";

  return (
    <svg
      width={size}
      height={size}
      viewBox="0 0 32 32"
      className={className}
      role="img"
      aria-label="Learnora"
    >
      <rect width="32" height="32" rx="9" fill={bg} />
      <path
        d="M12 8.5V20c0 1.66 1.34 3 3 3 1.1 0 2.15-.5 2.9-1.3L21.5 18.4"
        stroke={glyph}
        strokeWidth="2.4"
        strokeLinecap="round"
        strokeLinejoin="round"
        fill="none"
      />
      <circle cx="21.5" cy="18.4" r="1.9" fill={glyph} />
    </svg>
  );
}
