"use client";

import { useEffect, useState } from "react";
import { useT } from "@/lib/i18n";

type Theme = "light" | "dark";
const STORAGE_KEY = "theme";

function getEffectiveTheme(): Theme {
  const stamped = document.documentElement.dataset.theme;
  if (stamped === "light" || stamped === "dark") return stamped;
  return window.matchMedia("(prefers-color-scheme: dark)").matches ? "dark" : "light";
}

export function ThemeToggle({
  className,
  variant = "dark",
}: {
  className?: string;
  variant?: "light" | "dark";
}) {
  const t = useT();
  const [theme, setTheme] = useState<Theme | null>(null);

  useEffect(() => {
    // Reads the DOM's already-applied theme (set by the blocking init script
    // or the OS media query) once after mount — not a render-derivable value.
    // eslint-disable-next-line react-hooks/set-state-in-effect
    setTheme(getEffectiveTheme());
  }, []);

  const toggle = () => {
    const next: Theme = (theme ?? getEffectiveTheme()) === "dark" ? "light" : "dark";
    document.documentElement.dataset.theme = next;
    try {
      window.localStorage.setItem(STORAGE_KEY, next);
    } catch {
      // ignore write failures (private browsing, etc.)
    }
    setTheme(next);
  };

  const current = theme ?? "light";

  const variantClasses =
    variant === "light"
      ? "text-muted hover:bg-primary-tint hover:text-foreground"
      : "text-board-foreground/80 hover:bg-board-foreground/10 hover:text-board-foreground";

  return (
    <button
      type="button"
      onClick={toggle}
      aria-label={current === "dark" ? t("theme.toggleToLight") : t("theme.toggleToDark")}
      className={`flex h-8 w-8 shrink-0 items-center justify-center rounded-full transition-colors ${variantClasses} ${className ?? ""}`}
    >
      {current === "dark" ? <SunIcon /> : <MoonIcon />}
    </button>
  );
}

function SunIcon() {
  return (
    <svg viewBox="0 0 20 20" fill="none" className="h-4 w-4" aria-hidden="true">
      <circle cx="10" cy="10" r="3.5" stroke="currentColor" strokeWidth="1.5" />
      <g stroke="currentColor" strokeWidth="1.5" strokeLinecap="round">
        <path d="M10 2.5v2M10 15.5v2M17.5 10h-2M4.5 10h-2M15.3 4.7l-1.4 1.4M6.1 13.9l-1.4 1.4M15.3 15.3l-1.4-1.4M6.1 6.1L4.7 4.7" />
      </g>
    </svg>
  );
}

function MoonIcon() {
  return (
    <svg viewBox="0 0 20 20" fill="none" className="h-4 w-4" aria-hidden="true">
      <path
        d="M16.5 12.5A7 7 0 1 1 7.5 3.5a5.5 5.5 0 0 0 9 9Z"
        stroke="currentColor"
        strokeWidth="1.5"
        strokeLinejoin="round"
      />
    </svg>
  );
}
