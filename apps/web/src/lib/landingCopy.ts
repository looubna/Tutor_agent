import type { Lang } from "@/lib/i18n";

/**
 * Copy for the marketing landing page. It lives outside the shared `i18n`
 * dictionary because it is structural — steps, plans and questions come in
 * ordered lists — and flattening that into dotted keys would make it harder
 * to keep the two languages in step.
 */
export type LandingCopy = {
  heroMock: {
    badge: string;
    badgeLabel: string;
    headline1: string;
    headline2: string;
    body: string;
    pills: string[];
    selectLabel: string;
    cta: string;
    trial: string;
    cancel: string;
    tutorCardTitle: string;
    tutorName: string;
    tutorStatus: string;
    tutorTraits: string[];
    features: { title: string; body: string }[];
  };
  nav: { subjects: string; how: string; pricing: string; login: string; start: string; menu: string };
  hero: {
    eyebrow: string;
    headline: string;
    body: string;
    pickLabel: string;
    languages: string;
    sciences: string;
    cta: string;
    ctaNote: string;
    boardLabel: string;
    live: string;
    tutorLine: string;
    levelsHeading: string;
    levelsBody: string;
    levelsCta: string;
  };
  showcase: {
    heading: string;
    body: string;
    expand: string;
    collapse: string;
    cards: { line1: string; line2: string; body: string }[];
  };
  facts: { value: string; label: string }[];
  benefits: { heading: string; items: { title: string; body: string }[] };
  subjects: { heading: string; body: string; languages: string; sciences: string; cta: string };
  how: { heading: string; steps: { title: string; body: string }[] };
  pricing: {
    heading: string;
    body: string;
    badge: string;
    plans: { name: string; price: string; cadence: string; body: string; features: string[]; cta: string }[];
    note: string;
  };
  testimonials: { heading: string; items: { quote: string; name: string; detail: string }[] };
  faq: { heading: string; items: { q: string; a: string }[] };
  footer: {
    tagline: string;
    columns: { heading: string; links: { label: string; href?: string }[] }[];
    legal: string;
  };
};

const en: LandingCopy = {
  heroMock: {
    badge: "Live",
    badgeLabel: "AI Tutor Class",
    headline1: "AI Tutor. Real Teaching.",
    headline2: "Real Progress.",
    body: "One-to-one AI tutor sessions with live conversation, an interactive whiteboard, and personalized learning built around you.",
    pills: ["Speak naturally", "AI writes & explains", "Personalized lessons", "Adapts to you"],
    selectLabel: "Lesson language",
    cta: "Start your first class",
    trial: "7-day free trial",
    cancel: "Cancel anytime",
    tutorCardTitle: "Your AI Tutor",
    tutorName: "Luna",
    tutorStatus: "Online & ready to teach",
    tutorTraits: [
      "Patient and encouraging",
      "Explains in multiple ways",
      "Adapts to your pace",
      "Here to help you succeed",
    ],
    features: [
      { title: "Curriculum-based", body: "Structured lessons that build real skills" },
      { title: "Live AI tutor", body: "Natural voice conversations" },
      { title: "Smart adaptation", body: "Learns your level and improves with you" },
      { title: "Safe and focused", body: "Designed for effective, distraction-free learning" },
    ],
  },
  nav: {
    subjects: "Subjects",
    how: "How it works",
    pricing: "Pricing",
    login: "Log in",
    start: "Start free",
    menu: "Jump to a section",
  },
  hero: {
    eyebrow: "Live 1-on-1 lessons · languages and sciences",
    headline: "A tutor for every subject, free at every hour.",
    body: "Live 50-minute video lessons in eight languages and six sciences. Pick a subject, pick a slot, and work through it together — at 6am or at midnight.",
    pickLabel: "What do you want to learn?",
    languages: "Languages",
    sciences: "Scientific subjects",
    cta: "Book a free lesson",
    ctaNote: "Your first lesson is free. No card needed.",
    boardLabel: "On the board",
    live: "Live",
    tutorLine: "Zanoba tutor",
    levelsHeading: "About the levels",
    levelsBody:
      "Every language runs the CEFR ladder from A1 to C1. Not sure where you sit?",
    levelsCta: "Take the placement test",
  },
  showcase: {
    heading: "Inside a Zanoba lesson",
    body: "Not a chat window. A tutor who shows up on camera, talks you through it, and writes on the board with you.",
    expand: "Read more",
    collapse: "Close",
    cards: [
      {
        line1: "A tutor with a face.",
        line2: "One to one, on live video.",
        body: "Your tutor joins on camera and speaks — it looks at you, waits while you think, and picks up when you trail off mid-sentence. Fifty minutes, just the two of you.",
      },
      {
        line1: "A shared board.",
        line2: "You both write on it.",
        body: "Sketch the triangle, show your working, paste a photo of the exercise. Your tutor works on the same board and corrects the step, not just the answer.",
      },
      {
        line1: "Between the lessons.",
        line2: "Ask anything, any hour.",
        body: "Stuck on question 7 at midnight? Send it. The same tutor answers in chat, with the context of everything you have covered together.",
      },
      {
        line1: "A curriculum per subject.",
        line2: "It knows what comes next.",
        body: "Languages follow the CEFR ladder; sciences follow the syllabus. Each lesson opens where the last one closed.",
      },
    ],
  },
  facts: [
    { value: "24/7", label: "Slots open, every day of the year" },
    { value: "14", label: "Subjects, from Korean to Bayes' rule" },
    { value: "50 min", label: "Every lesson, one to one on video" },
  ],
  benefits: {
    heading: "What a tutor that never tires can do",
    items: [
      {
        title: "It waits for your question",
        body: "Ask the same thing three times. Your tutor never sighs, never checks the clock, and never moves on before you say you're ready.",
      },
      {
        title: "It teaches, not just answers",
        body: "Every lesson runs on a plan: the concept, then a worked example, then problems you drive. You leave with the method, not the answer key.",
      },
      {
        title: "It remembers last week",
        body: "Your tutor opens where the last lesson stopped — including the exact step that tripped you up — so nothing has to be explained twice.",
      },
    ],
  },
  subjects: {
    heading: "Fourteen subjects, one tutor",
    body: "Book any of them in the same calendar, switch between them week to week, and keep one record of everything you've covered.",
    languages: "Languages",
    sciences: "Scientific subjects",
    cta: "Book a lesson",
  },
  how: {
    heading: "How a lesson works",
    steps: [
      {
        title: "Pick a subject and a slot",
        body: "Fourteen subjects, 50-minute lessons starting on the hour and the half hour. Book three weeks out or twenty minutes from now.",
      },
      {
        title: "Show up on video",
        body: "Your tutor is already at the board. Bring your homework, a photo of a problem, or just the thing you didn't follow in class.",
      },
      {
        title: "Keep the board",
        body: "Every lesson saves its board and transcript to your calendar, so revising is just re-reading what the two of you wrote.",
      },
    ],
  },
  pricing: {
    heading: "Pay for lessons, not for a membership",
    body: "Start free, then choose the shape that fits how you study.",
    badge: "Most popular",
    plans: [
      {
        name: "Per lesson",
        price: "€12",
        cadence: "per lesson",
        body: "Book one at a time, in any subject.",
        features: ["No subscription", "Credits never expire", "Cancel up to 1 hour before"],
        cta: "Start free",
      },
      {
        name: "Monthly",
        price: "€39",
        cadence: "per month",
        body: "For a subject you're working through week by week.",
        features: [
          "12 lessons a month, any subjects",
          "Unlimited chat between lessons",
          "Google Calendar sync and reminders",
        ],
        cta: "Start free",
      },
    ],
    note: "Both plans start with one free lesson. Cancel any time from Settings.",
  },
  testimonials: {
    heading: "What learners say",
    items: [
      {
        quote: "I book integrals at 11pm because that's when I actually do my problem sets. It has never once been unavailable.",
        name: "Amine",
        detail: "Mathematics · first-year engineering",
      },
      {
        quote: "I stopped being embarrassed about asking. It just explains the subjunctive again, differently, until it lands.",
        name: "Klara",
        detail: "Spanish · B1",
      },
      {
        quote: "The board from each lesson is the only revision material I use now. It's my own handwriting, basically.",
        name: "Tomás",
        detail: "Chemistry · final year",
      },
    ],
  },
  faq: {
    heading: "Questions, answered",
    items: [
      {
        q: "Is the tutor a person?",
        a: "No. Your tutor is an AI that joins you on live video, speaks, listens, and writes on a shared board. That's why it's available at any hour and never has to be booked weeks ahead.",
      },
      {
        q: "What happens in the free lesson?",
        a: "A full 50 minutes, in the subject you choose, with nothing held back. No card is needed to book it.",
      },
      {
        q: "Which subjects can I take?",
        a: "Eight languages — English, French, Spanish, German, Italian, Arabic, Chinese and Korean, each from A1 to C1 — and six sciences: mathematics, physics, chemistry, biology, computer science and statistics.",
      },
      {
        q: "Can I switch subjects?",
        a: "Every lesson is booked on its own, so you can take Spanish on Monday and physics on Thursday. Your progress is kept per subject.",
      },
      {
        q: "What do I need to join a lesson?",
        a: "A browser, a microphone and a camera. Nothing to install. A phone camera pointed at your homework works well too.",
      },
      {
        q: "Can I cancel a lesson?",
        a: "Up to an hour before it starts, from your calendar. The credit goes straight back to your account.",
      },
    ],
  },
  footer: {
    tagline: "Live lessons in languages and sciences, with a tutor that's on when you are.",
    columns: [
      {
        heading: "Subjects",
        links: [
          { label: "Languages", href: "#subjects" },
          { label: "Sciences", href: "#subjects" },
          { label: "Book a lesson", href: "/signup" },
        ],
      },
      {
        heading: "Zanoba",
        links: [
          { label: "How it works", href: "#how" },
          { label: "Pricing", href: "#pricing" },
          { label: "Log in", href: "/login" },
        ],
      },
      { heading: "Support", links: [{ label: "Help centre" }, { label: "Contact" }, { label: "Status" }] },
    ],
    legal: "Zanoba — an AI tutor for languages and sciences.",
  },
};

