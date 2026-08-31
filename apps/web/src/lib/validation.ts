import * as z from "zod";

import { LOCALES } from "@/lib/locales";

const LANG_CODES = LOCALES.map((l) => l.code) as [string, ...string[]];

export const SignupFormSchema = z.object({
  name: z.string().min(2, "Name must be at least 2 characters long.").trim(),
  email: z.email("Please enter a valid email.").trim(),
  password: z
    .string()
    .min(8, "Be at least 8 characters long.")
    .regex(/[a-zA-Z]/, "Contain at least one letter.")
    .regex(/[0-9]/, "Contain at least one number."),
  /**
   * The language the tutor may explain in when the learner is stuck. Asked here
   * because someone who starts a class straight from the course page never
   * passes through the booking form.
   */
  supportLanguage: z.enum(LANG_CODES, { message: "Please choose a language." }),
});

export const LoginFormSchema = z.object({
  email: z.email("Please enter a valid email."),
  password: z.string().min(1, "Password is required."),
});

export type SignupFormState =
  | {
      errors?: {
        name?: string[];
        email?: string[];
        password?: string[];
        supportLanguage?: string[];
      };
      message?: string;
    }
  | undefined;

export type LoginFormState =
  | {
      errors?: {
        email?: string[];
        password?: string[];
      };
      message?: string;
    }
  | undefined;
