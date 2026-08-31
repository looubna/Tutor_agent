import Image from "next/image";

/**
 * The Zanoba logo, exactly as supplied — the full lockup, glyph and wordmark,
 * with only the white background removed. Not re-drawn, not recoloured, so it
 * carries the artwork's own brush edges and purple on every surface.
 */
const NATURAL = { width: 722, height: 347 };

export function Logo({ size = 32, className }: { size?: number; className?: string }) {
  return (
    <Image
      src="/brand/logo.png"
      alt="Zanoba"
      width={NATURAL.width}
      height={NATURAL.height}
      priority
      style={{ height: size, width: "auto" }}
      className={className}
    />
  );
}
