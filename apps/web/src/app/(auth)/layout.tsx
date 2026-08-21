"use client";

import Link from "next/link";
import { PlottedCurve } from "@/components/PlottedCurve";
import { Logo } from "@/components/Logo";
import { ThemeToggle } from "@/components/ThemeToggle";
import { LanguageToggle } from "@/components/LanguageToggle";
import { useT } from "@/lib/i18n";

export default function AuthLayout({ children }: { children: React.ReactNode }) {
  const t = useT();

  return (
    <div className="flex min-h-screen w-full flex-col md:flex-row">
      <div className="relative flex shrink-0 flex-col justify-between overflow-hidden bg-board px-8 py-8 text-board-foreground md:w-[42%] md:px-12 md:py-12">
        <div className="bg-grid-paper pointer-events-none absolute inset-0" />

        <div className="relative flex items-center justify-between gap-4">
          <Link href="/" className="flex items-center gap-2">
            <Logo size={36} variant="dark" />
            <span className="text-xl font-semibold font-display">Learnora</span>
          </Link>
          <div className="flex items-center gap-2">
            <ThemeToggle />
            <LanguageToggle />
          </div>
        </div>

        <div className="relative mt-10 hidden max-w-xs flex-col gap-6 md:flex">
          <PlottedCurve animate className="h-28 w-full text-accent" />
          <p className="text-2xl font-semibold leading-snug font-display">{t("auth.tagline")}</p>
          <p className="text-sm text-board-foreground/70">{t("auth.taglineBody")}</p>
        </div>

        <p className="relative hidden text-xs text-board-foreground/50 md:block">
          Learnora — an AI Math Tutor
        </p>
      </div>

      <div className="flex flex-1 flex-col items-center justify-center bg-background px-4 py-12">
        <div className="w-full max-w-sm rounded-2xl border border-border bg-surface p-8 shadow-sm">
          {children}
        </div>
      </div>
    </div>
  );
}
