"use client";

import { useEffect, useRef, useState } from "react";
import { LOCALES, localeFor, useLanguage } from "@/lib/i18n";

/**
 * The interface-language switcher. With one locale per language taught, the
 * old two-button pill no longer fits, so the trigger keeps the compact
 * two-letter shape and opens a menu of every language written in itself.
 */
export function LanguageToggle({
  className,
  variant = "dark",
}: {
  className?: string;
  variant?: "light" | "dark";
}) {
  const { lang, setLang } = useLanguage();
  const [open, setOpen] = useState(false);
  const wrapper = useRef<HTMLDivElement>(null);
  const active = localeFor(lang);

  // A menu that stays open after you click away reads as broken, and Escape is
  // the keyboard equivalent of clicking away.
  useEffect(() => {
    if (!open) return;
    const onPointerDown = (event: MouseEvent) => {
      if (!wrapper.current?.contains(event.target as Node)) setOpen(false);
    };
    const onKeyDown = (event: KeyboardEvent) => {
      if (event.key === "Escape") setOpen(false);
    };
    document.addEventListener("mousedown", onPointerDown);
    document.addEventListener("keydown", onKeyDown);
    return () => {
      document.removeEventListener("mousedown", onPointerDown);
      document.removeEventListener("keydown", onKeyDown);
    };
  }, [open]);

  const triggerClasses =
    variant === "light"
      ? "border-border text-foreground hover:bg-primary-tint/60"
      : "border-board-foreground/20 text-board-foreground hover:bg-board-foreground/10";

  return (
    <div ref={wrapper} className={`relative inline-flex ${className ?? ""}`}>
      <button
        type="button"
        onClick={() => setOpen((v) => !v)}
        aria-haspopup="listbox"
        aria-expanded={open}
        className={`inline-flex items-center gap-1.5 rounded-full border px-2.5 py-1 text-xs font-semibold uppercase transition-colors ${triggerClasses}`}
      >
        {active.short}
        <svg viewBox="0 0 20 20" fill="none" className="h-3 w-3" aria-hidden="true">
          <path
            d={open ? "M6 12l4-4 4 4" : "M6 8l4 4 4-4"}
            stroke="currentColor"
            strokeWidth="1.8"
            strokeLinecap="round"
            strokeLinejoin="round"
          />
        </svg>
      </button>

      {open && (
        <ul
          role="listbox"
          className="absolute end-0 top-full z-50 mt-1.5 max-h-72 min-w-40 overflow-y-auto rounded-xl border border-border bg-surface py-1 shadow-lg"
        >
          {LOCALES.map((locale) => {
            const selected = locale.code === lang;
            return (
              <li key={locale.code}>
                <button
                  type="button"
                  role="option"
                  aria-selected={selected}
                  dir={locale.dir}
                  onClick={() => {
                    setLang(locale.code);
                    setOpen(false);
                  }}
                  className={`flex w-full items-center justify-between gap-3 px-3 py-1.5 text-start text-sm transition-colors ${
                    selected ? "bg-primary-tint font-semibold text-primary" : "text-foreground hover:bg-primary-tint/60"
                  }`}
                >
                  <span>{locale.label}</span>
                  <span className="font-mono text-[0.65rem] uppercase text-muted">{locale.short}</span>
                </button>
              </li>
            );
          })}
        </ul>
      )}
    </div>
  );
}
