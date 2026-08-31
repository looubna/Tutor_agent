"use client";

import { useActionState, useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { useFormStatus } from "react-dom";
import { updateSupportLanguage } from "@/app/actions/preferences";
import { HelpLanguageField } from "@/components/HelpLanguageField";
import { useLanguage, useT } from "@/lib/i18n";

/**
 * Asked once, on the way into a language class, when the learner has never
 * chosen a help language — someone who used "Start now" never passed through
 * the booking form. The lesson itself waits behind it, because the tutor needs
 * the answer in its very first sentence.
 */
export function HelpLanguageGate({ subjectName }: { subjectName: string }) {
  const router = useRouter();
  const { lang } = useLanguage();
  const [help, setHelp] = useState<string>(lang);
  const [state, action] = useActionState(updateSupportLanguage, undefined);

  // The lesson page reads the saved value on the server, so it has to re-render
  // for the class to start.
  useEffect(() => {
    if (state?.saved) router.refresh();
  }, [state?.saved, router]);

  return (
    <div className="flex min-h-dvh items-center justify-center bg-background p-6">
      <form action={action} className="w-full max-w-md">
        <input type="hidden" name="supportLanguage" value={help} />
        <HelpLanguageField value={help} onChange={setHelp} subjectName={subjectName} />
        <Submit />
        {state?.error && (
          <p role="alert" className="mt-2 text-xs text-danger">
            {state.error}
          </p>
        )}
      </form>
    </div>
  );
}

function Submit() {
  const t = useT();
  const { pending } = useFormStatus();

  return (
    <button
      type="submit"
      disabled={pending}
      className="mt-4 w-full rounded-full bg-primary px-4 py-2.5 text-sm font-semibold text-white transition-colors hover:bg-primary-hover disabled:opacity-60"
    >
      {pending ? t("course.starting") : t("course.startNow")}
    </button>
  );
}
