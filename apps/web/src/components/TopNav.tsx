"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { useEffect, useRef, useState } from "react";
import { logout } from "@/app/actions/auth";
import { Logo } from "@/components/Logo";
import { ThemeToggle } from "@/components/ThemeToggle";
import { LanguageToggle } from "@/components/LanguageToggle";
import { useT } from "@/lib/i18n";

type Menu = "book" | "account" | null;

export function TopNav({ userName }: { userName: string }) {
  const pathname = usePathname();
  const t = useT();
  const [menu, setMenu] = useState<Menu>(null);
  const barRef = useRef<HTMLElement>(null);

  // Any click outside the bar, or Escape, closes whichever menu is open.
  useEffect(() => {
    if (!menu) return;
    const onPointer = (e: MouseEvent) => {
      if (!barRef.current?.contains(e.target as Node)) setMenu(null);
    };
    const onKey = (e: KeyboardEvent) => {
      if (e.key === "Escape") setMenu(null);
    };
    document.addEventListener("mousedown", onPointer);
    document.addEventListener("keydown", onKey);
    return () => {
      document.removeEventListener("mousedown", onPointer);
      document.removeEventListener("keydown", onKey);
    };
  }, [menu]);

  const links = [
    { href: "/dashboard", label: t("nav.dashboard") },
    { href: "/course", label: t("nav.course") },
    { href: "/calendar", label: t("nav.calendar") },
  ];

  const bookLinks = [
    { href: "/book/languages", label: t("nav.bookLanguage") },
    { href: "/book/sciences", label: t("nav.bookScience") },
  ];

  const isActive = (href: string) => pathname === href || pathname.startsWith(href + "/");
  const bookingOpen = bookLinks.some((l) => isActive(l.href));

  return (
    <header
      ref={barRef}
      className="sticky top-0 z-40 border-b border-border bg-surface"
    >
      <div className="mx-auto flex h-16 w-full max-w-6xl items-center gap-5 px-6 sm:px-8">
        <Link href="/dashboard" className="flex shrink-0 items-center">
          <Logo size={34} />
        </Link>

        <nav className="flex items-center gap-1">
          {links.map((link) => (
            <Link
              key={link.href}
              href={link.href}
              aria-current={isActive(link.href) ? "page" : undefined}
              className={`rounded-lg px-3 py-2 text-sm font-medium transition-colors ${
                isActive(link.href)
                  ? "text-primary"
                  : "text-muted hover:bg-primary-tint hover:text-foreground"
              }`}
            >
              {link.label}
            </Link>
          ))}
        </nav>

        <div className="relative shrink-0">
          <button
            type="button"
            onClick={() => setMenu(menu === "book" ? null : "book")}
            aria-expanded={menu === "book"}
            aria-haspopup="menu"
            className={`flex items-center gap-2 rounded-full px-4 py-2 text-sm font-semibold text-white transition-colors ${
              bookingOpen ? "bg-primary-hover" : "bg-primary hover:bg-primary-hover"
            }`}
          >
            {t("nav.bookClass")}
            <svg viewBox="0 0 24 24" fill="none" className="h-4 w-4" aria-hidden="true">
              <path
                d={menu === "book" ? "m6 15 6-6 6 6" : "m6 9 6 6 6-6"}
                stroke="currentColor"
                strokeWidth="2"
                strokeLinecap="round"
                strokeLinejoin="round"
              />
            </svg>
          </button>

          {menu === "book" && (
            <div
              role="menu"
              className="absolute left-0 top-full z-50 mt-2 w-64 overflow-hidden rounded-xl border border-border bg-surface py-1 shadow-lg"
            >
              {bookLinks.map((link) => (
                <Link
                  key={link.href}
                  href={link.href}
                  role="menuitem"
                  onClick={() => setMenu(null)}
                  className="block px-4 py-2.5 text-sm text-foreground transition-colors hover:bg-primary-tint"
                >
                  {link.label}
                </Link>
              ))}
            </div>
          )}
        </div>

        <div className="ml-auto flex shrink-0 items-center gap-2">
          <ThemeToggle variant="light" />
          <LanguageToggle variant="light" className="hidden sm:inline-flex" />

          <div className="relative">
            <button
              type="button"
              onClick={() => setMenu(menu === "account" ? null : "account")}
              aria-expanded={menu === "account"}
              aria-haspopup="menu"
              aria-label={t("nav.account")}
              className="flex h-9 w-9 items-center justify-center rounded-full bg-primary text-sm font-semibold text-white transition-colors hover:bg-primary-hover"
            >
              {userName.trim().charAt(0).toUpperCase() || "?"}
            </button>

            {menu === "account" && (
              <div
                role="menu"
                className="absolute right-0 top-full z-50 mt-2 w-56 overflow-hidden rounded-xl border border-border bg-surface py-1 shadow-lg"
              >
                <p className="truncate border-b border-border px-4 py-2.5 text-sm font-medium text-foreground">
                  {userName}
                </p>
                <Link
                  href="/settings"
                  role="menuitem"
                  onClick={() => setMenu(null)}
                  className="block px-4 py-2.5 text-sm text-foreground transition-colors hover:bg-primary-tint"
                >
                  {t("nav.settings")}
                </Link>
                <form action={logout}>
                  <button
                    type="submit"
                    role="menuitem"
                    className="w-full px-4 py-2.5 text-left text-sm text-foreground transition-colors hover:bg-primary-tint"
                  >
                    {t("nav.logout")}
                  </button>
                </form>
              </div>
            )}
          </div>
        </div>
      </div>
    </header>
  );
}
