"use client";

import { useActionState } from "react";
import { useFormStatus } from "react-dom";
import { startLessonNow } from "@/app/actions/booking";
import type { BookingContext } from "@/app/actions/booking";
import { useT } from "@/lib/i18n";

/**
 * Opens a lesson on this chapter straight away, without a trip through the
 * calendar. The refusal — an overlapping class — is rare enough to sit in a
 * small popover under the button rather than take up room in the row.
 */
export function StartNowButton({
  context,
  className,
}: {
  context: BookingContext;
  className?: string;
}) {
  const [state, action] = useActionState(startLessonNow.bind(null, context), undefined);

  return (
    <form action={action} className="relative shrink-0">
      <Submit className={className} />
      {state?.error && (
        <p
          role="alert"
          className="absolute right-0 top-full z-10 mt-2 w-60 rounded-lg border border-border bg-surface p-2.5 text-xs leading-relaxed text-danger shadow-lg"
        >
          {state.error}
        </p>
      )}
    </form>
  );
}

function Submit({ className }: { className?: string }) {
  const t = useT();
  const { pending } = useFormStatus();

  return (
    <button type="submit" disabled={pending} className={className}>
      {pending ? t("course.starting") : t("course.startNow")}
    </button>
  );
}
