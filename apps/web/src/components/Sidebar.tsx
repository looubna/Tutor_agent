"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { logout } from "@/app/actions/auth";
import { Logo } from "@/components/Logo";
import { useT } from "@/lib/i18n";

export function Sidebar({ userName }: { userName: string }) {
  const pathname = usePathname();
  const t = useT();

  const NAV_ITEMS = [
    { href: "/dashboard", label: t("nav.dashboard") },
    { href: "/calendar", label: t("nav.calendar") },
    { href: "/book", label: t("nav.book") },
    { href: "/settings", label: t("nav.settings") },
  ];

  return (
    <aside className="flex h-full w-64 shrink-0 flex-col border-r border-border bg-surface px-4 py-6 text-foreground">
      <Link href="/dashboard" className="mb-8 flex items-center gap-2 px-2">
        <Logo size={32} variant="light" />
        <span className="text-lg font-semibold font-display">Learnora</span>
      </Link>

      <nav className="flex flex-1 flex-col gap-1">
        {NAV_ITEMS.map((item) => {
          const active = pathname === item.href || pathname.startsWith(item.href + "/");
          return (
            <Link
              key={item.href}
              href={item.href}
              className={`rounded-r-md border-l-2 px-3 py-2 text-sm font-medium transition-colors ${
                active
                  ? "border-primary bg-primary-tint text-primary"
                  : "border-transparent text-muted hover:border-border hover:text-foreground"
              }`}
            >
              {item.label}
            </Link>
          );
        })}
      </nav>

      <div className="mt-auto flex flex-col gap-2 border-t border-border pt-4">
        <p className="truncate px-3 text-sm text-muted">{userName}</p>
        <form action={logout}>
          <button
            type="submit"
            className="w-full rounded-lg px-3 py-2 text-left text-sm font-medium text-muted transition-colors hover:bg-primary-tint hover:text-foreground"
          >
            {t("nav.logout")}
          </button>
        </form>
      </div>
    </aside>
  );
}