const fr: LandingCopy = {
  heroMock: {
    badge: "En direct",
    badgeLabel: "Cours avec tuteur IA",
    headline1: "Tuteur IA. Vrais cours.",
    headline2: "Vrais progrès.",
    body: "Des cours particuliers avec un tuteur IA : conversation en direct, tableau blanc interactif, et un apprentissage construit autour de vous.",
    pills: ["Parlez naturellement", "L'IA écrit et explique", "Cours personnalisés", "S'adapte à vous"],
    selectLabel: "Langue du cours",
    cta: "Commencer votre premier cours",
    trial: "7 jours d'essai gratuit",
    cancel: "Annulable à tout moment",
    tutorCardTitle: "Votre tuteur IA",
    tutorName: "Luna",
    tutorStatus: "En ligne, prête à enseigner",
    tutorTraits: [
      "Patiente et encourageante",
      "Explique de plusieurs façons",
      "S'adapte à votre rythme",
      "Là pour vous faire réussir",
    ],
    features: [
      { title: "Basé sur un programme", body: "Des cours structurés qui construisent de vraies compétences" },
      { title: "Tuteur IA en direct", body: "Des conversations vocales naturelles" },
      { title: "Adaptation intelligente", body: "Apprend votre niveau et progresse avec vous" },
      { title: "Sûr et concentré", body: "Conçu pour un apprentissage efficace, sans distraction" },
    ],
  },
  nav: {
    subjects: "Matières",
    how: "Comment ça marche",
    pricing: "Tarifs",
    login: "Se connecter",
    start: "Commencer gratuitement",
    menu: "Aller à une section",
  },
  hero: {
    eyebrow: "Cours particuliers en direct · langues et sciences",
    headline: "Un tuteur pour chaque matière, libre à toute heure.",
    body: "Des cours vidéo de 50 minutes en huit langues et six sciences. Choisissez une matière, choisissez un créneau, et travaillez ensemble — à 6h du matin comme à minuit.",
    pickLabel: "Que voulez-vous apprendre ?",
    languages: "Langues",
    sciences: "Matières scientifiques",
    cta: "Réserver un cours gratuit",
    ctaNote: "Le premier cours est gratuit. Sans carte bancaire.",
    boardLabel: "Au tableau",
    live: "En direct",
    tutorLine: "Tuteur Zanoba",
    levelsHeading: "À propos des niveaux",
    levelsBody:
      "Chaque langue se suit de A1 à C1 sur l'échelle du CECRL. Vous ne savez pas où vous en êtes ?",
    levelsCta: "Passer le test de niveau",
  },
  showcase: {
    heading: "À quoi ressemble un cours Zanoba",
    body: "Pas une fenêtre de chat. Un tuteur qui apparaît à la caméra, vous explique, et écrit au tableau avec vous.",
    expand: "En savoir plus",
    collapse: "Fermer",
    cards: [
      {
        line1: "Un tuteur avec un visage.",
        line2: "En tête-à-tête, en vidéo.",
        body: "Votre tuteur apparaît à la caméra et parle — il vous regarde, attend pendant que vous réfléchissez, et reprend quand vous vous arrêtez au milieu d'une phrase. Cinquante minutes, rien qu'à deux.",
      },
      {
        line1: "Un tableau partagé.",
        line2: "Vous y écrivez tous les deux.",
        body: "Tracez le triangle, montrez votre raisonnement, collez la photo de l'exercice. Votre tuteur travaille sur le même tableau et corrige l'étape, pas seulement le résultat.",
      },
      {
        line1: "Entre les cours.",
        line2: "Posez vos questions, à toute heure.",
        body: "Bloqué sur la question 7 à minuit ? Envoyez-la. Le même tuteur répond par message, avec en tête tout ce que vous avez travaillé ensemble.",
      },
      {
        line1: "Un programme par matière.",
        line2: "Il sait ce qui vient ensuite.",
        body: "Les langues suivent l'échelle du CECRL, les sciences suivent le programme. Chaque cours reprend là où le précédent s'est arrêté.",
      },
    ],
  },
  facts: [
    { value: "24/7", label: "Des créneaux ouverts, tous les jours de l'année" },
    { value: "14", label: "Matières, du coréen au théorème de Bayes" },
    { value: "50 min", label: "Chaque cours, en tête-à-tête en vidéo" },
  ],
  benefits: {
    heading: "Ce que peut faire un tuteur infatigable",
    items: [
      {
        title: "Il attend votre question",
        body: "Posez-la trois fois. Votre tuteur ne soupire pas, ne regarde pas l'heure, et n'avance pas tant que vous ne le dites pas.",
      },
      {
        title: "Il enseigne, il ne donne pas la réponse",
        body: "Chaque cours suit un plan : la notion, puis un exemple traité, puis des exercices que vous menez. Vous repartez avec la méthode, pas le corrigé.",
      },
      {
        title: "Il se souvient de la semaine dernière",
        body: "Votre tuteur reprend là où le dernier cours s'est arrêté — y compris à l'étape qui vous a bloqué — pour ne rien réexpliquer deux fois.",
      },
    ],
  },
  subjects: {
    heading: "Quatorze matières, un seul tuteur",
    body: "Réservez-les dans le même calendrier, alternez d'une semaine à l'autre, et gardez une seule trace de tout ce que vous avez vu.",
    languages: "Langues",
    sciences: "Matières scientifiques",
    cta: "Réserver un cours",
  },
  how: {
    heading: "Comment se déroule un cours",
    steps: [
      {
        title: "Choisissez une matière et un créneau",
        body: "Quatorze matières, des cours de 50 minutes qui commencent à l'heure et à la demi-heure. Réservez trois semaines à l'avance ou dans vingt minutes.",
      },
      {
        title: "Connectez-vous en vidéo",
        body: "Votre tuteur est déjà au tableau. Apportez vos devoirs, la photo d'un exercice, ou simplement ce que vous n'avez pas suivi en cours.",
      },
      {
        title: "Gardez le tableau",
        body: "Chaque cours enregistre son tableau et sa transcription dans votre calendrier : réviser, c'est relire ce que vous avez écrit à deux.",
      },
    ],
  },
  pricing: {
    heading: "Payez des cours, pas un abonnement",
    body: "Commencez gratuitement, puis choisissez la formule qui correspond à votre façon de travailler.",
    badge: "Le plus choisi",
    plans: [
      {
        name: "À l'unité",
        price: "12 €",
        cadence: "par cours",
        body: "Réservez un cours à la fois, dans la matière de votre choix.",
        features: ["Sans abonnement", "Crédits sans date d'expiration", "Annulation jusqu'à 1 h avant"],
        cta: "Commencer gratuitement",
      },
      {
        name: "Mensuel",
        price: "39 €",
        cadence: "par mois",
        body: "Pour une matière que vous travaillez semaine après semaine.",
        features: [
          "12 cours par mois, toutes matières",
          "Messagerie illimitée entre les cours",
          "Synchronisation Google Agenda et rappels",
        ],
        cta: "Commencer gratuitement",
      },
    ],
    note: "Les deux formules commencent par un cours gratuit. Résiliable à tout moment depuis les Paramètres.",
  },
  testimonials: {
    heading: "Ce qu'en disent les élèves",
    items: [
      {
        quote: "Je réserve mes intégrales à 23h, parce que c'est là que je fais vraiment mes exercices. Ça n'a jamais été indisponible.",
        name: "Amine",
        detail: "Mathématiques · première année d'ingénierie",
      },
      {
        quote: "J'ai arrêté d'avoir honte de demander. Il réexplique le subjonctif, autrement, jusqu'à ce que ça rentre.",
        name: "Klara",
        detail: "Espagnol · B1",
      },
      {
        quote: "Le tableau de chaque cours est devenu ma seule fiche de révision. C'est presque mon écriture.",
        name: "Tomás",
        detail: "Chimie · dernière année",
      },
    ],
  },
  faq: {
    heading: "Vos questions",
    items: [
      {
        q: "Le tuteur est-il une personne ?",
        a: "Non. Votre tuteur est une IA qui vous rejoint en vidéo : elle parle, elle écoute, et elle écrit sur un tableau partagé. C'est pour cela qu'elle est disponible à toute heure, sans réserver des semaines à l'avance.",
      },
      {
        q: "Que contient le cours gratuit ?",
        a: "50 minutes complètes, dans la matière de votre choix, sans rien retenir. Aucune carte bancaire n'est demandée.",
      },
      {
        q: "Quelles matières puis-je suivre ?",
        a: "Huit langues — anglais, français, espagnol, allemand, italien, arabe, chinois et coréen, chacune de A1 à C1 — et six sciences : mathématiques, physique, chimie, biologie, informatique et statistiques.",
      },
      {
        q: "Puis-je changer de matière ?",
        a: "Chaque cours se réserve séparément : espagnol le lundi, physique le jeudi. Votre progression est suivie matière par matière.",
      },
      {
        q: "De quoi ai-je besoin pour suivre un cours ?",
        a: "D'un navigateur, d'un micro et d'une caméra. Rien à installer. Un téléphone braqué sur vos devoirs fonctionne très bien aussi.",
      },
      {
        q: "Puis-je annuler un cours ?",
        a: "Jusqu'à une heure avant le début, depuis votre calendrier. Le crédit revient aussitôt sur votre compte.",
      },
    ],
  },
  footer: {
    tagline: "Des cours en direct en langues et en sciences, avec un tuteur disponible quand vous l'êtes.",
    columns: [
      {
        heading: "Matières",
        links: [
          { label: "Langues", href: "#subjects" },
          { label: "Sciences", href: "#subjects" },
          { label: "Réserver un cours", href: "/signup" },
        ],
      },
      {
        heading: "Zanoba",
        links: [
          { label: "Comment ça marche", href: "#how" },
          { label: "Tarifs", href: "#pricing" },
          { label: "Se connecter", href: "/login" },
        ],
      },
      { heading: "Aide", links: [{ label: "Centre d'aide" }, { label: "Contact" }, { label: "État du service" }] },
    ],
    legal: "Zanoba — un tuteur IA pour les langues et les sciences.",
  },
};

