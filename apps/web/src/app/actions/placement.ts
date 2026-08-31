"use server";

import { Resend } from "resend";
import { z } from "zod";
import { PLACEMENT_QUESTIONS, levelForScore, type Cefr } from "@/lib/placement/questions";
import { placementCopy } from "@/lib/placement/copy";
import type { Lang } from "@/lib/i18n";

const APP_URL = process.env.NEXT_PUBLIC_APP_URL ?? "http://localhost:3000";

const schema = z.object({
  subjectId: z.string().refine((id) => id in PLACEMENT_QUESTIONS, "Unknown language"),
  subjectName: z.string().min(1).max(60),
  score: z.number().int().min(0).max(12),
  firstName: z.string().max(60).optional(),
  email: z.email(),
  lang: z.enum(["en", "fr"]),
});

export type EmailResultState = { ok: boolean; message?: string };

/**
 * Emails a copy of the placement result. The result itself is always shown on
 * screen, so a missing API key or a send failure costs the learner nothing.
 */
export async function emailPlacementResult(input: unknown): Promise<EmailResultState> {
  const parsed = schema.safeParse(input);
  if (!parsed.success) return { ok: false, message: "invalid" };

  const { subjectName, score, firstName, email, lang } = parsed.data;
  const apiKey = process.env.RESEND_API_KEY;
  if (!apiKey) {
    console.warn("[placement] RESEND_API_KEY is not set — result emails are disabled.");
    return { ok: false, message: "disabled" };
  }

  const level: Cefr = levelForScore(score);
  const copy = placementCopy(lang as Lang);
  const { name, blurb } = copy.levels[level];
  const greeting = firstName ? `Hi ${firstName},` : "Hi,";

  try {
    await new Resend(apiKey).emails.send({
      from: process.env.RESEND_FROM_EMAIL ?? "Zanoba <onboarding@resend.dev>",
      to: email,
      subject: `Your ${subjectName} level: ${level}`,
      html: `
        <p>${greeting}</p>
        <p>You scored <strong>${score} out of 12</strong> on the ${subjectName} placement test,
        which puts you at <strong>${level} — ${name}</strong>.</p>
        <p>${blurb}</p>
        <p><a href="${APP_URL}/signup">Book a free ${subjectName} lesson at ${level}</a></p>
        <p>— Zanoba</p>
      `,
    });
    return { ok: true };
  } catch (err) {
    console.error("[placement] failed to send result email", err);
    return { ok: false, message: "send-failed" };
  }
}
