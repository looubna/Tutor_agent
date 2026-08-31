/**
 * The deck for German A1.1 · "I can follow my first German lesson".
 *
 * Written here rather than by the material agent because the agent needs a
 * target before it can be pointed at one: this is the shape it produces, and
 * `worksheet.test.ts` checks it the way every generated deck will be checked.
 *
 * It is also the argument for the format. Seventeen slides, each one a title, a
 * subtitle, one or two blocks and a note — and the pages that look most unlike
 * each other (the alphabet grid, the dialogue, the closing idiom) are the same
 * three fields with different things written in them.
 *
 * Every article below is looked up in `words.de.json`, not remembered — a test
 * fails the build if one of them disagrees with the word file.
 */
export const SAMPLE = {
  lessonId: "german.a1-1.classroom",
  version: 1,
  title: "Hallo! Und wie heißt du?",
  subtitle: "Kommunikation · Grundstufe A1",
  cover: {
    src: "/materials/german/a1-1/photos/klassenzimmer.jpg",
    alt: "Ein leerer Kursraum mit Tischen und Stühlen.",
    assetId: "sample-klassenzimmer",
    credit: "Lauren Manning · CC BY",
  },
  meta: { niveau: "Grundstufe (A1)", nummer: "ZB_DE_A1_02", sprache: "Deutsch" },
  slides: [
    {
      id: "s1",
      title: "Lernziele",
      subtitle: "Das kannst du am Ende dieser Stunde.",
      blocks: [
        {
          kind: "goals",
          items: [
            "Ich kann jemanden auf Deutsch begrüßen – morgens, mittags und abends.",
            "Ich kann mich am Ende der Stunde verabschieden.",
            "Ich kann der, die und das mit den Wörtern aus dieser Stunde benutzen.",
          ],
        },
      ],
    },
    {
      id: "s2",
      title: "Einstieg",
      subtitle: "Es ist acht Uhr. Du kommst in den Kurs.",
      blocks: [
        {
          kind: "bubbles",
          turns: [
            { side: "l", text: "Guten Morgen! Ich bin Herr Klein." },
            { side: "r", text: "Auf Deutsch gibt es vier Grüße. Die Uhrzeit entscheidet." },
          ],
        },
        {
          kind: "cards",
          cols: 3,
          numbered: true,
          items: [
            { label: "Wie grüßt man in deiner Sprache?" },
            { label: "Gibt es einen Gruß nur für den Morgen?" },
            { label: "Sagst du zu deiner Lehrkraft du oder Sie?" },
          ],
        },
      ],
      note: { text: "Sprich im Kurs. Es gibt keine falsche Antwort." },
    },
    {
      id: "s3",
      title: "Die vier Grüße",
      subtitle: "Sprich nach. Die Uhr entscheidet, welcher Gruß passt.",
      blocks: [
        {
          kind: "cards",
          cols: 3,
          items: [
            { label: "Hallo", caption: "immer · informell", icon: "hallo" },
            { label: "Guten Morgen", caption: "bis etwa 11:00", icon: "morgen" },
            { label: "Guten Tag", caption: "11:00–18:00 · immer sicher", icon: "sonne" },
            { label: "Guten Abend", caption: "ab etwa 18:00", icon: "abend" },
            { label: "Gute Nacht", caption: "nur vor dem Schlafen", icon: "nacht" },
            { label: "Auf Wiedersehen", caption: "beim Gehen · formell", icon: "tuer" },
          ],
        },
      ],
      note: {
        title: "Achtung",
        text: "Gute Nacht ist kein Gruß. Man sagt es nur, wenn jemand schlafen geht.",
      },
    },
    {
      id: "s4",
      title: "du oder Sie?",
      subtitle: "Das ist die erste Entscheidung in jedem Gespräch.",
      // A photograph as a panel, and the two rows beside it. Two rows on their
      // own left the bottom half of this page white — check:fit measured it at
      // 44% — and a picture of a real room is the thing that makes du/Sie a
      // decision about people rather than a grammar note.
      blocks: [
        {
          kind: "photo",
          shape: "panel",
          src: "/materials/german/a1-1/photos/kurs.jpg",
          alt: "Lernende sitzen zusammen in einem Kursraum.",
          assetId: "sample-kurs",
          credit: "flickingerbrad · CC BY",
        },
        {
          kind: "rows",
          items: [
            { head: "du", body: "Freunde, Familie, Kinder, Leute im Kurs. Vorname." },
            { head: "Sie", body: "Fremde, im Geschäft, deine Lehrkraft – bis sie du sagt." },
          ],
        },
      ],
      note: {
        // Was "Englisch hat ein Wort für you" — which only helps a student who
        // already speaks English. Most do not, and the deck may not assume it.
        text: "Deutsch hat zwei Wörter: du und Sie. Das falsche Wort hören alle "
          + "sofort – viel früher als einen falschen Artikel.",
      },
    },
    {
      id: "s5",
      title: "der · die · das",
      subtitle: "Jedes Nomen hat einen Artikel. Lerne beide zusammen.",
      blocks: [
        {
          kind: "table",
          head: ["Artikel", "Beispiel", "Plural"],
          rows: [
            ["der", "der Tisch", "die Tische"],
            ["das", "das Buch", "die Bücher"],
            ["die", "die Aufgabe", "die Aufgaben"],
          ],
          caption: "Im Plural steht immer die.",
        },
      ],
      note: {
        title: "Tipp",
        text: "Schreib nie Tisch allein in dein Heft. Schreib der Tisch. Der Artikel "
          + "gehört zum Wort.",
      },
    },
    {
      id: "s6",
      title: "Wörter aus dem Kursraum",
      subtitle: "Sprich das Wort mit dem Artikel.",
      blocks: [
        {
          kind: "cards",
          cols: 3,
          // Photographs, and captions that are the plural rather than the
          // English. Both are deliberate: meaning comes from the picture, so
          // the caption is free to teach the second fact a learner needs about
          // a noun. Every plural here is the one in words.de.json — Papier and
          // Uhr have none recorded, so they say nothing rather than guess.
          items: [
            { label: "der Tisch", caption: "die Tische", img: "/materials/german/a1-1/photos/tisch.jpg", assetId: "sample-tisch" },
            { label: "das Buch", caption: "die Bücher", img: "/materials/german/a1-1/photos/buch.jpg", assetId: "sample-buch" },
            { label: "das Papier", img: "/materials/german/a1-1/photos/papier.jpg", assetId: "sample-papier" },
            { label: "die Uhr", img: "/materials/german/a1-1/photos/uhr.jpg", assetId: "sample-uhr" },
            { label: "der Kurs", caption: "die Kurse", img: "/materials/german/a1-1/photos/kurs.jpg", assetId: "sample-kurs" },
            { label: "die Aufgabe", caption: "die Aufgaben", img: "/materials/german/a1-1/photos/aufgabe.jpg", assetId: "sample-aufgabe" },
          ],
        },
      ],
    },
    {
      id: "s7",
      title: "Im Unterricht",
      subtitle: "Hier schreibt deine Lehrkraft.",
      blocks: [{ kind: "lines", tone: "board", count: 5 }],
    },
    {
      id: "s8",
      tab: "Übungen",
      title: "Ergänze den Artikel",
      subtitle: "Schreib der, die oder das.",
      blocks: [
        {
          kind: "exercise",
          skillId: "german.a1-1.classroom.definite-article",
          rows: [
            { prompt: "___ Tisch ist neu.", answer: "Der", hint: "der · die · das" },
            { prompt: "___ Buch ist neu.", answer: "Das" },
            { prompt: "___ Uhr ist neu.", answer: "Die" },
            { prompt: "___ Kurs ist neu.", answer: "Der" },
            { prompt: "___ Aufgabe ist neu.", answer: "Die" },
            { prompt: "___ Papier ist neu.", answer: "Das" },
          ],
        },
      ],
    },
    {
      id: "s9",
      tab: "Übungen",
      title: "Kreuze an",
      subtitle: "Welcher Artikel ist richtig?",
      blocks: [
        {
          kind: "choose",
          rows: [
            { prompt: "___ Tisch", options: ["der", "die", "das"], answer: "der" },
            { prompt: "___ Aufgabe", options: ["der", "die", "das"], answer: "die" },
            { prompt: "___ Papier", options: ["der", "die", "das"], answer: "das" },
            { prompt: "___ Kurs", options: ["der", "die", "das"], answer: "der" },
          ],
        },
      ],
    },
    {
      id: "s10",
      tab: "Übungen",
      title: "Bilde Sätze",
      subtitle: "Schreib den Satz richtig auf.",
      blocks: [
        {
          kind: "build",
          rows: [
            { parts: ["ist", "der", "neu", "Tisch"], answer: "Der Tisch ist neu." },
            { parts: ["Buch", "das", "hier", "ist"], answer: "Das Buch ist hier." },
            { parts: ["Aufgabe", "die", "leicht", "ist"], answer: "Die Aufgabe ist leicht." },
          ],
        },
      ],
    },
    {
      id: "s11",
      title: "An der Tür",
      subtitle: "Lies den Dialog. Ergänze dann die Sätze unten.",
      blocks: [
        {
          kind: "dialogue",
          scene: "08:15 · vor dem Kursraum",
          lines: [
            { who: "Herr Klein", says: "Guten Morgen!" },
            { who: "Amal", says: "Guten Morgen, Herr Klein." },
            { who: "Herr Klein", says: "Bis morgen, Amal!" },
            { who: "Amal", says: "Auf Wiedersehen!" },
          ],
        },
        {
          kind: "cards",
          cols: 3,
          items: [
            { label: "___ Morgen!", answer: "Guten" },
            { label: "___ Wiedersehen!", answer: "Auf" },
            { label: "Bis ___!", answer: "morgen" },
          ],
        },
      ],
    },
    {
      id: "s12",
      title: "Frage und antworte",
      subtitle: "Nimm ein Wort. Frage deine Partnerin oder deinen Partner.",
      blocks: [
        {
          kind: "bubbles",
          numbered: true,
          turns: [
            { side: "l", text: "Ist das der Tisch?" },
            { side: "r", text: "Ja, genau. Der Tisch." },
            { side: "l", text: "Und das hier? Ist das das Buch?" },
            { side: "r", text: "Ja, genau. Das Buch." },
          ],
        },
      ],
      note: { title: "Extra", text: "Sag auch den Plural: die Tische · die Bücher." },
    },
    {
      id: "s13",
      title: "Im Unterricht",
      subtitle: "Noch einmal Platz für die Lehrkraft.",
      blocks: [{ kind: "lines", tone: "board", count: 5 }],
    },
    {
      id: "s14",
      title: "Über die Lernziele nachdenken",
      subtitle: "Kreuze an und schreib eine Notiz.",
      blocks: [
        {
          kind: "goals",
          items: [
            "Kannst du morgens, mittags und abends grüßen?",
            "Kannst du dich verabschieden?",
            "Kannst du der, die und das richtig benutzen?",
          ],
        },
        { kind: "lines", label: "Was mache ich nächste Woche besser?", count: 3 },
      ],
    },
    {
      id: "s15",
      title: "Wortschatz",
      subtitle: "Nomen · Redemittel",
      blocks: [
        {
          kind: "list",
          cols: 2,
          // No translations. A noun's gloss is its plural — the second fact a
          // learner needs about it — and a phrase's gloss is when to use it.
          // Every plural here is the one in words.de.json; Papier and Uhr have
          // none recorded, so they say nothing rather than guess.
          items: [
            { term: "der Tisch", gloss: "die Tische" },
            { term: "Hallo", gloss: "immer · informell" },
            { term: "das Buch", gloss: "die Bücher" },
            { term: "Guten Morgen", gloss: "bis etwa 11:00" },
            { term: "das Papier" },
            { term: "Guten Tag", gloss: "11:00–18:00" },
            { term: "die Uhr" },
            { term: "Guten Abend", gloss: "ab etwa 18:00" },
            { term: "der Kurs", gloss: "die Kurse" },
            { term: "Gute Nacht", gloss: "vor dem Schlafen" },
            { term: "die Aufgabe", gloss: "die Aufgaben" },
            { term: "Auf Wiedersehen", gloss: "beim Gehen · formell" },
          ],
        },
      ],
    },
    {
      id: "s16",
      title: "Notizen",
      subtitle: "Neue Wörter, Fragen, Hausaufgaben.",
      blocks: [{ kind: "lines", count: 9 }],
    },
    {
      id: "s17",
      title: "Ende der Stunde",
      tone: "violet",
      blocks: [
        {
          kind: "hero",
          glyph: "Guten Tag",
          label: "Redewendung",
          sub: "Der Gruß, der immer passt.",
        },
        {
          kind: "rows",
          items: [
            { head: "Bedeutung", body: "höflich, sicher, zu jeder Tageszeit zwischen 11 und 18 Uhr" },
            { head: "Beispiel", body: "Guten Tag, Frau Klein. Ich bin Amal." },
          ],
        },
      ],
    },
  ],
} as const;