const es: LandingCopy = {
  heroMock: {
    badge: "En directo",
    badgeLabel: "Clase con tutor de IA",
    headline1: "Tutor de IA. Enseñanza de verdad.",
    headline2: "Progreso de verdad.",
    body: "Clases individuales con un tutor de IA: conversación en directo, pizarra interactiva y un aprendizaje construido a tu medida.",
    pills: ["Habla con naturalidad", "La IA escribe y explica", "Clases personalizadas", "Se adapta a ti"],
    selectLabel: "Idioma de la clase",
    cta: "Empieza tu primera clase",
    trial: "7 días de prueba gratis",
    cancel: "Cancela cuando quieras",
    tutorCardTitle: "Tu tutor de IA",
    tutorName: "Luna",
    tutorStatus: "En línea y lista para enseñar",
    tutorTraits: [
      "Paciente y motivadora",
      "Explica de varias maneras",
      "Se adapta a tu ritmo",
      "Está aquí para que lo consigas",
    ],
    features: [
      { title: "Basado en un programa", body: "Clases estructuradas que construyen destrezas reales" },
      { title: "Tutor de IA en directo", body: "Conversaciones de voz naturales" },
      { title: "Adaptación inteligente", body: "Aprende tu nivel y mejora contigo" },
      { title: "Seguro y centrado", body: "Diseñado para aprender sin distracciones" },
    ],
  },
  nav: {
    subjects: "Materias",
    how: "Cómo funciona",
    pricing: "Precios",
    login: "Iniciar sesión",
    start: "Empieza gratis",
    menu: "Ir a una sección",
  },
  hero: {
    eyebrow: "Clases individuales en directo · idiomas y ciencias",
    headline: "Un tutor para cada materia, libre a cualquier hora.",
    body: "Clases de vídeo de 50 minutos en ocho idiomas y seis ciencias. Elige una materia, elige un horario y trabajadlo juntos — a las 6 de la mañana o a medianoche.",
    pickLabel: "¿Qué quieres aprender?",
    languages: "Idiomas",
    sciences: "Materias científicas",
    cta: "Reserva una clase gratis",
    ctaNote: "Tu primera clase es gratis. Sin tarjeta.",
    boardLabel: "En la pizarra",
    live: "En directo",
    tutorLine: "Tutor de Zanoba",
    levelsHeading: "Sobre los niveles",
    levelsBody: "Cada idioma recorre la escala del MCER de A1 a C1. ¿No sabes dónde estás?",
    levelsCta: "Haz la prueba de nivel",
  },
  showcase: {
    heading: "Dentro de una clase de Zanoba",
    body: "No es una ventana de chat. Es un tutor que aparece en cámara, te lo explica y escribe contigo en la pizarra.",
    expand: "Leer más",
    collapse: "Cerrar",
    cards: [
      {
        line1: "Un tutor con cara.",
        line2: "Uno a uno, en vídeo en directo.",
        body: "Tu tutor entra en cámara y habla: te mira, espera mientras piensas y retoma cuando se te apaga la frase. Cincuenta minutos, solo vosotros dos.",
      },
      {
        line1: "Una pizarra compartida.",
        line2: "Los dos escribís en ella.",
        body: "Dibuja el triángulo, enseña tus cálculos, pega una foto del ejercicio. Tu tutor trabaja en la misma pizarra y corrige el paso, no solo el resultado.",
      },
      {
        line1: "Entre clase y clase.",
        line2: "Pregunta lo que sea, a cualquier hora.",
        body: "¿Atascado en el ejercicio 7 a medianoche? Envíalo. El mismo tutor responde en el chat, con el contexto de todo lo que habéis visto juntos.",
      },
      {
        line1: "Un programa por materia.",
        line2: "Sabe qué viene después.",
        body: "Los idiomas siguen la escala del MCER; las ciencias siguen el temario. Cada clase empieza donde terminó la anterior.",
      },
    ],
  },
  facts: [
    { value: "24/7", label: "Horarios abiertos, todos los días del año" },
    { value: "14", label: "Materias, del coreano al teorema de Bayes" },
    { value: "50 min", label: "Cada clase, uno a uno en vídeo" },
  ],
  benefits: {
    heading: "Lo que puede hacer un tutor que nunca se cansa",
    items: [
      {
        title: "Espera tu pregunta",
        body: "Pregunta lo mismo tres veces. Tu tutor nunca suspira, nunca mira el reloj y nunca sigue adelante antes de que digas que estás listo.",
      },
      {
        title: "Enseña, no solo responde",
        body: "Cada clase sigue un plan: el concepto, luego un ejemplo resuelto, luego problemas que llevas tú. Te vas con el método, no con el solucionario.",
      },
      {
        title: "Se acuerda de la semana pasada",
        body: "Tu tutor abre donde se quedó la última clase — incluido el paso exacto que se te atragantó — para no explicar nada dos veces.",
      },
    ],
  },
  subjects: {
    heading: "Catorce materias, un solo tutor",
    body: "Resérvalas todas en el mismo calendario, cambia de una a otra cada semana y mantén un único registro de todo lo que has visto.",
    languages: "Idiomas",
    sciences: "Materias científicas",
    cta: "Reservar una clase",
  },
  how: {
    heading: "Cómo es una clase",
    steps: [
      {
        title: "Elige materia y horario",
        body: "Catorce materias y clases de 50 minutos que empiezan en punto y y media. Reserva con tres semanas o para dentro de veinte minutos.",
      },
      {
        title: "Conéctate por vídeo",
        body: "Tu tutor ya está en la pizarra. Trae los deberes, una foto de un problema o simplemente eso que no entendiste en clase.",
      },
      {
        title: "Quédate con la pizarra",
        body: "Cada clase guarda su pizarra y su transcripción en tu calendario, así que repasar es releer lo que escribisteis los dos.",
      },
    ],
  },
  pricing: {
    heading: "Paga por clases, no por una suscripción",
    body: "Empieza gratis y luego elige el formato que encaje con tu forma de estudiar.",
    badge: "El más elegido",
    plans: [
      {
        name: "Por clase",
        price: "12 €",
        cadence: "por clase",
        body: "Reserva de una en una, en cualquier materia.",
        features: ["Sin suscripción", "Los créditos no caducan", "Cancela hasta 1 hora antes"],
        cta: "Empieza gratis",
      },
      {
        name: "Mensual",
        price: "39 €",
        cadence: "al mes",
        body: "Para una materia que trabajas semana a semana.",
        features: [
          "12 clases al mes, en las materias que quieras",
          "Chat ilimitado entre clases",
          "Sincronización y recordatorios con Google Calendar",
        ],
        cta: "Empieza gratis",
      },
    ],
    note: "Los dos planes empiezan con una clase gratis. Cancela cuando quieras desde Ajustes.",
  },
  testimonials: {
    heading: "Lo que dicen los estudiantes",
    items: [
      {
        quote: "Reservo integrales a las 11 de la noche porque es cuando de verdad hago los problemas. Nunca ha estado ocupado.",
        name: "Amine",
        detail: "Matemáticas · primero de ingeniería",
      },
      {
        quote: "Dejé de avergonzarme por preguntar. Simplemente vuelve a explicar el subjuntivo, de otra manera, hasta que encaja.",
        name: "Klara",
        detail: "Español · B1",
      },
      {
        quote: "La pizarra de cada clase es el único material de repaso que uso. Es prácticamente mi propia letra.",
        name: "Tomás",
        detail: "Química · último curso",
      },
    ],
  },
  faq: {
    heading: "Preguntas, respondidas",
    items: [
      {
        q: "¿El tutor es una persona?",
        a: "No. Tu tutor es una IA que se conecta contigo por vídeo en directo, habla, escucha y escribe en una pizarra compartida. Por eso está disponible a cualquier hora y no hay que reservarlo con semanas de antelación.",
      },
      {
        q: "¿Qué pasa en la clase gratuita?",
        a: "50 minutos completos, en la materia que elijas, sin recortes. No hace falta tarjeta para reservarla.",
      },
      {
        q: "¿Qué materias puedo dar?",
        a: "Ocho idiomas — inglés, francés, español, alemán, italiano, árabe, chino y coreano, cada uno de A1 a C1 — y seis ciencias: matemáticas, física, química, biología, informática y estadística.",
      },
      {
        q: "¿Puedo cambiar de materia?",
        a: "Cada clase se reserva por separado, así que puedes dar español el lunes y física el jueves. Tu progreso se guarda por materia.",
      },
      {
        q: "¿Qué necesito para entrar a una clase?",
        a: "Un navegador, un micrófono y una cámara. Nada que instalar. La cámara del móvil apuntando a los deberes también funciona muy bien.",
      },
      {
        q: "¿Puedo cancelar una clase?",
        a: "Hasta una hora antes de que empiece, desde tu calendario. El crédito vuelve directamente a tu cuenta.",
      },
    ],
  },
  footer: {
    tagline: "Clases en directo de idiomas y ciencias, con un tutor que está cuando tú estás.",
    columns: [
      {
        heading: "Materias",
        links: [
          { label: "Idiomas", href: "#subjects" },
          { label: "Ciencias", href: "#subjects" },
          { label: "Reservar una clase", href: "/signup" },
        ],
      },
      {
        heading: "Zanoba",
        links: [
          { label: "Cómo funciona", href: "#how" },
          { label: "Precios", href: "#pricing" },
          { label: "Iniciar sesión", href: "/login" },
        ],
      },
      { heading: "Ayuda", links: [{ label: "Centro de ayuda" }, { label: "Contacto" }, { label: "Estado" }] },
    ],
    legal: "Zanoba — un tutor de IA para idiomas y ciencias.",
  },
};

