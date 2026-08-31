/**
 * The mark that sits beside every lesson: a speech bubble with a camera in it,
 * because a lesson here is a live video call rather than a page to read.
 * Painted in the brand's violet and lime, so it reads at 40px.
 */
export function LiveLessonIcon({ className }: { className?: string }) {
  return (
    <svg viewBox="0 0 40 40" fill="none" className={className} role="presentation" aria-hidden="true">
      {/* bubble, with its tail dropped to the lower left */}
      <path
        d="M20 3.5c9.1 0 16.5 6.6 16.5 14.8 0 8.2-7.4 14.8-16.5 14.8-1.9 0-3.7-.3-5.4-.8-1.5 1.9-4 3.6-7.3 4.2-.7.1-1.2-.6-.8-1.2 1.1-1.6 1.9-3.4 2.2-5A14.4 14.4 0 0 1 3.5 18.3C3.5 10.1 10.9 3.5 20 3.5Z"
        fill="var(--brand)"
      />
      {/* camera body and lens */}
      <rect x="11.5" y="13" width="12" height="9.5" rx="2.6" fill="var(--accent)" />
      <path d="M25 16.6l4.4-2.5c.6-.3 1.3.1 1.3.8v5.7c0 .7-.7 1.1-1.3.8L25 18.9v-2.3Z" fill="var(--accent)" />
    </svg>
  );
}
