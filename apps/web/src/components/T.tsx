"use client";

import { createElement, type ElementType } from "react";
import { useT } from "@/lib/i18n";

/**
 * Renders one translated string. Lets Server Component pages (dashboard,
 * book, calendar) drop translated text inline without becoming client
 * components themselves.
 */
export function T({
  k,
  as: as_,
  className,
}: {
  k: string;
  as?: ElementType;
  className?: string;
}) {
  const t = useT();
  return createElement(as_ ?? "span", { className }, t(k));
}