const de: LandingCopy = {
  heroMock: {
    badge: "Live",
    badgeLabel: "Stunde mit KI-Tutor",
    headline1: "KI-Tutor. Echter Unterricht.",
    headline2: "Echte Fortschritte.",
    body: "Einzelstunden mit einem KI-Tutor: Gespräch in Echtzeit, interaktives Whiteboard und Lernen, das um dich herum gebaut ist.",
    pills: ["Sprich ganz natürlich", "Die KI schreibt und erklärt", "Individuelle Stunden", "Passt sich dir an"],
    selectLabel: "Unterrichtssprache",
    cta: "Starte deine erste Stunde",
    trial: "7 Tage kostenlos testen",
    cancel: "Jederzeit kündbar",
    tutorCardTitle: "Dein KI-Tutor",
    tutorName: "Luna",
    tutorStatus: "Online und bereit zu unterrichten",
    tutorTraits: [
      "Geduldig und ermutigend",
      "Erklärt auf mehrere Arten",
      "Passt sich deinem Tempo an",
      "Hier, damit du es schaffst",
    ],
    features: [
      { title: "Nach Lehrplan", body: "Strukturierte Stunden, die echtes Können aufbauen" },
      { title: "KI-Tutor live", body: "Natürliche Gespräche per Stimme" },
      { title: "Kluge Anpassung", body: "Lernt dein Niveau und wächst mit dir" },
      { title: "Sicher und fokussiert", body: "Gemacht für effektives Lernen ohne Ablenkung" },
    ],
  },
  nav: {
    subjects: "Fächer",
    how: "So funktioniert es",
    pricing: "Preise",
    login: "Anmelden",
    start: "Kostenlos starten",
    menu: "Zu einem Abschnitt springen",
  },
  hero: {
    eyebrow: "Live-Einzelunterricht · Sprachen und Naturwissenschaften",
    headline: "Ein Tutor für jedes Fach, frei zu jeder Stunde.",
    body: "50-minütige Videostunden in acht Sprachen und sechs Naturwissenschaften. Fach wählen, Termin wählen, gemeinsam durcharbeiten — um 6 Uhr morgens oder um Mitternacht.",
    pickLabel: "Was möchtest du lernen?",
    languages: "Sprachen",
    sciences: "Naturwissenschaften",
    cta: "Kostenlose Stunde buchen",
    ctaNote: "Deine erste Stunde ist kostenlos. Ohne Karte.",
    boardLabel: "An der Tafel",
    live: "Live",
    tutorLine: "Zanoba-Tutor",
    levelsHeading: "Über die Niveaus",
    levelsBody: "Jede Sprache durchläuft die GER-Skala von A1 bis C1. Du weißt nicht, wo du stehst?",
    levelsCta: "Mach den Einstufungstest",
  },
  showcase: {
    heading: "So läuft eine Zanoba-Stunde",
    body: "Kein Chatfenster. Ein Tutor, der vor der Kamera erscheint, dich durch den Stoff führt und mit dir an der Tafel schreibt.",
    expand: "Mehr lesen",
    collapse: "Schließen",
    cards: [
      {
        line1: "Ein Tutor mit Gesicht.",
        line2: "Eins zu eins, per Live-Video.",
        body: "Dein Tutor kommt vor die Kamera und spricht — schaut dich an, wartet, während du denkst, und hakt nach, wenn dein Satz stockt. Fünfzig Minuten, nur ihr zwei.",
      },
      {
        line1: "Eine gemeinsame Tafel.",
        line2: "Ihr schreibt beide darauf.",
        body: "Skizziere das Dreieck, zeig deinen Rechenweg, füg ein Foto der Aufgabe ein. Dein Tutor arbeitet auf derselben Tafel und korrigiert den Schritt, nicht nur das Ergebnis.",
      },
      {
        line1: "Zwischen den Stunden.",
        line2: "Frag alles, zu jeder Zeit.",
        body: "Um Mitternacht bei Aufgabe 7 hängen geblieben? Schick sie. Derselbe Tutor antwortet im Chat — mit dem Kontext von allem, was ihr zusammen gemacht habt.",
      },
      {
        line1: "Ein Lehrplan pro Fach.",
        line2: "Er weiß, was als Nächstes kommt.",
        body: "Sprachen folgen der GER-Skala, Naturwissenschaften dem Lehrplan. Jede Stunde beginnt dort, wo die letzte aufgehört hat.",
      },
    ],
  },
  facts: [
    { value: "24/7", label: "Freie Termine, jeden Tag im Jahr" },
    { value: "14", label: "Fächer, von Koreanisch bis zum Satz von Bayes" },
    { value: "50 Min", label: "Jede Stunde, eins zu eins per Video" },
  ],
  benefits: {
    heading: "Was ein Tutor kann, der nie müde wird",
    items: [
      {
        title: "Er wartet auf deine Frage",
        body: "Frag dasselbe dreimal. Dein Tutor seufzt nie, schaut nie auf die Uhr und geht nie weiter, bevor du sagst, dass du bereit bist.",
      },
      {
        title: "Er unterrichtet, statt nur zu antworten",
        body: "Jede Stunde folgt einem Plan: das Konzept, dann ein durchgerechnetes Beispiel, dann Aufgaben, die du führst. Du gehst mit der Methode nach Hause, nicht mit dem Lösungsheft.",
      },
      {
        title: "Er erinnert sich an letzte Woche",
        body: "Dein Tutor macht dort weiter, wo die letzte Stunde endete — samt dem Schritt, der dich gestolpert hat — damit nichts zweimal erklärt werden muss.",
      },
    ],
  },
  subjects: {
    heading: "Vierzehn Fächer, ein Tutor",
    body: "Buche sie alle im selben Kalender, wechsle von Woche zu Woche und behalte einen einzigen Überblick über alles, was du bearbeitet hast.",
    languages: "Sprachen",
    sciences: "Naturwissenschaften",
    cta: "Stunde buchen",
  },
  how: {
    heading: "So läuft eine Stunde ab",
    steps: [
      {
        title: "Fach und Termin wählen",
        body: "Vierzehn Fächer, 50-Minuten-Stunden, die zur vollen und zur halben Stunde beginnen. Buche drei Wochen im Voraus oder in zwanzig Minuten.",
      },
      {
        title: "Per Video dazukommen",
        body: "Dein Tutor steht schon an der Tafel. Bring deine Hausaufgaben mit, ein Foto einer Aufgabe oder einfach das, was du im Unterricht nicht verstanden hast.",
      },
      {
        title: "Behalte die Tafel",
        body: "Jede Stunde speichert Tafelbild und Mitschrift in deinem Kalender — Wiederholen heißt also einfach nachlesen, was ihr beide geschrieben habt.",
      },
    ],
  },
  pricing: {
    heading: "Bezahle Stunden, keine Mitgliedschaft",
    body: "Fang kostenlos an und wähl dann das Format, das zu deinem Lernen passt.",
    badge: "Am beliebtesten",
    plans: [
      {
        name: "Pro Stunde",
        price: "12 €",
        cadence: "pro Stunde",
        body: "Buche einzeln, in jedem Fach.",
        features: ["Kein Abo", "Guthaben verfällt nie", "Absage bis 1 Stunde vorher"],
        cta: "Kostenlos starten",
      },
      {
        name: "Monatlich",
        price: "39 €",
        cadence: "pro Monat",
        body: "Für ein Fach, das du Woche für Woche durcharbeitest.",
        features: [
          "12 Stunden im Monat, in beliebigen Fächern",
          "Unbegrenzter Chat zwischen den Stunden",
          "Google-Kalender-Sync und Erinnerungen",
        ],
        cta: "Kostenlos starten",
      },
    ],
    note: "Beide Tarife beginnen mit einer kostenlosen Stunde. Jederzeit in den Einstellungen kündbar.",
  },
  testimonials: {
    heading: "Was Lernende sagen",
    items: [
      {
        quote: "Ich buche Integrale um 23 Uhr, weil ich dann wirklich rechne. Es war noch kein einziges Mal belegt.",
        name: "Amine",
        detail: "Mathematik · erstes Semester Ingenieurwesen",
      },
      {
        quote: "Mir ist das Fragen nicht mehr peinlich. Der Subjuntivo wird einfach noch mal erklärt, anders, bis er sitzt.",
        name: "Klara",
        detail: "Spanisch · B1",
      },
      {
        quote: "Das Tafelbild jeder Stunde ist inzwischen mein einziges Lernmaterial. Praktisch meine eigene Handschrift.",
        name: "Tomás",
        detail: "Chemie · Abschlussjahr",
      },
    ],
  },
  faq: {
    heading: "Fragen, beantwortet",
    items: [
      {
        q: "Ist der Tutor ein Mensch?",
        a: "Nein. Dein Tutor ist eine KI, die per Live-Video dazukommt, spricht, zuhört und auf einer gemeinsamen Tafel schreibt. Deshalb ist er zu jeder Stunde verfügbar und muss nie Wochen im Voraus gebucht werden.",
      },
      {
        q: "Was passiert in der kostenlosen Stunde?",
        a: "Volle 50 Minuten, im Fach deiner Wahl, ohne Abstriche. Zum Buchen ist keine Karte nötig.",
      },
      {
        q: "Welche Fächer kann ich belegen?",
        a: "Acht Sprachen — Englisch, Französisch, Spanisch, Deutsch, Italienisch, Arabisch, Chinesisch und Koreanisch, jeweils von A1 bis C1 — und sechs Naturwissenschaften: Mathematik, Physik, Chemie, Biologie, Informatik und Statistik.",
      },
      {
        q: "Kann ich das Fach wechseln?",
        a: "Jede Stunde wird einzeln gebucht, du kannst also montags Spanisch und donnerstags Physik nehmen. Dein Fortschritt wird pro Fach geführt.",
      },
      {
        q: "Was brauche ich für eine Stunde?",
        a: "Einen Browser, ein Mikrofon und eine Kamera. Nichts zu installieren. Eine Handykamera, die auf deine Hausaufgaben zeigt, funktioniert auch bestens.",
      },
      {
        q: "Kann ich eine Stunde absagen?",
        a: "Bis eine Stunde vor Beginn, über deinen Kalender. Das Guthaben geht direkt auf dein Konto zurück.",
      },
    ],
  },
  footer: {
    tagline: "Live-Unterricht in Sprachen und Naturwissenschaften, mit einem Tutor, der da ist, wenn du da bist.",
    columns: [
      {
        heading: "Fächer",
        links: [
          { label: "Sprachen", href: "#subjects" },
          { label: "Naturwissenschaften", href: "#subjects" },
          { label: "Stunde buchen", href: "/signup" },
        ],
      },
      {
        heading: "Zanoba",
        links: [
          { label: "So funktioniert es", href: "#how" },
          { label: "Preise", href: "#pricing" },
          { label: "Anmelden", href: "/login" },
        ],
      },
      { heading: "Hilfe", links: [{ label: "Hilfebereich" }, { label: "Kontakt" }, { label: "Status" }] },
    ],
    legal: "Zanoba — ein KI-Tutor für Sprachen und Naturwissenschaften.",
  },
};

