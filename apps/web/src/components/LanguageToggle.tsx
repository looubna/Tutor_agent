"use client";

import { useLanguage } from "@/lib/i18n";

export function LanguageToggle({
  className,
  variant = "dark",
}: {
  className?: string;
  variant?: "light" | "dark";
}) {
  const { lang, setLang } = useLanguage();

  const containerClasses =
    variant === "light" ? "border-border text-foreground" : "border-board-foreground/20 text-board-foreground";

  return (
    <div className={`inline-flex overflow-hidden rounded-full border text-xs font-semibold ${containerClasses} ${className ?? ""}`}>
      {(["en", "fr"] as const).map((code) => {
        const active = lang === code;
        const buttonClasses =
          variant === "light"
            ? active
              ? "bg-primary-tint text-primary"
              : "hover:bg-primary-tint/60"
            : active
              ? "bg-board-foreground/20"
              : "hover:bg-board-foreground/10";
        return (
          <button
            key={code}
            type="button"
            onClick={() => setLang(code)}
            aria-pressed={active}
            className={`px-2.5 py-1 uppercase transition-colors ${buttonClasses}`}
          >
            {code}
          </button>
        );
      })}
    </div>
  );
}
