"use client";

import { createContext, useContext, useEffect, useMemo, useState, type ReactNode } from "react";

export type Lang = "en" | "fr";

const STORAGE_KEY = "lang";

const dictionaries: Record<Lang, Record<string, string>> = {
  en: {
    "nav.dashboard": "Lesson overview",
    "nav.calendar": "Calendar",
    "nav.book": "Book a lesson",
    "nav.settings": "Settings",
    "nav.logout": "Log out",

    "dashboard.heading": "Your lessons at a glance",
    "dashboard.emptyMessage": "You don't have any upcoming lessons yet.",
    "dashboard.emptyCta": "Book your first lesson",

    "book.heading": "Book a Math lesson",
    "book.subheading":
      "Your AI Math tutor is available any time — pick a 50-minute slot that works for you.",

    "calendar.heading": "Calendar",
    "calendar.subheading": "All of your Math lessons with your AI tutor.",

    "auth.loginHeading": "Log in to Learnora",
    "auth.loginSubheading": "Continue your Math lessons with your AI tutor.",
    "auth.signupHeading": "Create your account",
    "auth.signupSubheading": "Start learning Math with your AI tutor, free.",
    "auth.nameLabel": "Name",
    "auth.emailLabel": "Email",
    "auth.passwordLabel": "Password",
    "auth.loginSubmit": "Log in",
    "auth.loginSubmitPending": "Logging in…",
    "auth.signupSubmit": "Sign up",
    "auth.signupSubmitPending": "Creating account…",
    "auth.newToBrand": "New to Learnora?",
    "auth.createAccount": "Create an account",
    "auth.alreadyHaveAccount": "Already have an account?",
    "auth.login": "Log in",
    "auth.tagline": "Live math lessons with your AI tutor.",
    "auth.taglineBody":
      "Book a slot, show up, and work through the problem together — no scheduling a human required.",

    "lesson.startLesson": "Start Lesson",
    "lesson.cancel": "Cancel",
    "lesson.cancelling": "Cancelling…",
    "lesson.completed": "Completed",
    "lesson.cancelled": "Cancelled",
    "lesson.number": "Lesson {{n}}",

    "chat.title": "Ask your tutor",
    "chat.placeholder": "Type your question…",
    "chat.send": "Send",
    "chat.sending": "Sending…",
    "chat.error": "Something went wrong. Try again.",
    "chat.emptyHint": "Ask a quick math question anytime.",

    "theme.toggleToDark": "Switch to dark mode",
    "theme.toggleToLight": "Switch to light mode",

    "settings.heading": "Settings",
    "settings.subheading": "Your account and notification preferences.",
    "settings.accountHeading": "Account",
    "settings.googleHeading": "Google Calendar",
    "settings.googleBody":
      "Sync your lessons to Google Calendar so you get reminders there too — booking or cancelling a lesson here keeps it up to date automatically.",
    "settings.googleConnected": "Connected",
    "settings.googleConnect": "Connect Google Calendar",
    "settings.googleDisconnect": "Disconnect",
    "settings.googleNotConfigured": "Google Calendar sync isn't set up yet.",
    "settings.googleConnectedToast": "Google Calendar connected.",
    "settings.googleErrorToast": "Couldn't connect Google Calendar. Please try again.",
    "settings.emailReminderNote": "You'll also get an email 1 hour before each lesson.",
  },
  fr: {
    "nav.dashboard": "Aperçu des cours",
    "nav.calendar": "Calendrier",
    "nav.book": "Réserver un cours",
    "nav.settings": "Paramètres",
    "nav.logout": "Déconnexion",

    "dashboard.heading": "Vos cours en un coup d'œil",
    "dashboard.emptyMessage": "Vous n'avez pas encore de cours à venir.",
    "dashboard.emptyCta": "Réservez votre premier cours",

    "book.heading": "Réserver un cours de maths",
    "book.subheading":
      "Votre tuteur IA de maths est disponible à tout moment — choisissez un créneau de 50 minutes qui vous convient.",

    "calendar.heading": "Calendrier",
    "calendar.subheading": "Tous vos cours de maths avec votre tuteur IA.",

    "auth.loginHeading": "Connexion à Learnora",
    "auth.loginSubheading": "Continuez vos cours de maths avec votre tuteur IA.",
    "auth.signupHeading": "Créez votre compte",
    "auth.signupSubheading": "Commencez à apprendre les maths avec votre tuteur IA, gratuitement.",
    "auth.nameLabel": "Nom",
    "auth.emailLabel": "E-mail",
    "auth.passwordLabel": "Mot de passe",
    "auth.loginSubmit": "Se connecter",
    "auth.loginSubmitPending": "Connexion…",
    "auth.signupSubmit": "S'inscrire",
    "auth.signupSubmitPending": "Création du compte…",
    "auth.newToBrand": "Nouveau sur Learnora ?",
    "auth.createAccount": "Créer un compte",
    "auth.alreadyHaveAccount": "Vous avez déjà un compte ?",
    "auth.login": "Se connecter",
    "auth.tagline": "Cours de maths en direct avec votre tuteur IA.",
    "auth.taglineBody":
      "Réservez un créneau, connectez-vous, et travaillez le problème ensemble — sans avoir à planifier avec un humain.",

    "lesson.startLesson": "Démarrer le cours",
    "lesson.cancel": "Annuler",
    "lesson.cancelling": "Annulation…",
    "lesson.completed": "Terminé",
    "lesson.cancelled": "Annulé",
    "lesson.number": "Cours {{n}}",

    "chat.title": "Demandez à votre tuteur",
    "chat.placeholder": "Tapez votre question…",
    "chat.send": "Envoyer",
    "chat.sending": "Envoi…",
    "chat.error": "Une erreur est survenue. Réessayez.",
    "chat.emptyHint": "Posez une question rapide de maths à tout moment.",

    "theme.toggleToDark": "Passer en mode sombre",
    "theme.toggleToLight": "Passer en mode clair",

    "settings.heading": "Paramètres",
    "settings.subheading": "Votre compte et vos préférences de notification.",
    "settings.accountHeading": "Compte",
    "settings.googleHeading": "Google Agenda",
    "settings.googleBody":
      "Synchronisez vos cours avec Google Agenda pour recevoir aussi des rappels là-bas — réserver ou annuler un cours ici le met à jour automatiquement.",
    "settings.googleConnected": "Connecté",
    "settings.googleConnect": "Connecter Google Agenda",
    "settings.googleDisconnect": "Déconnecter",
    "settings.googleNotConfigured": "La synchronisation Google Agenda n'est pas encore configurée.",
    "settings.googleConnectedToast": "Google Agenda connecté.",
    "settings.googleErrorToast": "Impossible de connecter Google Agenda. Veuillez réessayer.",
    "settings.emailReminderNote": "Vous recevrez aussi un e-mail 1 heure avant chaque cours.",
  },
};