const it: LandingCopy = {
  heroMock: {
    badge: "Dal vivo",
    badgeLabel: "Lezione con tutor IA",
    headline1: "Tutor IA. Insegnamento vero.",
    headline2: "Progressi veri.",
    body: "Lezioni individuali con un tutor IA: conversazione dal vivo, lavagna interattiva e un percorso costruito su di te.",
    pills: ["Parla con naturalezza", "L'IA scrive e spiega", "Lezioni su misura", "Si adatta a te"],
    selectLabel: "Lingua della lezione",
    cta: "Inizia la tua prima lezione",
    trial: "7 giorni di prova gratuita",
    cancel: "Disdici quando vuoi",
    tutorCardTitle: "Il tuo tutor IA",
    tutorName: "Luna",
    tutorStatus: "Online e pronta a insegnare",
    tutorTraits: [
      "Paziente e incoraggiante",
      "Spiega in più modi",
      "Si adatta al tuo ritmo",
      "È qui per farti riuscire",
    ],
    features: [
      { title: "Basato su un programma", body: "Lezioni strutturate che costruiscono competenze reali" },
      { title: "Tutor IA dal vivo", body: "Conversazioni vocali naturali" },
      { title: "Adattamento intelligente", body: "Impara il tuo livello e cresce con te" },
      { title: "Sicuro e concentrato", body: "Pensato per imparare senza distrazioni" },
    ],
  },
  nav: {
    subjects: "Materie",
    how: "Come funziona",
    pricing: "Prezzi",
    login: "Accedi",
    start: "Inizia gratis",
    menu: "Vai a una sezione",
  },
  hero: {
    eyebrow: "Lezioni individuali dal vivo · lingue e scienze",
    headline: "Un tutor per ogni materia, libero a ogni ora.",
    body: "Lezioni video di 50 minuti in otto lingue e sei materie scientifiche. Scegli la materia, scegli l'orario e affrontatela insieme — alle 6 del mattino come a mezzanotte.",
    pickLabel: "Cosa vuoi imparare?",
    languages: "Lingue",
    sciences: "Materie scientifiche",
    cta: "Prenota una lezione gratuita",
    ctaNote: "La prima lezione è gratis. Senza carta.",
    boardLabel: "Alla lavagna",
    live: "Dal vivo",
    tutorLine: "Tutor Zanoba",
    levelsHeading: "Sui livelli",
    levelsBody: "Ogni lingua percorre la scala del QCER dall'A1 al C1. Non sai a che punto sei?",
    levelsCta: "Fai il test di livello",
  },
  showcase: {
    heading: "Dentro una lezione Zanoba",
    body: "Non una finestra di chat. Un tutor che si presenta in video, ti guida a voce e scrive con te alla lavagna.",
    expand: "Leggi di più",
    collapse: "Chiudi",
    cards: [
      {
        line1: "Un tutor con una faccia.",
        line2: "Uno a uno, in video dal vivo.",
        body: "Il tuo tutor entra in video e parla: ti guarda, aspetta mentre pensi e riprende quando la frase ti si spegne. Cinquanta minuti, solo voi due.",
      },
      {
        line1: "Una lavagna condivisa.",
        line2: "Ci scrivete in due.",
        body: "Disegna il triangolo, mostra i passaggi, incolla la foto dell'esercizio. Il tuo tutor lavora sulla stessa lavagna e corregge il passaggio, non solo il risultato.",
      },
      {
        line1: "Tra una lezione e l'altra.",
        line2: "Chiedi qualsiasi cosa, a qualsiasi ora.",
        body: "Bloccato sull'esercizio 7 a mezzanotte? Mandalo. Lo stesso tutor risponde in chat, con il contesto di tutto quello che avete fatto insieme.",
      },
      {
        line1: "Un programma per materia.",
        line2: "Sa cosa viene dopo.",
        body: "Le lingue seguono la scala del QCER, le scienze seguono il programma. Ogni lezione riparte da dove si era chiusa l'ultima.",
      },
    ],
  },
  facts: [
    { value: "24/7", label: "Orari aperti, ogni giorno dell'anno" },
    { value: "14", label: "Materie, dal coreano al teorema di Bayes" },
    { value: "50 min", label: "Ogni lezione, uno a uno in video" },
  ],
  benefits: {
    heading: "Cosa può fare un tutor che non si stanca mai",
    items: [
      {
        title: "Aspetta la tua domanda",
        body: "Chiedi la stessa cosa tre volte. Il tuo tutor non sbuffa mai, non guarda l'orologio e non va avanti finché non dici che sei pronto.",
      },
      {
        title: "Insegna, non risponde e basta",
        body: "Ogni lezione segue un piano: il concetto, poi un esempio svolto, poi esercizi guidati da te. Esci con il metodo, non con le soluzioni.",
      },
      {
        title: "Si ricorda della settimana scorsa",
        body: "Il tuo tutor riapre dove si era fermata l'ultima lezione — compreso il passaggio che ti aveva bloccato — così niente va spiegato due volte.",
      },
    ],
  },
  subjects: {
    heading: "Quattordici materie, un solo tutor",
    body: "Prenotale tutte nello stesso calendario, alternale settimana per settimana e tieni un unico registro di quello che hai fatto.",
    languages: "Lingue",
    sciences: "Materie scientifiche",
    cta: "Prenota una lezione",
  },
  how: {
    heading: "Come funziona una lezione",
    steps: [
      {
        title: "Scegli materia e orario",
        body: "Quattordici materie, lezioni di 50 minuti che iniziano all'ora e alla mezz'ora. Prenota con tre settimane di anticipo o fra venti minuti.",
      },
      {
        title: "Collegati in video",
        body: "Il tuo tutor è già alla lavagna. Porta i compiti, la foto di un esercizio o semplicemente quello che non hai seguito a scuola.",
      },
      {
        title: "Tieniti la lavagna",
        body: "Ogni lezione salva lavagna e trascrizione nel tuo calendario: ripassare vuol dire rileggere quello che avete scritto insieme.",
      },
    ],
  },
  pricing: {
    heading: "Paghi le lezioni, non un abbonamento",
    body: "Inizia gratis, poi scegli la formula adatta a come studi.",
    badge: "Il più scelto",
    plans: [
      {
        name: "A lezione",
        price: "12 €",
        cadence: "a lezione",
        body: "Prenota una alla volta, in qualsiasi materia.",
        features: ["Nessun abbonamento", "I crediti non scadono", "Disdici fino a 1 ora prima"],
        cta: "Inizia gratis",
      },
      {
        name: "Mensile",
        price: "39 €",
        cadence: "al mese",
        body: "Per una materia che segui settimana dopo settimana.",
        features: [
          "12 lezioni al mese, in qualsiasi materia",
          "Chat illimitata tra una lezione e l'altra",
          "Sincronizzazione e promemoria con Google Calendar",
        ],
        cta: "Inizia gratis",
      },
    ],
    note: "Entrambi i piani iniziano con una lezione gratuita. Disdici quando vuoi dalle Impostazioni.",
  },
  testimonials: {
    heading: "Cosa dicono gli studenti",
    items: [
      {
        quote: "Prenoto gli integrali alle 23 perché è lì che faccio davvero gli esercizi. Non l'ho mai trovato occupato.",
        name: "Amine",
        detail: "Matematica · primo anno di ingegneria",
      },
      {
        quote: "Ho smesso di vergognarmi a chiedere. Ti rispiega il congiuntivo, in un altro modo, finché non entra.",
        name: "Klara",
        detail: "Spagnolo · B1",
      },
      {
        quote: "La lavagna di ogni lezione è l'unico materiale di ripasso che uso. È praticamente la mia calligrafia.",
        name: "Tomás",
        detail: "Chimica · ultimo anno",
      },
    ],
  },
  faq: {
    heading: "Domande, con risposta",
    items: [
      {
        q: "Il tutor è una persona?",
        a: "No. Il tuo tutor è un'IA che si collega in video dal vivo, parla, ascolta e scrive su una lavagna condivisa. Per questo è disponibile a qualsiasi ora e non va prenotato con settimane di anticipo.",
      },
      {
        q: "Cosa succede nella lezione gratuita?",
        a: "50 minuti pieni, nella materia che scegli, senza nulla di meno. Per prenotarla non serve la carta.",
      },
      {
        q: "Quali materie posso seguire?",
        a: "Otto lingue — inglese, francese, spagnolo, tedesco, italiano, arabo, cinese e coreano, ciascuna dall'A1 al C1 — e sei materie scientifiche: matematica, fisica, chimica, biologia, informatica e statistica.",
      },
      {
        q: "Posso cambiare materia?",
        a: "Ogni lezione si prenota da sola, quindi puoi fare spagnolo il lunedì e fisica il giovedì. I progressi sono tenuti per materia.",
      },
      {
        q: "Cosa mi serve per seguire una lezione?",
        a: "Un browser, un microfono e una webcam. Niente da installare. Anche la fotocamera del telefono puntata sui compiti funziona benissimo.",
      },
      {
        q: "Posso disdire una lezione?",
        a: "Fino a un'ora prima dell'inizio, dal tuo calendario. Il credito torna subito sul tuo account.",
      },
    ],
  },
  footer: {
    tagline: "Lezioni dal vivo di lingue e scienze, con un tutor che c'è quando ci sei tu.",
    columns: [
      {
        heading: "Materie",
        links: [
          { label: "Lingue", href: "#subjects" },
          { label: "Scienze", href: "#subjects" },
          { label: "Prenota una lezione", href: "/signup" },
        ],
      },
      {
        heading: "Zanoba",
        links: [
          { label: "Come funziona", href: "#how" },
          { label: "Prezzi", href: "#pricing" },
          { label: "Accedi", href: "/login" },
        ],
      },
      { heading: "Assistenza", links: [{ label: "Centro assistenza" }, { label: "Contatti" }, { label: "Stato" }] },
    ],
    legal: "Zanoba — un tutor IA per lingue e scienze.",
  },
};

