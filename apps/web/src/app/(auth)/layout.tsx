"use client";

import Link from "next/link";
import { RoadToSun } from "@/components/RoadToSun";
import { Logo } from "@/components/Logo";
import { ThemeToggle } from "@/components/ThemeToggle";
import { LanguageToggle } from "@/components/LanguageToggle";
import { useT } from "@/lib/i18n";

export default function AuthLayout({ children }: { children: React.ReactNode }) {
  const t = useT();

  return (
    <div className="flex min-h-screen w-full flex-col md:flex-row">
      <div className="relative flex shrink-0 flex-col justify-between overflow-hidden bg-chalk px-8 py-8 text-chalk-ink md:w-[42%] md:px-12 md:py-12">
        <div className="bg-grid-chalk pointer-events-none absolute inset-0" />

        <div className="relative flex items-center justify-between gap-4">
          <Link href="/" className="flex items-center">
            <Logo size={46} />
          </Link>
          <div className="flex items-center gap-2">
            <ThemeToggle variant="light" />
            <LanguageToggle variant="light" />
          </div>
        </div>

        <div className="relative mt-10 hidden max-w-xs flex-col gap-6 md:flex">
          <RoadToSun animate className="h-32 w-full text-accent-ink" />
          <p className="text-2xl font-semibold leading-snug font-display">{t("auth.tagline")}</p>
          <p className="text-sm text-chalk-ink/70">{t("auth.taglineBody")}</p>
        </div>

      </div>

      <div className="flex flex-1 flex-col items-center justify-center bg-background px-4 py-12">
        <div className="w-full max-w-sm rounded-2xl border border-border bg-surface p-8 shadow-sm">
          {children}
        </div>
      </div>
    </div>
  );
}