type LanguageContextValue = {
  lang: Lang;
  setLang: (lang: Lang) => void;
};

const LanguageContext = createContext<LanguageContextValue | null>(null);

export function LanguageProvider({ children }: { children: ReactNode }) {
  const [lang, setLangState] = useState<Lang>("en");

  useEffect(() => {
    // Reads the persisted choice once after mount, matching SSR's "en"
    // default on first paint to avoid a hydration mismatch.
    try {
      const stored = window.localStorage.getItem(STORAGE_KEY);
      // eslint-disable-next-line react-hooks/set-state-in-effect
      if (stored === "en" || stored === "fr") setLangState(stored);
    } catch {
      // localStorage unavailable — stay on default "en"
    }
  }, []);

  const setLang = (next: Lang) => {
    setLangState(next);
    try {
      window.localStorage.setItem(STORAGE_KEY, next);
    } catch {
      // ignore write failures (private browsing, etc.)
    }
  };

  const value = useMemo(() => ({ lang, setLang }), [lang]);

  return <LanguageContext.Provider value={value}>{children}</LanguageContext.Provider>;
}

function translate(lang: Lang, key: string, vars?: Record<string, string | number>) {
  const dict = dictionaries[lang] ?? dictionaries.en;
  let str = dict[key] ?? dictionaries.en[key] ?? key;
  if (vars) {
    for (const [name, value] of Object.entries(vars)) {
      str = str.replaceAll(`{{${name}}}`, String(value));
    }
  }
  return str;
}

export function useT() {
  const ctx = useContext(LanguageContext);
  const lang = ctx?.lang ?? "en";
  return (key: string, vars?: Record<string, string | number>) => translate(lang, key, vars);
}

export function useLanguage() {
  const ctx = useContext(LanguageContext);
  if (!ctx) throw new Error("useLanguage must be used within a LanguageProvider");
  return ctx;
}
