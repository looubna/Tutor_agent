"use client";

import Link from "next/link";
import { Logo } from "@/components/Logo";
import { LanguageToggle } from "@/components/LanguageToggle";
import { ThemeToggle } from "@/components/ThemeToggle";
import { useLanguage } from "@/lib/i18n";
import { landingCopy } from "@/lib/landingCopy";

export function LandingNav() {
  const { lang } = useLanguage();
  const copy = landingCopy(lang).nav;

  const links = [
    { href: "#subjects", label: copy.subjects },
    { href: "#how", label: copy.how },
    { href: "#pricing", label: copy.pricing },
  ];

  return (
    <header className="sticky top-0 z-40 border-b border-border bg-background/90 text-foreground backdrop-blur-md">
      <div className="mx-auto flex h-16 w-full max-w-6xl items-center gap-6 px-5 sm:px-8">
        <Link href="/" className="flex shrink-0 items-center">
          <Logo size={38} />
        </Link>

        <nav aria-label={copy.menu} className="hidden flex-1 items-center gap-7 md:flex">
          {links.map((link) => (
            <a
              key={link.href}
              href={link.href}
              className="text-sm font-medium text-muted transition-colors hover:text-foreground"
            >
              {link.label}
            </a>
          ))}
        </nav>

        <div className="ml-auto flex items-center gap-2 md:ml-0">
          <ThemeToggle variant="light" />
          <LanguageToggle variant="light" className="hidden sm:inline-flex" />
          <Link
            href="/login"
            className="hidden rounded-lg px-3 py-2 text-sm font-medium transition-colors hover:bg-primary-tint sm:block"
          >
            {copy.login}
          </Link>
          <Link
            href="/signup"
            className="rounded-lg bg-primary px-4 py-2 text-sm font-semibold text-white transition-colors hover:bg-primary-hover"
          >
            {copy.start}
          </Link>
        </div>
      </div>
    </header>
  );
}