const ar: LandingCopy = {
  heroMock: {
    badge: "مباشر",
    badgeLabel: "درس مع معلم ذكي",
    headline1: "معلم ذكي. تعليم حقيقي.",
    headline2: "تقدّم حقيقي.",
    body: "دروس فردية مع معلم ذكي: محادثة مباشرة، ولوح تفاعلي، وتعلّم مبنيّ حولك أنت.",
    pills: ["تحدّث بطبيعية", "الذكاء الاصطناعي يكتب ويشرح", "دروس مخصّصة", "يتكيّف معك"],
    selectLabel: "لغة الدرس",
    cta: "ابدأ درسك الأول",
    trial: "تجربة مجانية 7 أيام",
    cancel: "الإلغاء متاح في أي وقت",
    tutorCardTitle: "معلمك الذكي",
    tutorName: "لونا",
    tutorStatus: "متصلة وجاهزة للتدريس",
    tutorTraits: [
      "صبورة ومشجّعة",
      "تشرح بأكثر من طريقة",
      "تتكيّف مع إيقاعك",
      "هنا لتساعدك على النجاح",
    ],
    features: [
      { title: "قائم على منهج", body: "دروس منظّمة تبني مهارات حقيقية" },
      { title: "معلم ذكي مباشر", body: "محادثات صوتية طبيعية" },
      { title: "تكيّف ذكي", body: "يتعرّف على مستواك ويتطوّر معك" },
      { title: "آمن ومركّز", body: "مصمَّم لتعلّم فعّال بلا تشتيت" },
    ],
  },
  nav: {
    subjects: "المواد",
    how: "كيف يعمل",
    pricing: "الأسعار",
    login: "تسجيل الدخول",
    start: "ابدأ مجانًا",
    menu: "الانتقال إلى قسم",
  },
  hero: {
    eyebrow: "دروس فردية مباشرة · لغات وعلوم",
    headline: "معلم لكل مادة، متاح في كل ساعة.",
    body: "دروس فيديو مدتها 50 دقيقة في ثماني لغات وست مواد علمية. اختر المادة، واختر الموعد، واعملا معًا — في السادسة صباحًا أو في منتصف الليل.",
    pickLabel: "ماذا تريد أن تتعلّم؟",
    languages: "اللغات",
    sciences: "المواد العلمية",
    cta: "احجز درسًا مجانيًا",
    ctaNote: "درسك الأول مجاني. بلا بطاقة.",
    boardLabel: "على السبورة",
    live: "مباشر",
    tutorLine: "معلم زنوبة",
    levelsHeading: "عن المستويات",
    levelsBody: "كل لغة تُدرَّس على سلّم الإطار الأوروبي المرجعي من A1 إلى C1. لا تعرف أين موقعك؟",
    levelsCta: "اختبر مستواك",
  },
  showcase: {
    heading: "داخل درس في زنوبة",
    body: "ليست نافذة دردشة. معلم يظهر أمام الكاميرا، ويشرح لك بصوته، ويكتب معك على السبورة.",
    expand: "اقرأ المزيد",
    collapse: "إغلاق",
    cards: [
      {
        line1: "معلم له وجه.",
        line2: "واحد لواحد، بالفيديو المباشر.",
        body: "ينضم معلمك أمام الكاميرا ويتحدث — ينظر إليك، وينتظر بينما تفكّر، ويلتقط الخيط حين تتوقف في منتصف الجملة. خمسون دقيقة لكما وحدكما.",
      },
      {
        line1: "سبورة مشتركة.",
        line2: "تكتبان عليها معًا.",
        body: "ارسم المثلث، واعرض خطوات حلّك، وألصق صورة التمرين. يعمل معلمك على السبورة نفسها ويصحّح الخطوة، لا النتيجة فقط.",
      },
      {
        line1: "بين الدروس.",
        line2: "اسأل ما تشاء، في أي ساعة.",
        body: "تعثّرت في السؤال السابع منتصف الليل؟ أرسله. يجيبك المعلم نفسه في الدردشة، وهو يعرف كل ما درستماه معًا.",
      },
      {
        line1: "منهج لكل مادة.",
        line2: "يعرف ما يأتي بعد ذلك.",
        body: "اللغات تسير على سلّم الإطار الأوروبي، والعلوم تسير على المقرر. كل درس يبدأ حيث انتهى الذي قبله.",
      },
    ],
  },
  facts: [
    { value: "24/7", label: "مواعيد متاحة كل يوم في السنة" },
    { value: "14", label: "مادة، من الكورية إلى قاعدة بايز" },
    { value: "50 دقيقة", label: "كل درس، فرديًا بالفيديو" },
  ],
  benefits: {
    heading: "ما يستطيعه معلم لا يتعب أبدًا",
    items: [
      {
        title: "ينتظر سؤالك",
        body: "اسأل الشيء نفسه ثلاث مرات. معلمك لا يتنهّد، ولا ينظر إلى الساعة، ولا ينتقل قبل أن تقول إنك جاهز.",
      },
      {
        title: "يعلّم، لا يكتفي بالإجابة",
        body: "كل درس يسير على خطة: الفكرة، ثم مثال محلول، ثم تمارين تقودها أنت. تخرج بالطريقة، لا بمفتاح الحل.",
      },
      {
        title: "يتذكّر الأسبوع الماضي",
        body: "يفتح معلمك من حيث توقّف الدرس السابق — بما في ذلك الخطوة التي أعاقتك — فلا يُشرح شيء مرتين.",
      },
    ],
  },
  subjects: {
    heading: "أربع عشرة مادة، ومعلم واحد",
    body: "احجزها كلها في التقويم نفسه، وتنقّل بينها أسبوعًا بعد أسبوع، واحتفظ بسجل واحد لكل ما درسته.",
    languages: "اللغات",
    sciences: "المواد العلمية",
    cta: "احجز درسًا",
  },
  how: {
    heading: "كيف يجري الدرس",
    steps: [
      {
        title: "اختر مادة وموعدًا",
        body: "أربع عشرة مادة، ودروس من 50 دقيقة تبدأ عند رأس الساعة وعند النصف. احجز قبل ثلاثة أسابيع أو بعد عشرين دقيقة من الآن.",
      },
      {
        title: "احضر بالفيديو",
        body: "معلمك أمام السبورة سلفًا. أحضر واجبك، أو صورة لمسألة، أو ببساطة ما لم تفهمه في الصف.",
      },
      {
        title: "احتفظ بالسبورة",
        body: "كل درس يحفظ سبورته ونصّه في تقويمك، فتصبح المراجعة قراءةً لما كتبتماه معًا.",
      },
    ],
  },
  pricing: {
    heading: "ادفع مقابل الدروس، لا مقابل اشتراك",
    body: "ابدأ مجانًا، ثم اختر الصيغة التي تناسب طريقتك في الدراسة.",
    badge: "الأكثر اختيارًا",
    plans: [
      {
        name: "لكل درس",
        price: "12 €",
        cadence: "للدرس الواحد",
        body: "احجز درسًا واحدًا في كل مرة، في أي مادة.",
        features: ["بلا اشتراك", "الرصيد لا ينتهي", "الإلغاء حتى ساعة قبل الموعد"],
        cta: "ابدأ مجانًا",
      },
      {
        name: "شهري",
        price: "39 €",
        cadence: "شهريًا",
        body: "لمادة تتقدّم فيها أسبوعًا بعد أسبوع.",
        features: [
          "12 درسًا في الشهر، في أي مادة",
          "دردشة بلا حدود بين الدروس",
          "مزامنة تقويم Google والتذكيرات",
        ],
        cta: "ابدأ مجانًا",
      },
    ],
    note: "تبدأ الخطتان بدرس مجاني. ويمكنك الإلغاء في أي وقت من الإعدادات.",
  },
  testimonials: {
    heading: "ماذا يقول المتعلّمون",
    items: [
      {
        quote: "أحجز دروس التكامل في الحادية عشرة ليلًا لأنني حينها أحلّ تماريني فعلًا. ولم يحدث قط أن كان غير متاح.",
        name: "أمين",
        detail: "الرياضيات · السنة الأولى هندسة",
      },
      {
        quote: "لم أعد أخجل من السؤال. يعيد ببساطة شرح صيغة الشرط بطريقة أخرى حتى تستقر.",
        name: "كلارا",
        detail: "الإسبانية · B1",
      },
      {
        quote: "سبورة كل درس هي مادة المراجعة الوحيدة التي أستعملها الآن. وكأنها بخط يدي.",
        name: "توماس",
        detail: "الكيمياء · السنة النهائية",
      },
    ],
  },
  faq: {
    heading: "أسئلة وأجوبة",
    items: [
      {
        q: "هل المعلم إنسان؟",
        a: "لا. معلمك ذكاء اصطناعي ينضم إليك بالفيديو المباشر، ويتحدث، ويستمع، ويكتب على سبورة مشتركة. لذلك هو متاح في أي ساعة ولا يحتاج إلى حجز قبل أسابيع.",
      },
      {
        q: "ماذا يحدث في الدرس المجاني؟",
        a: "خمسون دقيقة كاملة، في المادة التي تختارها، دون انتقاص. ولا حاجة إلى بطاقة لحجزه.",
      },
      {
        q: "ما المواد التي يمكنني دراستها؟",
        a: "ثماني لغات — الإنجليزية والفرنسية والإسبانية والألمانية والإيطالية والعربية والصينية والكورية، كل منها من A1 إلى C1 — وست مواد علمية: الرياضيات والفيزياء والكيمياء والأحياء وعلوم الحاسوب والإحصاء.",
      },
      {
        q: "هل يمكنني تغيير المادة؟",
        a: "كل درس يُحجز على حدة، فيمكنك أخذ الإسبانية الإثنين والفيزياء الخميس. ويُحفظ تقدّمك لكل مادة على حدة.",
      },
      {
        q: "ماذا أحتاج لحضور درس؟",
        a: "متصفّح وميكروفون وكاميرا. لا شيء تثبّته. وكاميرا الهاتف الموجّهة إلى واجبك تفي بالغرض تمامًا.",
      },
      {
        q: "هل يمكنني إلغاء درس؟",
        a: "حتى ساعة قبل بدايته، من تقويمك. ويعود الرصيد مباشرة إلى حسابك.",
      },
    ],
  },
  footer: {
    tagline: "دروس مباشرة في اللغات والعلوم، مع معلم يحضر حين تحضر.",
    columns: [
      {
        heading: "المواد",
        links: [
          { label: "اللغات", href: "#subjects" },
          { label: "العلوم", href: "#subjects" },
          { label: "احجز درسًا", href: "/signup" },
        ],
      },
      {
        heading: "زنوبة",
        links: [
          { label: "كيف يعمل", href: "#how" },
          { label: "الأسعار", href: "#pricing" },
          { label: "تسجيل الدخول", href: "/login" },
        ],
      },
      { heading: "الدعم", links: [{ label: "مركز المساعدة" }, { label: "اتصل بنا" }, { label: "حالة الخدمة" }] },
    ],
    legal: "زنوبة — معلم ذكي للغات والعلوم.",
  },
};

