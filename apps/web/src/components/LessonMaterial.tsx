"use client";

import { useT } from "@/lib/i18n";

/**
 * The lesson's handout. Opens in a new tab so the learner keeps the lesson
 * page. Lessons without a PDF say so rather than showing a dead button.
 */
export function LessonMaterial({ material }: { material: string | null }) {
  const t = useT();

  if (!material) {
    return <p className="text-sm text-muted">{t("course.noMaterial")}</p>;
  }

  return (
    <a
      href={material}
      target="_blank"
      rel="noopener noreferrer"
      className="inline-flex items-center gap-2 rounded-full border border-primary px-5 py-2.5 text-sm font-semibold text-primary transition-colors hover:bg-primary-tint"
    >
      <svg viewBox="0 0 24 24" fill="none" className="h-4 w-4" aria-hidden="true">
        <path
          d="M14 3H7a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h10a2 2 0 0 0 2-2V8l-5-5Z"
          stroke="currentColor"
          strokeWidth="1.7"
          strokeLinejoin="round"
        />
        <path d="M14 3v5h5" stroke="currentColor" strokeWidth="1.7" strokeLinejoin="round" />
      </svg>
      {t("course.openMaterial")}
    </a>
  );
}
