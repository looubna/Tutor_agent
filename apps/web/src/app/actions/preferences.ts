"use server";

import { revalidatePath } from "next/cache";
import { prisma } from "@/lib/prisma";
import { verifySession } from "@/lib/dal";
import { isLang } from "@/lib/locales";

export type SupportLanguageState = { error?: string; saved?: boolean } | undefined;

/**
 * The language the tutor is allowed to drop into when the student is stuck.
 * Stored per student rather than per booking: it is a fact about the learner,
 * not about one class.
 */
export async function updateSupportLanguage(
  _prev: SupportLanguageState,
  formData: FormData,
): Promise<SupportLanguageState> {
  const { userId } = await verifySession();

  const value = formData.get("supportLanguage")?.toString() ?? "";
  if (!isLang(value)) {
    return { error: "Please choose a language from the list." };
  }

  await prisma.user.update({
    where: { id: userId },
    data: { supportLanguage: value },
  });

  revalidatePath("/settings");
  return { saved: true };
}