const zh: LandingCopy = {
  heroMock: {
    badge: "直播",
    badgeLabel: "AI 导师课堂",
    headline1: "AI 导师。真正的教学。",
    headline2: "真正的进步。",
    body: "一对一的 AI 导师课：实时对话、互动白板，以及围绕你本人设计的学习路径。",
    pills: ["自然地开口", "AI 边写边讲", "个性化课程", "随你调整"],
    selectLabel: "授课语言",
    cta: "开始第一节课",
    trial: "7 天免费试用",
    cancel: "随时取消",
    tutorCardTitle: "你的 AI 导师",
    tutorName: "Luna",
    tutorStatus: "在线，随时开课",
    tutorTraits: ["有耐心、会鼓励", "换几种方式讲解", "配合你的节奏", "陪你一路学成"],
    features: [
      { title: "依照课程大纲", body: "结构化的课程，练出真本事" },
      { title: "AI 导师直播", body: "自然的语音对话" },
      { title: "智能适配", body: "摸清你的水平，并与你一同提高" },
      { title: "安全专注", body: "为高效、无干扰的学习而设计" },
    ],
  },
  nav: {
    subjects: "科目",
    how: "如何上课",
    pricing: "价格",
    login: "登录",
    start: "免费开始",
    menu: "跳转到章节",
  },
  hero: {
    eyebrow: "一对一直播课 · 语言与理科",
    headline: "每一门科目都有导师，随时有空。",
    body: "八门语言、六门理科，每节 50 分钟的直播视频课。选科目、选时间，一起把它弄懂——早上六点或午夜都行。",
    pickLabel: "你想学什么？",
    languages: "语言",
    sciences: "理科科目",
    cta: "预约免费课",
    ctaNote: "第一节课免费，无需绑卡。",
    boardLabel: "板书",
    live: "直播中",
    tutorLine: "Zanoba 导师",
    levelsHeading: "关于等级",
    levelsBody: "每门语言都按 CEFR 从 A1 教到 C1。不确定自己在哪一级？",
    levelsCta: "做个分级测试",
  },
  showcase: {
    heading: "一节 Zanoba 课里发生了什么",
    body: "不是聊天窗口，而是一位出镜的导师：讲给你听，还和你一起在白板上写。",
    expand: "了解更多",
    collapse: "收起",
    cards: [
      {
        line1: "一位看得见的导师。",
        line2: "一对一，实时视频。",
        body: "导师出镜说话——看着你，等你思考，在你话说到一半卡住时接上。五十分钟，只有你们两个人。",
      },
      {
        line1: "一块共用白板。",
        line2: "两个人一起写。",
        body: "画出三角形、写下你的步骤、贴一张题目照片。导师在同一块板上作答，纠正的是步骤，而不只是答案。",
      },
      {
        line1: "课与课之间。",
        line2: "任何时间，随便问。",
        body: "半夜卡在第 7 题？发过来。同一位导师在聊天里回答，并且记得你们一起学过的一切。",
      },
      {
        line1: "每门科目都有大纲。",
        line2: "它知道下一步学什么。",
        body: "语言按 CEFR 等级推进，理科按教学大纲推进。每节课都从上一节结束的地方开始。",
      },
    ],
  },
  facts: [
    { value: "24/7", label: "全年每天都有可约时段" },
    { value: "14", label: "门科目，从韩语到贝叶斯定理" },
    { value: "50 分钟", label: "每节课，一对一视频" },
  ],
  benefits: {
    heading: "一位永不疲倦的导师能做到什么",
    items: [
      {
        title: "它等你提问",
        body: "同一个问题问三遍，导师从不叹气、不看表，也绝不会在你说“可以了”之前往下讲。",
      },
      {
        title: "它教方法，不只给答案",
        body: "每节课都有计划：先讲概念，再做例题，然后由你主导练习。你带走的是方法，不是答案。",
      },
      {
        title: "它记得上周",
        body: "导师从上一节课停下的地方开始——包括让你卡住的那一步——不必把任何内容讲第二遍。",
      },
    ],
  },
  subjects: {
    heading: "十四门科目，一位导师",
    body: "在同一个日历里预约，每周换着上，所有学过的内容都记在同一份记录里。",
    languages: "语言",
    sciences: "理科科目",
    cta: "预约课程",
  },
  how: {
    heading: "一节课怎么上",
    steps: [
      {
        title: "选科目和时间",
        body: "十四门科目，50 分钟的课在整点和半点开始。可以约三周后，也可以约二十分钟后。",
      },
      {
        title: "视频入课",
        body: "导师已经站在白板前。带上作业、一张题目照片，或者课上没听懂的那一段。",
      },
      {
        title: "带走板书",
        body: "每节课都会把板书和文字记录保存到你的日历里，复习就是重读你们一起写下的内容。",
      },
    ],
  },
  pricing: {
    heading: "按课付费，不是会员制",
    body: "先免费试听，再挑一个适合你学习方式的方案。",
    badge: "最受欢迎",
    plans: [
      {
        name: "单节课",
        price: "€12",
        cadence: "每节课",
        body: "一次约一节，任何科目都行。",
        features: ["无需订阅", "课时永不过期", "开课前 1 小时可取消"],
        cta: "免费开始",
      },
      {
        name: "包月",
        price: "€39",
        cadence: "每月",
        body: "适合一周一节、持续推进的科目。",
        features: ["每月 12 节课，科目不限", "课间无限次聊天提问", "同步 Google 日历并提醒"],
        cta: "免费开始",
      },
    ],
    note: "两种方案都从一节免费课开始。可随时在“设置”中取消。",
  },
  testimonials: {
    heading: "学员怎么说",
    items: [
      {
        quote: "我把积分课约在晚上十一点，因为那才是我真正做题的时间。从来没有约不上过。",
        name: "Amine",
        detail: "数学 · 工科一年级",
      },
      {
        quote: "我不再因为提问而不好意思。它就换个说法再讲一遍虚拟式，直到我听懂为止。",
        name: "Klara",
        detail: "西班牙语 · B1",
      },
      {
        quote: "现在我复习只看每节课的板书。那基本上就是我自己的笔迹。",
        name: "Tomás",
        detail: "化学 · 毕业年级",
      },
    ],
  },
  faq: {
    heading: "常见问题",
    items: [
      {
        q: "导师是真人吗？",
        a: "不是。你的导师是一个 AI，会通过实时视频加入课堂，能说、能听，还能在共享白板上书写。所以它任何时间都在，也不需要提前几周预约。",
      },
      {
        q: "免费课上什么？",
        a: "完整的 50 分钟，科目由你选，内容不打折。预约时不需要绑定银行卡。",
      },
      {
        q: "有哪些科目可以上？",
        a: "八门语言——英语、法语、西班牙语、德语、意大利语、阿拉伯语、中文和韩语，每门都从 A1 到 C1——以及六门理科：数学、物理、化学、生物、计算机科学和统计学。",
      },
      {
        q: "可以换科目吗？",
        a: "每节课单独预约，所以你可以周一上西班牙语、周四上物理。学习进度按科目分别记录。",
      },
      {
        q: "上课需要准备什么？",
        a: "一个浏览器、一个麦克风和一个摄像头，不用安装任何东西。用手机摄像头对着作业本效果也很好。",
      },
      {
        q: "可以取消课程吗？",
        a: "开课前一小时内都可以在日历里取消，课时会立刻退回你的账户。",
      },
    ],
  },
  footer: {
    tagline: "语言与理科的直播课，导师在你有空的时候在。",
    columns: [
      {
        heading: "科目",
        links: [
          { label: "语言", href: "#subjects" },
          { label: "理科", href: "#subjects" },
          { label: "预约课程", href: "/signup" },
        ],
      },
      {
        heading: "Zanoba",
        links: [
          { label: "如何上课", href: "#how" },
          { label: "价格", href: "#pricing" },
          { label: "登录", href: "/login" },
        ],
      },
      { heading: "支持", links: [{ label: "帮助中心" }, { label: "联系我们" }, { label: "服务状态" }] },
    ],
    legal: "Zanoba —— 语言与理科的 AI 导师。",
  },
};

const ko: LandingCopy = {
  heroMock: {
    badge: "실시간",
    badgeLabel: "AI 튜터 수업",
    headline1: "AI 튜터. 진짜 수업.",
    headline2: "진짜 실력.",
    body: "AI 튜터와의 1:1 수업 — 실시간 대화, 인터랙티브 화이트보드, 그리고 당신에게 맞춘 학습.",
    pills: ["자연스럽게 말하기", "AI가 쓰고 설명하기", "맞춤 수업", "당신에게 맞춰 조절"],
    selectLabel: "수업 언어",
    cta: "첫 수업 시작하기",
    trial: "7일 무료 체험",
    cancel: "언제든 해지 가능",
    tutorCardTitle: "당신의 AI 튜터",
    tutorName: "Luna",
    tutorStatus: "온라인 — 바로 수업 가능",
    tutorTraits: ["참을성 있고 격려하는", "여러 방식으로 설명하는", "당신의 속도에 맞추는", "끝까지 함께하는"],
    features: [
      { title: "커리큘럼 기반", body: "실력을 쌓아 주는 체계적인 수업" },
      { title: "실시간 AI 튜터", body: "자연스러운 음성 대화" },
      { title: "똑똑한 적응", body: "당신의 수준을 파악하고 함께 성장" },
      { title: "안전하고 집중되는", body: "산만함 없이 효과적으로 배우도록 설계" },
    ],
  },
  nav: {
    subjects: "과목",
    how: "수업 방식",
    pricing: "요금",
    login: "로그인",
    start: "무료로 시작",
    menu: "섹션으로 이동",
  },
  hero: {
    eyebrow: "실시간 1:1 수업 · 언어와 과학",
    headline: "모든 과목의 튜터가, 언제든 비어 있습니다.",
    body: "여덟 개 언어와 여섯 개 과학 과목의 50분 화상 수업. 과목을 고르고 시간을 골라 함께 풀어 보세요 — 새벽 6시에도, 자정에도.",
    pickLabel: "무엇을 배우고 싶으세요?",
    languages: "언어",
    sciences: "과학 과목",
    cta: "무료 수업 예약하기",
    ctaNote: "첫 수업은 무료입니다. 카드도 필요 없습니다.",
    boardLabel: "칠판에는",
    live: "실시간",
    tutorLine: "Zanoba 튜터",
    levelsHeading: "레벨 안내",
    levelsBody: "모든 언어를 CEFR 기준 A1부터 C1까지 가르칩니다. 내 수준이 어디쯤인지 모르겠다면?",
    levelsCta: "레벨 테스트 받기",
  },
  showcase: {
    heading: "Zanoba 수업 속으로",
    body: "채팅창이 아닙니다. 카메라에 나타나 직접 설명하고, 칠판에 함께 쓰는 튜터입니다.",
    expand: "더 읽기",
    collapse: "닫기",
    cards: [
      {
        line1: "얼굴이 있는 튜터.",
        line2: "1:1 실시간 화상.",
        body: "튜터가 카메라를 켜고 말합니다 — 당신을 바라보고, 생각할 때 기다려 주고, 말끝을 흐리면 이어받습니다. 50분, 오직 둘만의 시간입니다.",
      },
      {
        line1: "함께 쓰는 칠판.",
        line2: "둘 다 적을 수 있습니다.",
        body: "삼각형을 그리고, 풀이 과정을 보여 주고, 문제 사진을 붙여 보세요. 튜터가 같은 칠판에서 답이 아니라 '그 단계'를 고쳐 줍니다.",
      },
      {
        line1: "수업과 수업 사이.",
        line2: "언제든 무엇이든 물어보세요.",
        body: "자정에 7번 문제에서 막혔나요? 보내세요. 같은 튜터가 지금까지 함께한 내용을 기억한 채로 채팅에서 답합니다.",
      },
      {
        line1: "과목마다 커리큘럼.",
        line2: "다음에 무엇을 할지 압니다.",
        body: "언어는 CEFR 단계를, 과학은 교과 과정을 따릅니다. 매 수업은 지난 수업이 끝난 지점에서 시작합니다.",
      },
    ],
  },
  facts: [
    { value: "24/7", label: "1년 내내 열려 있는 시간대" },
    { value: "14", label: "개 과목, 한국어부터 베이즈 정리까지" },
    { value: "50분", label: "모든 수업, 1:1 화상" },
  ],
  benefits: {
    heading: "지치지 않는 튜터가 할 수 있는 일",
    items: [
      {
        title: "질문을 기다립니다",
        body: "같은 것을 세 번 물어보세요. 튜터는 한숨 쉬지 않고, 시계를 보지 않으며, 준비됐다고 말하기 전에는 넘어가지 않습니다.",
      },
      {
        title: "답이 아니라 방법을 가르칩니다",
        body: "모든 수업에는 계획이 있습니다. 개념, 풀이 예시, 그다음엔 당신이 주도하는 문제. 정답지가 아니라 방법을 가지고 나옵니다.",
      },
      {
        title: "지난주를 기억합니다",
        body: "튜터는 지난 수업이 멈춘 자리에서 — 당신이 걸렸던 바로 그 단계까지 포함해 — 다시 시작합니다. 같은 설명을 두 번 들을 필요가 없습니다.",
      },
    ],
  },
  subjects: {
    heading: "열네 과목, 한 명의 튜터",
    body: "같은 캘린더에서 모두 예약하고, 주마다 과목을 바꾸고, 배운 모든 것을 한 곳에 기록해 두세요.",
    languages: "언어",
    sciences: "과학 과목",
    cta: "수업 예약하기",
  },
  how: {
    heading: "수업은 이렇게 진행됩니다",
    steps: [
      {
        title: "과목과 시간을 고르세요",
        body: "열네 과목, 정시와 30분에 시작하는 50분 수업. 3주 뒤로도, 20분 뒤로도 예약할 수 있습니다.",
      },
      {
        title: "화상으로 들어오세요",
        body: "튜터는 이미 칠판 앞에 있습니다. 숙제, 문제 사진, 아니면 수업에서 놓친 부분만 들고 오세요.",
      },
      {
        title: "칠판은 남습니다",
        body: "모든 수업의 칠판과 대화 기록이 캘린더에 저장됩니다. 복습은 둘이 함께 쓴 것을 다시 읽는 일이 됩니다.",
      },
    ],
  },
  pricing: {
    heading: "회원권이 아니라 수업에 지불하세요",
    body: "무료로 시작한 뒤, 공부 방식에 맞는 형태를 고르세요.",
    badge: "가장 인기",
    plans: [
      {
        name: "수업당",
        price: "€12",
        cadence: "수업 1회",
        body: "과목에 상관없이 한 번에 하나씩 예약합니다.",
        features: ["구독 없음", "수강권은 만료되지 않음", "시작 1시간 전까지 취소 가능"],
        cta: "무료로 시작",
      },
      {
        name: "월간",
        price: "€39",
        cadence: "월",
        body: "매주 이어서 공부하는 과목에 좋습니다.",
        features: ["월 12회 수업, 과목 제한 없음", "수업 사이 무제한 채팅", "Google 캘린더 동기화와 알림"],
        cta: "무료로 시작",
      },
    ],
    note: "두 요금제 모두 무료 수업 한 번으로 시작합니다. 설정에서 언제든 해지할 수 있습니다.",
  },
  testimonials: {
    heading: "수강생의 이야기",
    items: [
      {
        quote: "밤 11시에 적분 수업을 예약합니다. 그때가 제가 실제로 문제를 푸는 시간이거든요. 자리가 없던 적은 한 번도 없었어요.",
        name: "Amine",
        detail: "수학 · 공학 1학년",
      },
      {
        quote: "묻는 게 더는 창피하지 않아요. 접속법을 다른 방식으로, 이해될 때까지 다시 설명해 줍니다.",
        name: "Klara",
        detail: "스페인어 · B1",
      },
      {
        quote: "이제 복습 자료는 매 수업의 칠판뿐이에요. 사실상 제 손글씨나 마찬가지입니다.",
        name: "Tomás",
        detail: "화학 · 졸업반",
      },
    ],
  },
  faq: {
    heading: "자주 묻는 질문",
    items: [
      {
        q: "튜터는 사람인가요?",
        a: "아니요. 튜터는 실시간 화상으로 함께 들어와 말하고, 듣고, 공용 칠판에 쓰는 AI입니다. 그래서 어느 시간에나 가능하고, 몇 주 전에 예약할 필요도 없습니다.",
      },
      {
        q: "무료 수업에서는 무엇을 하나요?",
        a: "고른 과목으로 꽉 찬 50분을, 아끼는 것 없이 진행합니다. 예약에 카드도 필요 없습니다.",
      },
      {
        q: "어떤 과목을 들을 수 있나요?",
        a: "여덟 개 언어 — 영어, 프랑스어, 스페인어, 독일어, 이탈리아어, 아랍어, 중국어, 한국어를 각각 A1부터 C1까지 — 그리고 여섯 개 과학 과목: 수학, 물리, 화학, 생물, 컴퓨터 과학, 통계입니다.",
      },
      {
        q: "과목을 바꿀 수 있나요?",
        a: "수업은 하나씩 따로 예약하므로 월요일엔 스페인어, 목요일엔 물리를 들어도 됩니다. 진도는 과목별로 저장됩니다.",
      },
      {
        q: "수업에 들어가려면 무엇이 필요한가요?",
        a: "브라우저와 마이크, 카메라면 됩니다. 설치할 것은 없습니다. 휴대폰 카메라로 숙제를 비춰도 잘 됩니다.",
      },
      {
        q: "수업을 취소할 수 있나요?",
        a: "시작 한 시간 전까지 캘린더에서 취소할 수 있고, 수강권은 곧바로 계정으로 돌아갑니다.",
      },
    ],
  },
  footer: {
    tagline: "언어와 과학의 실시간 수업 — 당신이 있을 때 함께 있는 튜터와 함께.",
    columns: [
      {
        heading: "과목",
        links: [
          { label: "언어", href: "#subjects" },
          { label: "과학", href: "#subjects" },
          { label: "수업 예약", href: "/signup" },
        ],
      },
      {
        heading: "Zanoba",
        links: [
          { label: "수업 방식", href: "#how" },
          { label: "요금", href: "#pricing" },
          { label: "로그인", href: "/login" },
        ],
      },
      { heading: "지원", links: [{ label: "고객센터" }, { label: "문의" }, { label: "서비스 상태" }] },
    ],
    legal: "Zanoba — 언어와 과학을 위한 AI 튜터.",
  },
};

const COPY: Record<Lang, LandingCopy> = { en, fr, es, de, it, ar, zh, ko };

export function landingCopy(lang: Lang): LandingCopy {
  return COPY[lang] ?? COPY.en;
}
