/**
 * What each subject actually teaches, so a learner books a specific chapter
 * rather than an unlabelled hour.
 *
 * Chapter and lesson titles are deliberately not translated — like the chalk
 * lines in `subjects.ts`, they are course content rather than interface text.
 * This is a starting syllabus and is meant to be replaced by the real one.
 */
import { FR_MATHS_LEVELS } from "@/lib/curriculum/frMaths";

export type Lesson = {
  id: string;
  title: string;
  /** "Vocabulary", "Grammar", "Practice" — shown above the lesson title. */
  category?: string;
  summary?: string;
  /** What the learner will be able to do afterwards. */
  objectives?: string[];
  /**
   * Path to the lesson's handout, relative to `public` — e.g.
   * "/materials/english/a1-hello.pdf". Lessons without one simply show no
   * material button.
   */
  material?: string;
};

export type Chapter = {
  id: string;
  /** A can-do statement for languages, a topic for sciences. */
  title: string;
  /** A single emoji for the chapter, shown as its badge in the lists. */
  emoji?: string;
  lessons: Lesson[];
};

export type Level = {
  id: string;
  label: string;
  /**
   * The syllabus this level belongs to. A subject taught to more than one —
   * maths runs both the French programme and the US Pre-K–8 grades — shows a
   * row of programme buttons above its level menu; a subject on a single
   * ladder leaves this out and shows none.
   *
   * Not translated: these are the programmes' own names.
   */
  programme?: string;
  /**
   * The heading this level sits under inside its programme — "Collège",
   * "Lycée". Levels without one are listed flat.
   */
  group?: string;
  /**
   * BCP-47 tag for the language this level's programme is taught in, when that
   * is not the subject's own. The French maths programme is taught in French
   * whatever language the interface is in, and this is what tells the call
   * screen to speak it that way. Languages leave it out — the subject already
   * says what they are spoken in.
   */
  locale?: string;
  chapters: Chapter[];
};

/**
 * Lessons are written as bare titles for brevity; anything richer — a
 * category, objectives, a PDF — is passed as an object instead.
 */
const ch = (
  id: string,
  title: string,
  lessons: (string | Lesson)[],
  emoji?: string,
): Chapter => ({
  id,
  title,
  emoji,
  lessons: lessons.map((lesson, i) =>
    typeof lesson === "string" ? { id: `l${i + 1}`, title: lesson } : lesson,
  ),
});

/**
 * A Pre-K–8 unit. Those grades are listed as units rather than as lessons
 * inside units, so the unit is both the chapter a learner books and the single
 * lesson inside it.
 */
const unit = (id: string, title: string, emoji?: string): Chapter =>
  ch(id, title, [title], emoji);

/**
 * A German A1.1 lesson written out in full: the material agent's spec is built
 * from `summary` and `objectives`, so neither may be left empty.
 */
const l = (
  n: 1 | 2 | 3,
  category: "Vocabulary" | "Communication" | "Grammar",
  title: string,
  summary: string,
  objectives: string[],
): Lesson => ({ id: `l${n}`, title, category, summary, objectives });

/** A1.2 chapters run vocabulary, then grammar, then the practice that uses it. */
const vgc = (vocabulary: string, grammar: string, communication: string): Lesson[] => [
  { id: "l1", title: vocabulary, category: "Vocabulary" },
  { id: "l2", title: grammar, category: "Grammar" },
  { id: "l3", title: communication, category: "Communication" },
];

/** The two syllabuses maths is taught to, named once and reused per level. */
const FR = "Programme français (cours et exercices par niveau)";
const US = "Math: Pre-K – 8th grade";
const HS = "Math: High school & College";

export const CURRICULUM: Record<string, Level[]> = {
  english: [
    { id: "a1-1", label: "A1.1 — Beginner", chapters: [
      ch("intro", "I can introduce myself", [
        { id: "l1", title: "Introduce yourself!", category: "Vocabulary" },
        { id: "l2", title: "Making friends", category: "Communication" },
        { id: "l3", title: "Personal pronouns", category: "Grammar" },
        { id: "l4", title: "Hi! My name is Kim!", category: "Reading" },
      ], "👋"),
      ch("classroom", "I can survive in an English classroom", [
        { id: "l1", title: "Useful phrases", category: "Vocabulary" },
        { id: "l2", title: "Let's spell!", category: "Communication" },
        { id: "l3", title: "The verb 'to be'", category: "Grammar" },
        { id: "l4", title: "Talking about yourself", category: "Speaking" },
      ], "🎒"),
      ch("origins", "I can say where I'm from", [
        { id: "l1", title: "Countries and nationalities", category: "Vocabulary" },
        { id: "l2", title: "Contractions and apostrophes", category: "Communication" },
        { id: "l3", title: "Plural nouns", category: "Grammar" },
        { id: "l4", title: "We like sports!", category: "Reading" },
      ], "🌍"),
      ch("city", "I can talk about where I live", [
        { id: "l1", title: "The big city", category: "Vocabulary" },
        { id: "l2", title: "Count to 20!", category: "Communication" },
        { id: "l3", title: "The present simple", category: "Grammar" },
        { id: "l4", title: "Talking about where you are from", category: "Speaking" },
      ], "🏙️"),
      ch("family", "I can talk about my family", [
        { id: "l1", title: "This is my family", category: "Vocabulary" },
        { id: "l2", title: "My family is big", category: "Communication" },
        { id: "l3", title: "Possessive determiners", category: "Grammar" },
        { id: "l4", title: "Meet our family", category: "Reading" },
      ], "👪"),
      ch("details", "I can ask for and give personal details", [
        { id: "l1", title: "Descriptive adjectives", category: "Vocabulary" },
        { id: "l2", title: "How tall are you?", category: "Communication" },
        { id: "l3", title: "Simple wh- questions", category: "Grammar" },
        { id: "l4", title: "Talking about my family", category: "Speaking" },
      ], "📇"),
      ch("routine", "I can talk about my routine", [
        { id: "l1", title: "What day is it?", category: "Vocabulary" },
        { id: "l2", title: "What time is it?", category: "Communication" },
        { id: "l3", title: "Wh- question words", category: "Grammar" },
        { id: "l4", title: "I love weekends!", category: "Reading" },
      ], "⏰"),
      ch("transport", "I can talk about forms of transport", [
        { id: "l1", title: "Transport and mobility", category: "Vocabulary" },
        { id: "l2", title: "Do-questions and negative questions", category: "Communication" },
        { id: "l3", title: "Adverbs of time", category: "Grammar" },
        { id: "l4", title: "Talking about my daily routine", category: "Speaking" },
      ], "🚌"),
      ch("weather", "I can talk about the weather and seasons", [
        { id: "l1", title: "Weather", category: "Vocabulary" },
        { id: "l2", title: "Months and seasons of the year", category: "Communication" },
        { id: "l3", title: "Negation with 'not'", category: "Grammar" },
        { id: "l4", title: "I'm going to build a snowman!", category: "Reading" },
      ], "🌦️"),
      ch("hobbies", "I can talk about sports and hobbies", [
        { id: "l1", title: "Hobbies", category: "Vocabulary" },
        { id: "l2", title: "I like sports!", category: "Communication" },
        { id: "l3", title: "All about negation", category: "Grammar" },
        { id: "l4", title: "Talking about the weather", category: "Speaking" },
      ], "⚽"),
      ch("supermarket", "I can buy food at the supermarket", [
        { id: "l1", title: "At the supermarket", category: "Vocabulary" },
        { id: "l2", title: "Making a grocery list", category: "Communication" },
        { id: "l3", title: "The present continuous: part I", category: "Grammar" },
        { id: "l4", title: "Food Fight", category: "Reading" },
      ], "🛒"),
      ch("food", "I can talk about the food I like and don't like", [
        { id: "l1", title: "I'm hungry", category: "Vocabulary" },
        { id: "l2", title: "Let's eat!", category: "Communication" },
        { id: "l3", title: "The present continuous: part II", category: "Grammar" },
        { id: "l4", title: "Talking about food", category: "Speaking" },
      ], "🍽️"),
      ch("level-check", "Level check English A1.1", [
        { id: "l1", title: "My first piece of writing in English", category: "Level check" },
      ], "✅"),
    ]},
    { id: "a1-2", label: "A1.2 — Beginner", chapters: [
      ch("work", "I can say what I do for work", [
        { id: "l1", title: "At work", category: "Vocabulary" },
        { id: "l2", title: "Writing a to-do list", category: "Communication" },
        { id: "l3", title: "The present simple vs the present continuous", category: "Grammar" },
        { id: "l4", title: "Steve loves his job", category: "Reading" },
      ], "💼"),
      ch("office", "I can have a simple conversation at the office", [
        { id: "l1", title: "Communication", category: "Vocabulary" },
        { id: "l2", title: "Writing a text message", category: "Communication" },
        { id: "l3", title: "Object pronouns", category: "Grammar" },
        { id: "l4", title: "Talking about work", category: "Speaking" },
      ], "🗂️"),
      ch("house", "I can talk about my house", [
        { id: "l1", title: "My house", category: "Vocabulary" },
        { id: "l2", title: "Come on over!", category: "Communication" },
        { id: "l3", title: "The comparative of adjectives", category: "Grammar" },
        { id: "l4", title: "A day off at home", category: "Reading" },
      ], "🏠"),
      ch("room", "I can describe a room in my home", [
        { id: "l1", title: "Furniture", category: "Vocabulary" },
        { id: "l2", title: "That was then, this is now!", category: "Communication" },
        { id: "l3", title: "The superlative of adjectives", category: "Grammar" },
        { id: "l4", title: "Talking about where I live", category: "Speaking" },
      ], "🛋️"),
      ch("doctor", "I can go to the doctor", [
        { id: "l1", title: "My health", category: "Vocabulary" },
        { id: "l2", title: "Going to the doctor", category: "Communication" },
        { id: "l3", title: "'Can' and 'can't'", category: "Grammar" },
        { id: "l4", title: "Staying healthy", category: "Reading" },
      ], "🩺"),
      ch("feelings", "I can talk about how I'm feeling", [
        { id: "l1", title: "My body", category: "Vocabulary" },
        { id: "l2", title: "I feel great!", category: "Communication" },
        { id: "l3", title: "'Should' and 'could'", category: "Grammar" },
        { id: "l4", title: "Talking about your health", category: "Speaking" },
      ], "😊"),
      ch("clothes", "I can describe an item of clothing", [
        { id: "l1", title: "Clothes", category: "Vocabulary" },
        { id: "l2", title: "Green shirt, blue jeans!", category: "Communication" },
        { id: "l3", title: "Expressing possession", category: "Grammar" },
        { id: "l4", title: "Clothes shopping", category: "Reading" },
      ], "👕"),
      ch("shopping", "I can go clothes shopping", [
        { id: "l1", title: "Shopping", category: "Vocabulary" },
        { id: "l2", title: "At the mall", category: "Communication" },
        { id: "l3", title: "Forming different types of questions", category: "Grammar" },
        { id: "l4", title: "Talking about shopping", category: "Speaking" },
      ], "🛍️"),
      ch("travel", "I can talk about travel", [
        { id: "l1", title: "Travel", category: "Vocabulary" },
        { id: "l2", title: "Writing a postcard", category: "Communication" },
        { id: "l3", title: "The past simple: 'to be' and 'to have'", category: "Grammar" },
        { id: "l4", title: "Getting ready for a trip", category: "Reading" },
      ], "✈️"),
      ch("directions", "I can ask for and give directions", [
        { id: "l1", title: "Giving directions", category: "Vocabulary" },
        { id: "l2", title: "Learn the imperative", category: "Communication" },
        { id: "l3", title: "The past simple: regular verbs", category: "Grammar" },
        { id: "l4", title: "Talking about holidays", category: "Speaking" },
      ], "🧭"),
      ch("celebrations", "I can talk about celebrations", [
        { id: "l1", title: "Holidays", category: "Vocabulary" },
        { id: "l2", title: "Celebrations", category: "Communication" },
        { id: "l3", title: "The past simple: common irregular verbs", category: "Grammar" },
        { id: "l4", title: "Getting ready to celebrate", category: "Reading" },
      ], "🎉"),
      ch("invitations", "I can invite someone to an event", [
        { id: "l1", title: "Writing an invitation", category: "Communication" },
        { id: "l2", title: "Let's party!", category: "Communication" },
        { id: "l3", title: "Asking questions with the present and simple past", category: "Grammar" },
        { id: "l4", title: "Talking about parties", category: "Speaking" },
      ], "💌"),
      ch("level-check", "Level check English A1.2", [
        { id: "l1", title: "Real writing: level check", category: "Level check" },
        { id: "l2", title: "Real conversation: level check", category: "Level check" },
      ], "✅"),
    ]},
    { id: "a2-1", label: "A2.1 — Elementary", chapters: [
      ch("relationships", "I can talk about relationships", [
        { id: "l1", title: "Friends and family", category: "Vocabulary" },
        { id: "l2", title: "My favourite place", category: "Communication" },
        { id: "l3", title: "Prepositions of place and time", category: "Grammar" },
        { id: "l4", title: "Can you introduce me to your friend?", category: "Reading" },
      ], "🤝"),
      ch("restaurant", "I can order at a restaurant", [
        { id: "l1", title: "Going out in my city", category: "Vocabulary" },
        { id: "l2", title: "At a restaurant", category: "Communication" },
        { id: "l3", title: "Reviewing the present tense", category: "Grammar" },
        { id: "l4", title: "A conversation about my city", category: "Speaking" },
      ], "🍝"),
      ch("phone", "I can answer a phone call at work", [
        { id: "l1", title: "A lot of work!", category: "Vocabulary" },
        { id: "l2", title: "On the phone", category: "Communication" },
        { id: "l3", title: "Reviewing wh- and yes/no questions", category: "Grammar" },
        { id: "l4", title: "A meeting with the boss", category: "Reading" },
      ], "📞"),
      ch("jobs", "I can talk about jobs", [
        { id: "l1", title: "Looking for a job", category: "Vocabulary" },
        { id: "l2", title: "Verbs for work", category: "Communication" },
        { id: "l3", title: "More prepositions of time", category: "Grammar" },
        { id: "l4", title: "A conversation about work", category: "Speaking" },
      ], "🧑‍💼"),
      ch("moving", "I can look for a new place to live", [
        { id: "l1", title: "We are moving out!", category: "Vocabulary" },
        { id: "l2", title: "I'm looking for a place", category: "Communication" },
        { id: "l3", title: "Reviewing the past simple", category: "Grammar" },
        { id: "l4", title: "It's moving day", category: "Reading" },
      ], "📦"),
      ch("home", "I can describe my home", [
        { id: "l1", title: "My new house", category: "Vocabulary" },
        { id: "l2", title: "I prefer my new house", category: "Communication" },
        { id: "l3", title: "Verb patterns for expressing preferences", category: "Grammar" },
        { id: "l4", title: "A conversation about my new house", category: "Speaking" },
      ], "🛏️"),
      ch("films", "I can talk about films", [
        { id: "l1", title: "All about films", category: "Vocabulary" },
        { id: "l2", title: "My favourite film", category: "Communication" },
        { id: "l3", title: "Using possessive pronouns", category: "Grammar" },
        { id: "l4", title: "I like science fiction films!", category: "Reading" },
      ], "🎬"),
      ch("culture", "I can suggest things to do in my city", [
        { id: "l1", title: "Culture in my city", category: "Vocabulary" },
        { id: "l2", title: "Suggesting an activity", category: "Communication" },
        { id: "l3", title: "Irregular verbs in the simple past", category: "Grammar" },
        { id: "l4", title: "A conversation about films and culture", category: "Speaking" },
      ], "🎭"),
      ch("hobbies", "I can talk about hobbies", [
        { id: "l1", title: "Sports and games", category: "Vocabulary" },
        { id: "l2", title: "I have lots of hobbies", category: "Communication" },
        { id: "l3", title: "Past continuous", category: "Grammar" },
        { id: "l4", title: "Let's get some exercise!", category: "Reading" },
      ], "🏸"),
      ch("fitness", "I can explain how to stay fit", [
        { id: "l1", title: "Staying fit", category: "Vocabulary" },
        { id: "l2", title: "Could you help me with this?", category: "Communication" },
        { id: "l3", title: "Modals of obligation", category: "Grammar" },
        { id: "l4", title: "A conversation about sports", category: "Speaking" },
      ], "🏋️"),
      ch("plans", "I can make plans", [
        { id: "l1", title: "Making plans", category: "Vocabulary" },
        { id: "l2", title: "I am looking forward to that!", category: "Communication" },
        { id: "l3", title: "Future simple", category: "Grammar" },
        { id: "l4", title: "See you this weekend!", category: "Reading" },
      ], "📅"),
      ch("future", "I can talk about my goals for the future", [
        { id: "l1", title: "Talking about the future", category: "Vocabulary" },
        { id: "l2", title: "My goals in life", category: "Communication" },
        { id: "l3", title: "Future with 'be going to'", category: "Grammar" },
        { id: "l4", title: "A conversation about the future", category: "Speaking" },
      ], "🎯"),
      ch("level-check", "Level check English A2.1", [
        { id: "l1", title: "Writing a letter", category: "Level check" },
      ], "✅"),
    ]},
    { id: "a2-2", label: "A2.2 — Elementary", chapters: [] },
    { id: "b1-1", label: "B1.1 — Intermediate", chapters: [
      ch("past", "I can tell a story about my past", ["Past simple and continuous", "Used to and would", "Check: telling a story"]),
      ch("plans", "I can talk about future plans", ["Will, going to, present continuous", "First conditional", "Check: making arrangements"]),
      ch("opinion", "I can give and defend an opinion", ["Agreeing and disagreeing", "Linking arguments", "Check: a short debate"]),
    ]},
    { id: "b1-2", label: "B1.2 — Intermediate", chapters: [] },
    { id: "b2-1", label: "B2.1 — Upper intermediate", chapters: [
      ch("narrative", "I can tell a detailed story", ["Past perfect and narrative tenses", "Reported speech", "Check: retelling a news story"]),
      ch("hypothetical", "I can talk about unreal situations", ["Second and third conditionals", "Wish and if only", "Check: regrets and what-ifs"]),
      ch("register", "I can adapt how formal I sound", ["The passive in reports", "Hedging and softening", "Check: a formal email"]),
    ]},
    { id: "b2-2", label: "B2.2 — Upper intermediate", chapters: [] },
    { id: "c1-1", label: "C1.1 — Advanced", chapters: [
      ch("nuance", "I can express fine shades of meaning", ["Inversion for emphasis", "Cleft sentences", "Check: rewriting for emphasis"]),
      ch("idiom", "I can use idiom and collocation naturally", ["Phrasal verbs in context", "Collocation and connotation", "Check: sounding natural"]),
      ch("argue", "I can build and defend a long argument", ["Discourse markers", "Concession and counter-argument", "Check: a structured debate"]),
    ]},
    { id: "c1-2", label: "C1.2 — Advanced", chapters: [] },
  ],
  french: [
    { id: "a1-1", label: "A1.1 — Débutant", chapters: [
      ch("intro", "I can introduce myself in French", ["Se présenter", "Les articles définis", "Check: se présenter"]),
      ch("family", "I can describe my family", ["Les possessifs", "Les adjectifs", "Check: parler de sa famille"]),
      ch("city", "I can find my way around a city", ["Demander son chemin", "Les prépositions de lieu", "Check: s'orienter"]),
    ]},
    { id: "a1-2", label: "A1.2 — Débutant", chapters: [] },
    { id: "a2-1", label: "A2.1 — Élémentaire", chapters: [
      ch("weekend", "I can talk about last weekend", ["Le passé composé", "Les marqueurs de temps", "Check: raconter son week-end"]),
      ch("shop", "I can shop and ask for prices", ["Les partitifs et les quantités", "Les nombres et les prix", "Check: faire ses courses"]),
      ch("plans", "I can say what I am going to do", ["Le futur proche", "Les pronoms COD et COI", "Check: prendre rendez-vous"]),
    ]},
    { id: "a2-2", label: "A2.2 — Élémentaire", chapters: [] },
    { id: "b1-1", label: "B1.1 — Intermédiaire", chapters: [
      ch("past", "I can talk about the past", ["Passé composé et imparfait", "Les accords du participe", "Check: raconter un souvenir"]),
      ch("subj", "I can express necessity and doubt", ["Le subjonctif présent", "Les expressions déclencheuses", "Check: donner un conseil"]),
      ch("opinion", "I can argue a point of view", ["Les connecteurs logiques", "Nuancer son propos", "Check: un court débat"]),
    ]},
    { id: "b1-2", label: "B1.2 — Intermédiaire", chapters: [] },
    { id: "b2-1", label: "B2.1 — Intermédiaire supérieur", chapters: [
      ch("narrative", "I can tell a detailed story", ["Le plus-que-parfait", "Le discours indirect", "Check: rapporter un récit"]),
      ch("hypo", "I can talk about unreal situations", ["Le conditionnel passé", "Les phrases avec si", "Check: exprimer un regret"]),
      ch("formal", "I can write in a formal register", ["La voix passive", "La nominalisation", "Check: une lettre formelle"]),
    ]},
    { id: "b2-2", label: "B2.2 — Intermédiaire supérieur", chapters: [] },
    { id: "c1-1", label: "C1.1 — Avancé", chapters: [
      ch("nuance", "I can express fine shades of meaning", ["Le subjonctif passé", "La concession : bien que, quoique", "Check: nuancer un avis"]),
      ch("style", "I can vary my style and register", ["Le participe présent et le gérondif", "Les registres de langue", "Check: réécrire un texte"]),
      ch("debate", "I can build and defend a long argument", ["L'argumentation écrite", "Réfuter et concéder", "Check: un débat structuré"]),
    ]},
    { id: "c1-2", label: "C1.2 — Avancé", chapters: [] },
  ],
  spanish: [
    { id: "a1-1", label: "A1.1 — Principiante", chapters: [
      ch("intro", "I can introduce myself in Spanish", ["Saludos y presentaciones", "Ser y estar", "Check: presentarse"]),
      ch("routine", "I can describe my routine", ["Presente regular", "Verbos reflexivos", "Check: un día normal"]),
      ch("shop", "I can shop and ask prices", ["Números y precios", "Los demostrativos", "Check: en la tienda"]),
    ]},
    { id: "a1-2", label: "A1.2 — Principiante", chapters: [] },
    { id: "a2-1", label: "A2.1 — Elemental", chapters: [
      ch("weekend", "I can talk about last weekend", ["Pretérito indefinido", "Marcadores temporales", "Check: contar el fin de semana"]),
      ch("house", "I can describe where I live", ["Hay, estar y ser", "Los posesivos", "Check: describir tu casa"]),
      ch("plans", "I can make plans", ["Ir a + infinitivo", "Quedar y proponer planes", "Check: quedar con un amigo"]),
    ]},
    { id: "a2-2", label: "A2.2 — Elemental", chapters: [] },
    { id: "b1-1", label: "B1.1 — Intermedio", chapters: [
      ch("past", "I can narrate past events", ["Indefinido e imperfecto", "Marcadores temporales", "Check: contar un viaje"]),
      ch("subj", "I can express wishes and doubt", ["Presente de subjuntivo", "Ojalá y espero que", "Check: dar consejos"]),
      ch("cond", "I can talk about hypotheses", ["Condicional simple", "Si + imperfecto de subjuntivo", "Check: qué harías si"]),
    ]},
    { id: "b1-2", label: "B1.2 — Intermedio", chapters: [] },
    { id: "b2-1", label: "B2.1 — Intermedio alto", chapters: [
      ch("perfect", "I can link the past to the present", ["Perfecto y pluscuamperfecto", "Estilo indirecto", "Check: contar una noticia"]),
      ch("emotion", "I can react and express emotion", ["Subjuntivo con verbos de emoción", "Indicativo o subjuntivo", "Check: reaccionar a una noticia"]),
      ch("formal", "I can write in a formal register", ["La pasiva y la pasiva refleja", "Conectores del discurso", "Check: un correo formal"]),
    ]},
    { id: "b2-2", label: "B2.2 — Intermedio alto", chapters: [] },
    { id: "c1-1", label: "C1.1 — Avanzado", chapters: [
      ch("hypo", "I can talk about unreal situations", ["Imperfecto y pluscuamperfecto de subjuntivo", "Condicional compuesto", "Check: lo que habría pasado"]),
      ch("idiom", "I can use idiom naturally", ["Perífrasis verbales", "Expresiones idiomáticas", "Check: sonar natural"]),
      ch("argue", "I can build and defend a long argument", ["Concesión y contraste", "Matizar una opinión", "Check: un debate estructurado"]),
    ]},
    { id: "c1-2", label: "C1.2 — Avanzado", chapters: [] },
  ],
  german: [
    /**
     * German A1.1 — the order, and where it comes from.
     *
     * The sequence below is not a textbook's. It is built from two free public
     * documents, and then deliberately cut a different way:
     *
     *   • the ten Themenbereiche of the Goethe-Institut A1 word list
     *     (Start Deutsch 1) — Person, Wohnen, Umwelt, Reisen/Verkehr,
     *     Essen/Trinken, Einkaufen, Dienstleistungen, Erziehung/Lernen,
     *     Arbeit/Beruf, Freizeit — plus its thirteen Wortgruppen (Zahlen,
     *     Uhrzeit, Wochentage, Monatsnamen, Farben …)
     *   • the CEFR A1 can-do descriptors, which the chapter titles restate
     *
     * The ordering rule is ours: **how soon someone newly arrived in Germany
     * actually needs it.** That is why paying for food comes fourth here rather
     * than near the end, why the job chapter waits until the tenth, and why the
     * post office, the bank and the Amt get a chapter of their own — they are a
     * Goethe theme (Dienstleistungen), not a to-do list.
     *
     * Each chapter names the theme it was drawn from, so the sequence can be
     * checked against the source rather than taken on trust. A1.1 takes half the
     * themes; A1.2 takes the rest.
     */
    { id: "a1-1", label: "A1.1 — Anfänger", chapters: [
      ch("get-started", "Getting started with German", [
        {
          id: "l1",
          title: "How this course works",
          category: "Orientation",
          summary:
            "A short first meeting: what A1.1 covers, how a lesson runs, and what you should be able to do twelve chapters from now.",
          objectives: [
            "I know what the twelve chapters of A1.1 cover.",
            "I know how a lesson is structured and what is expected of me.",
            "I can say what I want to be able to do in German.",
          ],
        },
      ], "🎒"),

      // Goethe theme: Erziehung/Ausbildung/Lernen → Sprachen lernen
      ch("classroom", "I can follow my first German lesson", [
        l(1, "Vocabulary", "Hello and goodbye",
          "The greetings that change with the clock, and the two ways to leave a room.",
          [
            "I can greet someone in German at any time of day.",
            "I can say goodbye at the end of a class.",
            "I can tell when to use du and when to use Sie.",
          ]),
        l(2, "Communication", "Spelling my name out loud",
          "The German alphabet, and the handful of phrases that keep a lesson moving when you have not understood.",
          [
            "I can spell my name letter by letter.",
            "I can ask someone to repeat something, or to speak more slowly.",
            "I can ask what a word means and how it is written.",
          ]),
        l(3, "Grammar", "der, die, das",
          "Every German noun carries a gender. This lesson is about learning the article together with the word, from the first day.",
          [
            "I can name the three genders of German nouns.",
            "I can use der, die and das with the nouns from this chapter.",
            "I can write down a new noun the way it needs to be learned — with its article and its plural.",
          ]),
      ], "👋"),

      // Goethe theme: Person → Name · Herkunft · Staatsangehörigkeit
      ch("myself", "I can tell someone my name and where I'm from", [
        l(1, "Vocabulary", "Countries, cities and nationalities",
          "The country you come from, the city you live in, and the languages you speak.",
          [
            "I can name my country and my nationality in German.",
            "I can say which languages I speak.",
            "I can understand where someone else is from.",
          ]),
        l(2, "Communication", "Introducing myself",
          "Four sentences that will introduce you for the rest of your life in German, and the questions that draw them out of someone else.",
          [
            "I can introduce myself with my name, my country and my city.",
            "I can ask someone their name and where they come from.",
            "I can introduce a third person.",
          ]),
        l(3, "Grammar", "Regular verbs in the present",
          "One stem, six endings. Once this pattern is in place, most German verbs follow it.",
          [
            "I can conjugate a regular verb in the present tense.",
            "I can match the right ending to ich, du, er/sie, wir, ihr and sie/Sie.",
            "I can build a simple sentence about myself with a regular verb.",
          ]),
      ], "🙋"),

      // Goethe: Wortgruppe Zahlen · Person → Adresse, Telefon, Alter
      ch("numbers", "I can give my phone number, my address and my age", [
        l(1, "Vocabulary", "Numbers from zero to a hundred",
          "Counting, and the trick that makes German numbers hard to hear: the units are said before the tens.",
          [
            "I can count from zero to a hundred.",
            "I can understand a number said out loud at normal speed.",
            "I can say my age and my year of birth.",
          ]),
        l(2, "Communication", "Filling in a form",
          "Surname, first name, date of birth, postcode. The fields that appear on every German form, and how to dictate them over a counter.",
          [
            "I can give my address, my postcode and my phone number.",
            "I can understand the labels on a simple German form.",
            "I can ask someone to repeat a number.",
          ]),
        l(3, "Grammar", "sein and haben",
          "The two verbs that refuse to follow the pattern, and the two you need most.",
          [
            "I can conjugate sein and haben in the present tense.",
            "I can say how old I am and what I have.",
            "I can tell the difference between where sein is used and where haben is.",
          ]),
      ], "🔢"),

      // Goethe theme: Einkaufen/Gebrauchsartikel → Geschäfte · Preis/Bezahlen
      ch("shopping", "I can buy food and pay for it", [
        l(1, "Vocabulary", "Food, drink, and the shops that sell them",
          "What is sold at the bakery, the butcher and the supermarket, and the words for weights and packets.",
          [
            "I can name the everyday foods I buy each week.",
            "I can say which shop sells what.",
            "I can use the German words for a kilo, a pound and a packet.",
          ]),
        l(2, "Communication", "At the till",
          "Asking for a quantity, hearing a price, and paying without slowing the queue down.",
          [
            "I can ask for an amount of something.",
            "I can ask what something costs and understand the answer.",
            "I can say whether I am paying in cash or by card.",
          ]),
        l(3, "Grammar", "The accusative",
          "When a noun is the thing being bought, eaten or taken, der becomes den. This is the first case change in the course.",
          [
            "I can explain what the accusative marks in a sentence.",
            "I can use den, die, das and einen, eine, ein after verbs like kaufen and nehmen.",
            "I can spot the one article that actually changes.",
          ]),
      ], "🛒"),

      // Goethe theme: Essen/Trinken → Lokale · Speisen · Getränke
      ch("eating", "I can order in a café and read a menu", [
        l(1, "Vocabulary", "On the menu",
          "Breakfast, cake and the drinks list — enough of a Speisekarte to order from without pointing.",
          [
            "I can read a simple German menu.",
            "I can name what I usually eat and drink.",
            "I can say what I do not eat.",
          ]),
        l(2, "Communication", "Ordering and paying at a table",
          "Being seated, ordering, asking for the bill, and the small politeness that goes with each.",
          [
            "I can order food and drink at a table.",
            "I can ask for the bill and say whether we are paying together or separately.",
            "I can understand what a waiter asks me.",
          ]),
        l(3, "Grammar", "Asking questions",
          "Two shapes: the ones that start with a question word, and the ones that start with the verb.",
          [
            "I can ask a yes/no question by putting the verb first.",
            "I can use wer, was, wo, wann, wie and wie viel.",
            "I can tell which of the two question shapes a sentence is using.",
          ]),
      ], "☕"),

      // Goethe: Wortgruppen Uhrzeit · Tag/Tageszeiten
      ch("clock", "I can tell someone what time it is", [
        l(1, "Vocabulary", "The 24-hour clock",
          "How Germany writes and says times officially — timetables, opening hours, appointments.",
          [
            "I can read a time written as 14:30 and say it aloud.",
            "I can name the parts of the day.",
            "I can understand opening hours on a sign.",
          ]),
        l(2, "Communication", "Asking and telling the time",
          "The everyday spoken clock, where halb drei means half past two and catches everyone out once.",
          [
            "I can ask what time it is.",
            "I can say a time using Viertel, halb and vor/nach.",
            "I can say when something opens, starts or closes.",
          ]),
        l(3, "Grammar", "Saying when: um, am, von … bis",
          "Small words that decide whether you are talking about a clock time, a day, or a stretch of time.",
          [
            "I can use um for clock times and am for days.",
            "I can give a span of time with von … bis.",
            "I can put a time expression in the right place in a sentence.",
          ]),
      ], "🕒"),

      // Goethe: Wortgruppen Woche/Wochentage · Monat/Monatsnamen · Datum · Jahreszeiten
      ch("calendar", "I can name the day, the date and the month", [
        l(1, "Vocabulary", "Days, months and seasons",
          "The seven days, the twelve months, the four seasons, and the words for yesterday, today and tomorrow.",
          [
            "I can name the days of the week and the months of the year.",
            "I can name the four seasons.",
            "I can say when something happens using heute, morgen and am Wochenende.",
          ]),
        l(2, "Communication", "Making an appointment",
          "Suggesting a time, accepting, refusing politely and moving it — by phone and in person.",
          [
            "I can suggest a day and a time for a meeting.",
            "I can accept or turn down a suggested time.",
            "I can ask to move an appointment.",
          ]),
        l(3, "Grammar", "Dates and ordinal numbers",
          "Why the first of May is der erste Mai, and how a German date changes shape depending on where it sits.",
          [
            "I can form ordinal numbers from one to thirty-one.",
            "I can say and write a full date.",
            "I can say the date of my birthday.",
          ]),
      ], "🗓️"),

      // Goethe theme: Person → Gewohnheiten/Tagesablauf
      ch("day", "I can describe an ordinary day", [
        l(1, "Vocabulary", "Verbs that come apart",
          "aufstehen, anfangen, einkaufen — the daily-routine verbs whose prefix jumps to the end of the sentence.",
          [
            "I can name the everyday actions that fill a normal day.",
            "I can recognise a separable verb from its prefix.",
            "I can send the prefix to the end of the sentence where it belongs.",
          ]),
        l(2, "Communication", "Telling someone about my day",
          "Stringing the day together in order, from waking up to going to bed, and asking someone about theirs.",
          [
            "I can describe my day in the order it happens.",
            "I can say how often I do something.",
            "I can ask someone what their day looks like.",
          ]),
        l(3, "Grammar", "The verb comes second",
          "German will move almost anything to the front of a sentence — as long as the verb stays in position two.",
          [
            "I can keep the conjugated verb in second position.",
            "I can start a sentence with a time expression without breaking it.",
            "I can order time, manner and place in a sentence.",
          ]),
      ], "⏰"),

      // Goethe theme: Reisen/Verkehr → privater und öffentlicher Verkehr
      ch("transport", "I can get across town by bus, tram and train", [
        l(1, "Vocabulary", "Buses, trams, trains and tickets",
          "The vehicles, the stops, the platforms and the machine that sells you the ticket.",
          [
            "I can name the kinds of public transport in a German city.",
            "I can understand the words on a ticket machine.",
            "I can name the parts of a station.",
          ]),
        l(2, "Communication", "At the station",
          "Buying the right ticket, finding the platform, and understanding an announcement well enough not to miss the train.",
          [
            "I can buy a ticket for a particular journey.",
            "I can ask which platform a train leaves from.",
            "I can ask whether this is the right bus or tram.",
          ]),
        l(3, "Grammar", "Prepositions that take the dative",
          "mit, zu, von, nach, aus, bei — after these, der becomes dem and die becomes der.",
          [
            "I can list the prepositions that are always followed by the dative.",
            "I can use dem, der and den with those prepositions.",
            "I can say how I travel and where I am going.",
          ]),
      ], "🚆"),

      // Goethe theme: Arbeit/Beruf → Arbeitsplatz
      ch("work", "I can say what I do for a living", [
        l(1, "Vocabulary", "Jobs and workplaces",
          "Job titles and the places they are done in — and the fact that German makes a separate word for a woman doing the job.",
          [
            "I can name common jobs in German.",
            "I can form the female version of a job title.",
            "I can say where I work.",
          ]),
        l(2, "Communication", "Talking about my working day",
          "What you do, who you do it with, and the hours — the answer to the question every new acquaintance asks.",
          [
            "I can say what my job is and what it involves.",
            "I can say what hours and days I work.",
            "I can ask someone else about their job.",
          ]),
        l(3, "Grammar", "Verbs that change their vowel",
          "sprechen becomes du sprichst, fahren becomes du fährst. A small group of very common verbs shifts its vowel for du and er/sie.",
          [
            "I can recognise the verbs that change their stem vowel.",
            "I can conjugate them correctly for du and er/sie.",
            "I can use them to talk about myself and one other person.",
          ]),
      ], "💼"),

      // Goethe theme: Freizeit/Unterhaltung → Interessen · Sport
      ch("freetime", "I can say what I like doing and what I don't", [
        l(1, "Vocabulary", "Hobbies, sport and screens",
          "What people actually do with an evening or a Sunday, from football to television.",
          [
            "I can name my hobbies in German.",
            "I can name common sports and say which I play.",
            "I can say what I do at the weekend.",
          ]),
        l(2, "Communication", "Saying what I like, and suggesting something",
          "gern, lieber and am liebsten — and how to turn a preference into an invitation.",
          [
            "I can say what I like doing using gern.",
            "I can say what I prefer.",
            "I can suggest doing something together and respond to a suggestion.",
          ]),
        l(3, "Grammar", "Saying no: nicht and kein",
          "German has two negatives and they are not interchangeable. One negates a noun, the other everything else.",
          [
            "I can choose between nicht and kein.",
            "I can put nicht in the right place in a sentence.",
            "I can say what I do not do and do not have.",
          ]),
      ], "🎨"),

      // Goethe theme: Dienstleistungen → Post · Telekommunikation · Banken · Polizei
      ch("paperwork", "I can handle the post office, the bank and a form", [
        l(1, "Vocabulary", "The counter, the form and the queue",
          "The words that appear on German official paperwork — Antrag, Formular, Schalter, Termin — and the places that hand it to you.",
          [
            "I can name the services at a post office and a bank.",
            "I can understand the common words on an official form.",
            "I can name the documents I am usually asked for.",
          ]),
        l(2, "Communication", "Asking for what I need at a counter",
          "Stating your business in one sentence, asking for help with a form, and making an appointment at an office.",
          [
            "I can say what I have come to do.",
            "I can ask for help filling in a form.",
            "I can make an appointment at an office.",
          ]),
        l(3, "Grammar", "können, müssen, dürfen",
          "The verbs for can, must and may — they take a second verb and send it, unchanged, to the end of the sentence.",
          [
            "I can conjugate können, müssen and dürfen.",
            "I can put the second verb at the end in its infinitive form.",
            "I can say what I can, must and am allowed to do.",
          ]),
      ], "📮"),

      ch("level-check", "Where I stand at the end of A1.1", [
        {
          id: "l1",
          title: "Level check",
          category: "Review",
          summary:
            "A conversation across all twelve chapters, ending with a short written record of what is solid and what to take into A1.2.",
          objectives: [
            "I can hold a short conversation drawing on all twelve chapters.",
            "I can see which chapters I still need to practise.",
            "I know what A1.2 will ask of me.",
          ],
        },
      ], "✅"),
    ]},
    { id: "a1-2", label: "A1.2 — Anfänger", chapters: [
      ch("get-started", "Get started! Welcome to the German A1.2 course", [
        { id: "l1", title: "Orientation German A1.2", category: "Orientation" },
      ], "🎒"),
      ch("home", "I can talk about my home in German",
        vgc("My home", "Possessive articles", "At the furniture store"), "🏠"),
      // The only chapter without a grammar lesson of its own.
      ch("directions", "I can ask for and give directions in German", [
        { id: "l1", title: "Where is the cinema?", category: "Vocabulary" },
        { id: "l2", title: "Giving directions", category: "Communication" },
        { id: "l3", title: "What's your stop?", category: "Communication" },
      ], "🧭"),
      ch("errands", "I can run errands in town in German",
        vgc("Shops and services in town", "Prepositions of place with the dative case", "At the post office"), "🏪"),
      ch("clothes", "I can buy a new outfit in German",
        vgc("Clothes and colours", "Welch- and dies-", "Going shopping"), "👕"),
      ch("restaurant", "I can order at a restaurant in German",
        vgc("The menu", "The past tense of 'sein' and 'haben'", "Enjoy your meal"), "🍽️"),
      ch("work", "I can communicate with my colleagues at work in German",
        vgc("My tasks at work", "Giving instructions at work using the imperative", "Writing an email at work"), "🧑‍💻"),
      ch("doctor", "I can pay a visit to the doctor in German",
        vgc("I don't feel well", "The modal verbs 'müssen', 'sollen' and 'dürfen'", "At the doctor's"), "🩺"),
      ch("accommodation", "I can book accommodation in German",
        vgc("Where are we staying?", "Expressing wishes with 'ich will' and 'ich möchte'", "Is the apartment still free?"), "🛏️"),
      ch("weather", "I can talk about the weather in German",
        vgc("The weather", "The comparative", "Being active outdoors"), "🌦️"),
      ch("holidays", "I can describe past holidays in German",
        vgc("How do you like to travel?", "The perfect tense with 'haben'", "Where did you go on holiday?"), "✈️"),
      ch("celebrations", "I can talk about celebrations and holidays in German",
        vgc("Celebrations and holidays", "The perfect tense of irregular verbs", "Tomorrow is a public holiday"), "🎉"),
      ch("party", "I can organise a party in German",
        vgc("We have to celebrate!", "Personal pronouns in the dative", "Writing an invitation"), "🥳"),
      ch("level-check", "Level check German A1.2", [
        { id: "l1", title: "Level check German A1.2", category: "Review" },
      ], "✅"),
    ]},
    { id: "a2-1", label: "A2.1 — Grundstufe", chapters: [
      ch("perfekt", "I can talk about last weekend", ["Das Perfekt", "Zeitangaben", "Check: das Wochenende erzählen"]),
      ch("dativ", "I can use the dative case", ["Dativ nach Verben und Präpositionen", "Personalpronomen im Dativ", "Check: jemandem etwas geben"]),
      ch("compare", "I can compare people and things", ["Komparativ und Superlativ", "Adjektivendungen", "Check: zwei Städte vergleichen"]),
    ]},
    { id: "a2-2", label: "A2.2 — Grundstufe", chapters: [] },
    { id: "b1-1", label: "B1.1 — Mittelstufe", chapters: [
      ch("cases", "I can use the case system with confidence", ["Dativ und Genitiv", "Wechselpräpositionen", "Check: Wegbeschreibung"]),
      ch("clauses", "I can build complex sentences", ["Nebensätze und Wortstellung", "Relativsätze", "Check: eine Geschichte"]),
      ch("konj", "I can be polite and hypothetical", ["Konjunktiv II", "Höfliche Bitten", "Check: ein Gespräch im Amt"]),
    ]},
    { id: "b1-2", label: "B1.2 — Mittelstufe", chapters: [] },
    { id: "b2-1", label: "B2.1 — Fortgeschritten", chapters: [
      ch("passiv", "I can report and describe processes", ["Passiv in allen Zeiten", "Indirekte Rede", "Check: einen Vorgang beschreiben"]),
      ch("nominal", "I can use a written, formal register", ["Nominalstil und Nominalisierung", "Partizipialattribute", "Check: ein formeller Brief"]),
      ch("konnektoren", "I can connect ideas precisely", ["Zweiteilige Konnektoren", "Kausal, konzessiv, final", "Check: eine Argumentation"]),
    ]},
    { id: "b2-2", label: "B2.2 — Fortgeschritten", chapters: [] },
    { id: "c1-1", label: "C1.1 — Oberstufe", chapters: [
      ch("konjunktiv1", "I can report speech in writing", ["Konjunktiv I", "Redewiedergabe in der Presse", "Check: eine Nachricht referieren"]),
      ch("idiom", "I can use idiom and nuance", ["Feste Wendungen", "Modalpartikeln", "Check: natürlich klingen"]),
      ch("debatte", "I can build and defend a long argument", ["Textkohärenz", "Einwände und Zugeständnisse", "Check: eine strukturierte Debatte"]),
    ]},
    { id: "c1-2", label: "C1.2 — Oberstufe", chapters: [] },
  ],
  italian: [
    { id: "a1-1", label: "A1.1 — Principiante", chapters: [
      ch("intro", "I can introduce myself in Italian", ["Saluti e presentazioni", "Essere e avere", "Check: presentarsi"]),
      ch("food", "I can order in a restaurant", ["Al ristorante", "L'articolo partitivo", "Check: ordinare un pasto"]),
      ch("routine", "I can describe my routine", ["Presente indicativo", "I verbi riflessivi", "Check: la mia giornata"]),
    ]},
    { id: "a1-2", label: "A1.2 — Principiante", chapters: [] },
    { id: "a2-1", label: "A2.1 — Elementare", chapters: [
      ch("weekend", "I can talk about last weekend", ["Il passato prossimo", "Le espressioni di tempo", "Check: raccontare il weekend"]),
      ch("city", "I can find my way around a city", ["Chiedere indicazioni", "Le preposizioni di luogo", "Check: orientarsi in città"]),
      ch("plans", "I can make plans", ["Il futuro semplice", "Proporre e accettare", "Check: prendere un appuntamento"]),
    ]},
    { id: "a2-2", label: "A2.2 — Elementare", chapters: [] },
    { id: "b1-1", label: "B1.1 — Intermedio", chapters: [
      ch("past", "I can talk about the past", ["Passato prossimo e imperfetto", "Accordo del participio", "Check: raccontare un viaggio"]),
      ch("pronouns", "I can use pronouns naturally", ["Pronomi diretti e indiretti", "Ci e ne", "Check: una conversazione"]),
      ch("subj", "I can express doubt and opinion", ["Congiuntivo presente", "Periodo ipotetico", "Check: esprimere un'opinione"]),
    ]},
    { id: "b1-2", label: "B1.2 — Intermedio", chapters: [] },
    { id: "b2-1", label: "B2.1 — Intermedio superiore", chapters: [
      ch("narrative", "I can tell a detailed story", ["Trapassato prossimo", "Discorso indiretto", "Check: riferire un racconto"]),
      ch("hypo", "I can talk about unreal situations", ["Congiuntivo imperfetto e trapassato", "Il periodo ipotetico dell'irrealtà", "Check: esprimere un rimpianto"]),
      ch("formal", "I can write in a formal register", ["La forma passiva", "I connettivi testuali", "Check: una mail formale"]),
    ]},
    { id: "b2-2", label: "B2.2 — Intermedio superiore", chapters: [] },
    { id: "c1-1", label: "C1.1 — Avanzato", chapters: [
      ch("nuance", "I can express fine shades of meaning", ["Concessive e dubitative", "Si impersonale e passivante", "Check: sfumare un'opinione"]),
      ch("idiom", "I can use idiom naturally", ["Espressioni idiomatiche", "Verbi pronominali: farcela, andarsene", "Check: sembrare naturale"]),
      ch("argue", "I can build and defend a long argument", ["L'argomentazione scritta", "Obiettare e concedere", "Check: un dibattito strutturato"]),
    ]},
    { id: "c1-2", label: "C1.2 — Avanzato", chapters: [] },
  ],
  arabic: [
    { id: "a1-1", label: "A1.1 — مبتدئ", chapters: [
      ch("script", "I can read and write the alphabet", ["الحروف والأصوات", "الحركات", "Check: قراءة كلمات بسيطة"]),
      ch("intro", "I can introduce myself in Arabic", ["التحية والتعريف بالنفس", "الجملة الاسمية", "Check: التعريف بالنفس"]),
      ch("family", "I can talk about my family", ["الضمائر والإضافة", "المفرد والجمع", "Check: عن عائلتي"]),
    ]},
    { id: "a1-2", label: "A1.2 — مبتدئ", chapters: [] },
    { id: "a2-1", label: "A2.1 — ما قبل المتوسط", chapters: [
      ch("daily", "I can describe my day", ["الفعل المضارع", "ظروف الزمان", "Check: يومي في المدرسة"]),
      ch("shop", "I can shop and ask prices", ["الأعداد والأسعار", "المذكر والمؤنث", "Check: في السوق"]),
      ch("past", "I can talk about last week", ["الفعل الماضي", "النفي بـ ما ولم", "Check: عطلة نهاية الأسبوع"]),
    ]},
    { id: "a2-2", label: "A2.2 — ما قبل المتوسط", chapters: [] },
    { id: "b1-1", label: "B1.1 — متوسط", chapters: [
      ch("verbs", "I can use verb forms with confidence", ["الفعل الماضي والمضارع", "أوزان الفعل", "Check: سرد قصة"]),
      ch("cases", "I can use case endings correctly", ["الرفع والنصب والجر", "كان وإنّ وأخواتهما", "Check: إعراب جمل"]),
      ch("opinion", "I can express an opinion", ["أدوات الربط", "التعبير عن الرأي", "Check: نقاش قصير"]),
    ]},
    { id: "b1-2", label: "B1.2 — متوسط", chapters: [] },
    { id: "b2-1", label: "B2.1 — فوق المتوسط", chapters: [
      ch("forms", "I can use the derived verb forms", ["أوزان الفعل المزيد", "المصدر واسم الفاعل", "Check: اشتقاق الكلمات"]),
      ch("passive", "I can report and describe", ["المبني للمجهول", "الجملة الشرطية", "Check: تقرير قصير"]),
      ch("style", "I can write in a formal register", ["أدوات الربط في النص", "الحال والمفعول المطلق", "Check: رسالة رسمية"]),
    ]},
    { id: "b2-2", label: "B2.2 — فوق المتوسط", chapters: [] },
    { id: "c1-1", label: "C1.1 — متقدم", chapters: [
      ch("rhetoric", "I can appreciate style and rhetoric", ["التشبيه والاستعارة", "الكناية والجناس", "Check: تحليل نص أدبي"]),
      ch("media", "I can follow the press and the media", ["لغة الصحافة", "المصطلحات السياسية والاقتصادية", "Check: تلخيص مقال"]),
      ch("debate", "I can build and defend a long argument", ["الحجاج والإقناع", "الاعتراض والتسليم", "Check: مناظرة قصيرة"]),
    ]},
    { id: "c1-2", label: "C1.2 — متقدم", chapters: [] },
  ],
  chinese: [
    { id: "a1-1", label: "A1.1 — 入门", chapters: [
      ch("pinyin", "I can read pinyin and the four tones", ["声母和韵母", "四声与变调", "Check: 朗读拼音"]),
      ch("intro", "I can introduce myself in Chinese", ["你好，我叫……", "国籍和职业", "Check: 自我介绍"]),
      ch("numbers", "I can use numbers, dates and times", ["数字与年月日", "几点了？", "Check: 说时间"]),
    ]},
    { id: "a1-2", label: "A1.2 — 入门", chapters: [] },
    { id: "a2-1", label: "A2.1 — 初级", chapters: [
      ch("family", "I can talk about my family", ["有和没有", "常用量词", "Check: 介绍我的家人"]),
      ch("shop", "I can shop and ask prices", ["多少钱？", "比较句：比", "Check: 在商店"]),
      ch("past", "I can talk about what I did", ["了 的用法", "过 表示经历", "Check: 说说昨天"]),
    ]},
    { id: "a2-2", label: "A2.2 — 初级", chapters: [] },
    { id: "b1-1", label: "B1.1 — 中级", chapters: [
      ch("directions", "I can find my way around a city", ["方位词", "怎么走？", "Check: 问路"]),
      ch("complements", "I can describe how an action goes", ["结果补语", "程度补语（得）", "Check: 描述一件事"]),
      ch("plans", "I can talk about plans and intentions", ["要、想、打算", "就 和 才", "Check: 我的计划"]),
    ]},
    { id: "b1-2", label: "B1.2 — 中级", chapters: [] },
    { id: "b2-1", label: "B2.1 — 中高级", chapters: [
      ch("ba", "I can use the 把 and 被 structures", ["把字句", "被字句", "Check: 改写句子"]),
      ch("connect", "I can link ideas in longer speech", ["虽然……但是……", "不但……而且……", "Check: 说一段话"]),
      ch("written", "I can read simple written Chinese", ["书面语与口语", "常见成语", "Check: 读一篇短文"]),
    ]},
    { id: "b2-2", label: "B2.2 — 中高级", chapters: [] },
    { id: "c1-1", label: "C1.1 — 高级", chapters: [
      ch("formal", "I can write in a formal register", ["书信与公文体", "被动句与无主句", "Check: 一封正式邮件"]),
      ch("idiom", "I can use idiom naturally", ["成语与惯用语", "歇后语", "Check: 地道表达"]),
      ch("debate", "I can build and defend a long argument", ["议论文结构", "让步与反驳", "Check: 一场辩论"]),
    ]},
    { id: "c1-2", label: "C1.2 — 高级", chapters: [] },
  ],
  korean: [
    { id: "a1-1", label: "A1.1 — 입문", chapters: [
      ch("hangul", "I can read and write Hangul", ["자음과 모음", "받침과 발음 규칙", "Check: 한글 읽기"]),
      ch("intro", "I can introduce myself in Korean", ["저는 …입니다", "은/는 과 이/가", "Check: 자기소개"]),
      ch("numbers", "I can use numbers, dates and times", ["한자어 수와 고유어 수", "몇 시예요?", "Check: 시간 말하기"]),
    ]},
    { id: "a1-2", label: "A1.2 — 입문", chapters: [] },
    { id: "a2-1", label: "A2.1 — 초급", chapters: [
      ch("day", "I can describe my day", ["-아요/어요", "을/를, 에/에서", "Check: 하루 일과"]),
      ch("past", "I can talk about what I did", ["-았어요/었어요", "시간 표현", "Check: 주말 이야기"]),
      ch("shop", "I can shop and order food", ["주세요 와 있어요", "가격 묻기", "Check: 식당에서"]),
    ]},
    { id: "a2-2", label: "A2.2 — 초급", chapters: [] },
    { id: "b1-1", label: "B1.1 — 중급", chapters: [
      ch("connect", "I can link two ideas in one sentence", ["-아서/어서, -(으)니까", "-지만, -는데", "Check: 이유 말하기"]),
      ch("honorific", "I can use polite and honorific speech", ["-(으)시-", "반말과 존댓말", "Check: 상황에 맞게 말하기"]),
      ch("plans", "I can talk about plans and intentions", ["-(으)ㄹ 거예요", "-고 싶다, -(으)려고 하다", "Check: 계획 말하기"]),
    ]},
    { id: "b1-2", label: "B1.2 — 중급", chapters: [] },
    { id: "b2-1", label: "B2.1 — 중상급", chapters: [
      ch("modifiers", "I can build longer descriptive sentences", ["관형형 -는/-(으)ㄴ/-(으)ㄹ", "간접 인용 -다고 하다", "Check: 들은 이야기 전하기"]),
      ch("passive", "I can use passives and causatives", ["피동 표현", "사동 표현", "Check: 문장 바꾸기"]),
      ch("nuance", "I can soften and qualify what I say", ["-(으)ㄹ 것 같다", "-잖아요, -더라고요", "Check: 부드럽게 말하기"]),
    ]},
    { id: "b2-2", label: "B2.2 — 중상급", chapters: [] },
    { id: "c1-1", label: "C1.1 — 고급", chapters: [
      ch("formal", "I can write in a formal register", ["문어체와 격식체", "명사형 -(으)ㅁ, -기", "Check: 격식 있는 이메일"]),
      ch("idiom", "I can use idiom naturally", ["관용 표현", "속담과 사자성어", "Check: 자연스러운 표현"]),
      ch("debate", "I can build and defend a long argument", ["논설문 구조", "반박과 양보", "Check: 토론하기"]),
    ]},
    { id: "c1-2", label: "C1.2 — 고급", chapters: [] },
  ],
  /**
   * Mathematics follows the French national programme, in its own order:
   * collège from la sixième to la troisième, then lycée from la seconde to la
   * terminale with its spécialité, complémentaire, experte and technologique
   * paths as separate levels.
   *
   * Each level is split into the programme's official domains — "Nombres et
   * calculs", "Espace et géométrie"… — and each domain lists its chapters in
   * the order they are taught, so a student picks their year and works down.
   *
   * Titles stay in French: they are the programme's own chapter names, and a
   * student following it looks for exactly those words.
   */
  mathematics: [
    // ── Collège ──────────────────────────────────────────────────────────
    // The seven levels the tutor has authored lessons for, generated from
    // the agent's own syllabus so a booking names an id it can resolve.
    ...FR_MATHS_LEVELS,

    // The technologique and complémentaire variants, which the agent's
    // syllabus does not cover. Bookable, but taught from the paper alone
    // until lessons are authored for them.
    { id: "1re-esm", programme: FR, group: "Lycée", label: "Première — enseignement scientifique et mathématique", chapters: [
      ch("esm", "Enseignement scientifique et mathématique", [
        "Automatismes",
        "Les suites",
        "Fonctions affines",
        "Second degré",
        "Fonctions exponentielles",
        "Statistiques",
        "Probabilités conditionnelles et indépendance",
      ], "📈"),
    ]},
    { id: "1re-techno", programme: FR, group: "Lycée", label: "Première technologique — enseignement commun", chapters: [
      ch("analyse", "Analyse", [
        "Automatismes — partie 1",
        "Les suites",
        "Généralités sur les fonctions",
        "Fonctions polynômes de degré 2",
        "Dérivation (sauf STI2D et STL)",
      ], "📈"),
      ch("proba", "Statistiques et probabilités", [
        "Automatismes — partie 2",
        "Statistiques",
        "Probabilités conditionnelles et indépendance",
        "Variables aléatoires",
        "Loi de Bernoulli",
      ], "🎲"),
      ch("geometrie", "Géométrie (uniquement STD2A)", [
        "Géométrie plane",
        "Géométrie dans l'espace",
      ], "📐"),
      ch("algo", "Algorithmique et programmation (sauf STD2A)", ["Algo au lycée (Python)"], "💻"),
    ]},
    { id: "1re-techno-spe", programme: FR, group: "Lycée", label: "Première technologique — spécialité STI2D et STL", chapters: [
      ch("geometrie", "Géométrie", [
        "Trigonométrie",
        "Produit scalaire",
        "Nombres complexes (uniquement STI2D)",
      ], "📐"),
      ch("analyse", "Analyse", [
        "Dérivation",
        "Primitives",
      ], "📈"),
    ]},
    { id: "tle-comp", programme: FR, group: "Lycée", label: "Terminale — mathématiques complémentaires", chapters: [
      ch("analyse", "Analyse", [
        "Les suites",
        "Limites des fonctions",
        "Dérivation",
        "Continuité des fonctions",
        "Convexité",
        "Fonction logarithme népérien",
        "Primitives et équations différentielles",
        "Calcul intégral",
      ], "📈"),
      ch("proba", "Probabilités et statistiques", [
        "Lois discrètes",
        "Lois à densité",
        "Statistiques",
      ], "🎲"),
    ]},
    { id: "tle-exp", programme: FR, group: "Lycée", label: "Terminale — mathématiques expertes", chapters: [
      ch("algebre", "Algèbre et géométrie", [
        "Nombres complexes",
        "Équations polynomiales",
      ], "✖️"),
      ch("arithmetique", "Arithmétique", [
        "Divisibilité et congruences",
        "PGCD et nombres premiers",
      ], "🧮"),
      ch("graphes", "Graphes et matrices", [
        "Matrices",
        "Graphes",
      ], "🕸️"),
    ]},
    { id: "tle-techno", programme: FR, group: "Lycée", label: "Terminale technologique — enseignement commun", chapters: [
      ch("analyse", "Analyse", [
        "Automatismes — partie 1",
        "Les suites",
        "Fonctions exponentielles",
        "Fonction logarithme décimal",
        "Fonction inverse",
      ], "📈"),
      ch("proba", "Statistiques et probabilités", [
        "Automatismes — partie 2",
        "Probabilités conditionnelles",
        "Variables aléatoires",
        "Statistiques",
      ], "🎲"),
      ch("geometrie", "Géométrie (uniquement STD2A)", [
        "Coniques",
        "Perspective centrale",
      ], "📐"),
      ch("algo", "Algorithmique et programmation (sauf STD2A)", ["Algo au lycée (Python)"], "💻"),
    ]},
    { id: "tle-techno-spe", programme: FR, group: "Lycée", label: "Terminale technologique — spécialité STI2D et STL", chapters: [
      ch("analyse", "Analyse", [
        "Intégration",
        "Fonctions exponentielles",
        "Fonction logarithme népérien",
        "Fonctions composées",
        "Équations différentielles",
      ], "📈"),
      ch("geometrie", "Géométrie (uniquement STI2D)", [
        "Nombres complexes",
      ], "📐"),
    ]},
    // ── Math: Pre-K – 8th grade ──────────────────────────────────────────
    { id: "us-prek", programme: US, label: "Pre-K", chapters: [] },
    { id: "us-k", programme: US, label: "Kindergarten", chapters: [] },
    { id: "us-1", programme: US, label: "1st grade", chapters: [] },
    { id: "us-2", programme: US, label: "2nd grade", chapters: [
      unit("add-sub-20", "Add and subtract within 20", "➕"),
      unit("place-value", "Place value", "🔢"),
      unit("add-sub-100", "Add and subtract within 100", "➕"),
      unit("add-sub-1000", "Add and subtract within 1,000", "➕"),
      unit("money-time", "Money and time", "💰"),
      unit("measurement", "Measurement", "📏"),
      unit("data", "Data", "📊"),
      unit("geometry", "Geometry", "📐"),
    ]},
    { id: "us-3", programme: US, label: "3rd grade", chapters: [
      unit("intro-multiplication", "Intro to multiplication", "✖️"),
      unit("multiply-1-digit", "1-digit multiplication", "✖️"),
      unit("add-sub-estimation", "Addition, subtraction and estimation", "➕"),
      unit("intro-division", "Intro to division", "➗"),
      unit("understand-fractions", "Understand fractions", "🍕"),
      unit("equivalent-fractions", "Equivalent fractions and comparing fractions", "🍕"),
      unit("more-mult-div", "More with multiplication and division", "✖️"),
      unit("patterns", "Arithmetic patterns and problem solving", "🧩"),
      unit("quadrilaterals", "Quadrilaterals", "📐"),
      unit("area", "Area", "🟦"),
      unit("perimeter", "Perimeter", "📏"),
      unit("time", "Time", "⏰"),
      unit("measurement", "Measurement", "⚖️"),
      unit("data", "Represent and interpret data", "📊"),
    ]},
    { id: "us-4", programme: US, label: "4th grade", chapters: [
      unit("place-value", "Place value", "🔢"),
      unit("add-sub-estimation", "Addition, subtraction and estimation", "➕"),
      unit("multiply-1-digit", "Multiply by 1-digit numbers", "✖️"),
      unit("multiply-2-digit", "Multiply by 2-digit numbers", "✖️"),
      unit("division", "Division", "➗"),
      unit("factors", "Factors, multiples and patterns", "🧩"),
      unit("equivalent-fractions", "Equivalent fractions and comparing fractions", "🍕"),
      unit("add-sub-fractions", "Add and subtract fractions", "🍕"),
      unit("multiply-fractions", "Multiply fractions", "🍕"),
      unit("understand-decimals", "Understand decimals", "🔟"),
      unit("plane-figures", "Plane figures", "📐"),
      unit("measuring-angles", "Measuring angles", "🧭"),
      unit("area-perimeter", "Area and perimeter", "📏"),
      unit("units", "Units of measurement", "⚖️"),
    ]},
    { id: "us-5", programme: US, label: "5th grade", chapters: [
      unit("decimal-place-value", "Decimal place value", "🔟"),
      unit("add-decimals", "Add decimals", "➕"),
      unit("subtract-decimals", "Subtract decimals", "➖"),
      unit("add-sub-fractions", "Add and subtract fractions", "🍕"),
      unit("multi-digit", "Multi-digit multiplication and division", "✖️"),
      unit("multiply-fractions", "Multiply fractions", "🍕"),
      unit("divide-fractions", "Divide fractions", "➗"),
      unit("multiply-decimals", "Multiply decimals", "✖️"),
      unit("divide-decimals", "Divide decimals", "➗"),
      unit("powers-of-ten", "Powers of ten", "🔟"),
      unit("volume", "Volume", "🧊"),
      unit("coordinate-plane", "Coordinate plane", "📈"),
      unit("algebraic-thinking", "Algebraic thinking", "🔤"),
      unit("converting-units", "Converting units of measure", "📏"),
      unit("line-plots", "Line plots", "📊"),
      unit("properties-of-shapes", "Properties of shapes", "📐"),
    ]},
    { id: "us-6", programme: US, label: "6th grade", chapters: [
      unit("ratios", "Ratios", "⚖️"),
      unit("rational-arithmetic", "Arithmetic with rational numbers", "🔢"),
      unit("rates-percentages", "Rates and percentages", "💯"),
      unit("exponents", "Exponents and order of operations", "🔟"),
      unit("negative-numbers", "Negative numbers", "➖"),
      unit("variables-expressions", "Variables and expressions", "🔤"),
      unit("equations-inequalities", "Equations and inequalities", "⚖️"),
      unit("plane-figures", "Plane figures", "📐"),
      unit("coordinate-plane", "Coordinate plane", "📈"),
      unit("figures-3d", "3D figures", "🧊"),
      unit("data-statistics", "Data and statistics", "📊"),
    ]},
    { id: "us-7", programme: US, label: "7th grade", chapters: [
      unit("proportional-relationships", "Proportional relationships", "⚖️"),
      unit("rates-percentages", "Rates and percentages", "💯"),
      unit("integers-add-sub", "Integers: addition and subtraction", "➕"),
      unit("rational-add-sub", "Rational numbers: addition and subtraction", "🔢"),
      unit("negative-mult-div", "Negative numbers: multiplication and division", "➗"),
      unit("expressions-equations", "Expressions, equations and inequalities", "🔤"),
      unit("statistics-probability", "Statistics and probability", "🎲"),
      unit("scale-copies", "Scale copies", "📐"),
      unit("geometry", "Geometry", "📐"),
    ]},
    { id: "us-8", programme: US, label: "8th grade", chapters: [
      unit("numbers-operations", "Numbers and operations", "🔢"),
      unit("solving-equations", "Solving equations with one unknown", "⚖️"),
      unit("linear-equations", "Linear equations and functions", "📈"),
      unit("systems", "Systems of equations", "📈"),
      unit("geometry", "Geometry", "📐"),
      unit("transformations", "Geometric transformations", "🔄"),
      unit("data-modeling", "Data and modeling", "📊"),
    ]},

    // ── Math: High school & College ──────────────────────────────────────
    { id: "hs-algebra-1", programme: HS, label: "Algebra 1", chapters: [
      unit("foundations", "Algebra foundations", "🔤"),
      unit("solving", "Solving equations and inequalities", "⚖️"),
      unit("units", "Working with units", "📏"),
      unit("linear-graphs", "Linear equations and graphs", "📈"),
      unit("linear-forms", "Forms of linear equations", "📈"),
      unit("systems", "Systems of equations", "📈"),
      unit("inequalities", "Inequalities (systems and graphs)", "⚖️"),
      unit("functions", "Functions", "📈"),
      unit("sequences", "Sequences", "🔢"),
      unit("absolute-value", "Absolute value and piecewise functions", "📈"),
      unit("exponents-radicals", "Exponents and radicals", "🔟"),
      unit("exponential", "Exponential growth and decay", "📈"),
      unit("quadratics", "Quadratic functions and equations", "✖️"),
      unit("irrational", "Irrational numbers", "🔢"),
      unit("creativity", "Creativity in algebra", "🎨"),
    ]},
    { id: "hs-geometry", programme: HS, label: "Geometry", chapters: [
      unit("transformations", "Performing transformations", "🔄"),
      unit("transformation-proofs", "Transformation properties and proofs", "🔄"),
      unit("congruence", "Congruence", "📐"),
      unit("similarity", "Similarity", "📐"),
      unit("right-triangles", "Right triangles and trigonometry", "🔺"),
      unit("analytic", "Analytic geometry", "📈"),
      unit("conics", "Conic sections", "📐"),
      unit("circles", "Circles", "⭕"),
      unit("solid", "Solid geometry", "🧊"),
    ]},
    { id: "hs-algebra-2", programme: HS, label: "Algebra 2", chapters: [
      unit("polynomial-arithmetic", "Polynomial arithmetic", "✖️"),
      unit("complex-numbers", "Complex numbers", "🔢"),
      unit("factorization", "Polynomial factorization", "✖️"),
      unit("polynomial-division", "Polynomial division", "➗"),
      unit("polynomial-graphs", "Polynomial graphs", "📈"),
      unit("rational-exponents", "Rational exponents and radicals", "🔟"),
      unit("exponential-models", "Exponential models", "📈"),
      unit("logarithms", "Logarithms", "📈"),
      unit("transformations", "Transformations of functions", "🔄"),
      unit("equations", "Equations", "⚖️"),
      unit("trigonometry", "Trigonometry", "🌀"),
      unit("modeling", "Modeling", "📊"),
    ]},
    { id: "hs-trigonometry", programme: HS, label: "Trigonometry", chapters: [
      unit("right-triangles", "Right triangles and trigonometry", "🔺"),
      unit("functions", "Trigonometric functions", "🌀"),
      unit("non-right-triangles", "Non-right triangles and trigonometry", "🔺"),
      unit("identities", "Trigonometric equations and identities", "🌀"),
    ]},
    { id: "hs-precalculus", programme: HS, label: "Precalculus", chapters: [
      unit("composite-inverse", "Composite and inverse functions", "📈"),
      unit("trigonometry", "Trigonometry", "🌀"),
      unit("complex-numbers", "Complex numbers", "🔢"),
      unit("rational-functions", "Rational functions", "📈"),
      unit("conics", "Conic sections", "📐"),
      unit("vectors", "Vectors", "➡️"),
      unit("matrices", "Matrices", "🕸️"),
      unit("probability", "Probability and combinatorics", "🎲"),
      unit("series", "Series", "🔢"),
      unit("limits", "Limits and continuity", "♾️"),
    ]},
    { id: "hs-statistics", programme: HS, label: "High school statistics", chapters: [
      unit("display-single", "Displaying a single quantitative variable", "📊"),
      unit("analyze-single", "Analyzing a single quantitative variable", "📊"),
      unit("two-way-tables", "Two-way tables", "📊"),
      unit("scatterplots", "Scatterplots", "📈"),
      unit("study-design", "Study design", "🧩"),
      unit("probability", "Probability", "🎲"),
      unit("distributions", "Probability distributions and expected value", "🎲"),
    ]},
    { id: "ap-statistics", programme: HS, label: "AP / College Statistics", chapters: [
      unit("categorical", "Exploring categorical data", "📊"),
      unit("one-var-display", "Exploring one-variable quantitative data: Displaying and describing", "📊"),
      unit("one-var-summary", "Exploring one-variable quantitative data: Summary statistics", "📊"),
      unit("one-var-normal", "Exploring one-variable quantitative data: Percentiles, z-scores and the normal distribution", "📊"),
      unit("two-var", "Exploring two-variable quantitative data", "📈"),
      unit("collecting", "Collecting data", "🧩"),
      unit("probability", "Probability", "🎲"),
      unit("random-variables", "Random variables and probability distributions", "🎲"),
      unit("sampling", "Sampling distributions", "🎲"),
      unit("inference-proportions", "Inference for categorical data: Proportions", "📊"),
      unit("inference-means", "Inference for quantitative data: Means", "📊"),
      unit("chi-square", "Inference for categorical data: Chi-square", "📊"),
      unit("inference-slopes", "Inference for quantitative data: Slopes", "📈"),
      unit("exam", "Prepare for the AP Statistics exam", "🎯"),
    ]},
    { id: "ap-precalculus", programme: HS, label: "AP / College Precalculus", chapters: [
      unit("polynomial-rational", "Polynomial and rational functions", "📈"),
      unit("exponential-logarithmic", "Exponential and logarithmic functions", "📈"),
      unit("trigonometric-polar", "Trigonometric and polar functions", "🌀"),
      unit("parametric", "Functions involving parameters, vectors and matrices", "🕸️"),
      unit("test-support", "AP Precalculus test support", "🎯"),
    ]},
    { id: "ap-calculus", programme: HS, label: "AP / College Calculus", chapters: [
      unit("limits", "Limits and continuity", "♾️"),
      unit("derivatives-basic", "Differentiation: definition and basic derivative rules", "📈"),
      unit("derivatives-advanced", "Differentiation: composite, implicit and inverse functions", "📈"),
      unit("contextual", "Contextual applications of differentiation", "📈"),
      unit("analytical", "Analytical applications of differentiation", "📈"),
      unit("integration", "Integration and accumulation of change", "🧮"),
      unit("differential-equations", "Differential equations", "🌊"),
      unit("applications-integration", "Applications of integration", "🧮"),
      unit("test-support", "AP Calculus test support", "🎯"),
    ]},
    { id: "multivariable-calculus", programme: HS, label: "Multivariable calculus", chapters: [
      unit("thinking", "Thinking about multivariable functions", "📈"),
      unit("derivatives", "Derivatives of multivariable functions", "📈"),
      unit("applications", "Applications of multivariable derivatives", "📈"),
      unit("integrating", "Integrating multivariable functions", "🧮"),
      unit("theorems", "Green's, Stokes', and the divergence theorems", "🌀"),
    ]},
    { id: "differential-equations", programme: HS, label: "Differential equations", chapters: [
      unit("first-order", "First-order differential equations", "🌊"),
      unit("second-order", "Second-order linear equations", "🌊"),
      unit("laplace", "Laplace transform", "🌊"),
    ]},
    { id: "linear-algebra", programme: HS, label: "Linear algebra", chapters: [
      unit("vectors", "Vectors and spaces", "➡️"),
      unit("matrix-transformations", "Matrix transformations", "🕸️"),
      unit("bases", "Alternate coordinate systems (bases)", "🕸️"),
    ]},
  ],
  physics: [
    { id: "found", label: "Foundation", chapters: [
      ch("kinematics", "Motion and forces", ["Velocity and acceleration", "Newton's laws", "Check: motion problems"]),
      ch("energy", "Energy and work", ["Work, power, efficiency", "Conservation of energy", "Check: energy transfers"]),
      ch("waves", "Waves", ["Wave properties", "Reflection and refraction", "Check: wave calculations"]),
    ]},
    { id: "adv", label: "Advanced", chapters: [
      ch("shm", "Oscillations", ["Simple harmonic motion", "Damping and resonance", "Check: pendulum problems"]),
      ch("fields", "Fields", ["Gravitational fields", "Electric fields", "Check: field calculations"]),
      ch("quantum", "Quantum and nuclear", ["Photoelectric effect", "Radioactive decay", "Check: photon energy"]),
    ]},
  ],
  chemistry: [
    { id: "found", label: "Foundation", chapters: [
      ch("atoms", "Atomic structure", ["Atoms, isotopes, ions", "The periodic table", "Check: electron configuration"]),
      ch("bonding", "Bonding", ["Ionic and covalent bonds", "Intermolecular forces", "Check: predicting structure"]),
      ch("reactions", "Reactions and equations", ["Balancing equations", "Moles and mass", "Check: stoichiometry"]),
    ]},
    { id: "adv", label: "Advanced", chapters: [
      ch("energetics", "Energetics and kinetics", ["Enthalpy changes", "Rates and catalysts", "Check: energy profiles"]),
      ch("equilibria", "Equilibria", ["Le Chatelier's principle", "Acids, bases and pH", "Check: equilibrium calculations"]),
      ch("organic", "Organic chemistry", ["Functional groups", "Reaction mechanisms", "Check: synthesis routes"]),
    ]},
  ],
  biology: [
    { id: "found", label: "Foundation", chapters: [
      ch("cells", "Cells", ["Cell structure", "Transport across membranes", "Check: comparing cell types"]),
      ch("organs", "Organ systems", ["Digestion and circulation", "Gas exchange", "Check: tracing a pathway"]),
      ch("genetics", "Genetics", ["DNA and inheritance", "Punnett squares", "Check: predicting offspring"]),
    ]},
    { id: "adv", label: "Advanced", chapters: [
      ch("respiration", "Respiration and photosynthesis", ["Glycolysis and the Krebs cycle", "Light and dark reactions", "Check: ATP yield"]),
      ch("homeostasis", "Homeostasis", ["Negative feedback", "Kidney and osmoregulation", "Check: control mechanisms"]),
      ch("evolution", "Evolution and ecology", ["Natural selection", "Population dynamics", "Check: interpreting data"]),
    ]},
  ],
  "computer-science": [
    { id: "found", label: "Foundation", chapters: [
      ch("basics", "Programming basics", ["Variables and control flow", "Functions and scope", "Check: writing a small program"]),
      ch("data", "Data structures", ["Arrays and lists", "Dictionaries and sets", "Check: choosing a structure"]),
      ch("algos", "Algorithms", ["Searching and sorting", "Big-O notation", "Check: analysing complexity"]),
    ]},
    { id: "adv", label: "Advanced", chapters: [
      ch("recursion", "Recursion and trees", ["Recursive thinking", "Trees and traversal", "Check: recursive problems"]),
      ch("graphs", "Graphs", ["Representation", "BFS and DFS", "Check: shortest paths"]),
      ch("systems", "Systems", ["Memory and processes", "Databases and queries", "Check: designing a schema"]),
    ]},
  ],
  statistics: [
    { id: "found", label: "Foundation", chapters: [
      ch("describe", "Describing data", ["Mean, median, spread", "Charts and distributions", "Check: summarising a dataset"]),
      ch("prob", "Probability", ["Rules of probability", "Conditional probability", "Check: probability problems"]),
      ch("dists", "Distributions", ["Binomial distribution", "Normal distribution", "Check: using tables"]),
    ]},
    { id: "adv", label: "Advanced", chapters: [
      ch("inference", "Inference", ["Sampling and estimation", "Confidence intervals", "Check: interpreting an interval"]),
      ch("testing", "Hypothesis testing", ["Null and alternative", "p-values and errors", "Check: running a test"]),
      ch("bayes", "Bayesian thinking", ["Bayes' rule", "Priors and posteriors", "Check: updating a belief"]),
    ]},
  ],
};

export function levelsFor(subjectId: string): Level[] {
  return CURRICULUM[subjectId] ?? [];
}

/**
 * The levels in menu order, split by the programme they belong to. A subject
 * taught to a single syllabus comes back as one unnamed run.
 */
export function programmes(levels: Level[]): { name?: string; levels: Level[] }[] {
  const runs: { name?: string; levels: Level[] }[] = [];
  for (const level of levels) {
    const last = runs[runs.length - 1];
    if (last && last.name === level.programme) last.levels.push(level);
    else runs.push({ name: level.programme, levels: [level] });
  }
  return runs;
}

/**
 * The levels in menu order, split into the headings they sit under. A syllabus
 * with no `group` on its levels comes back as one unlabelled run, so the menu
 * renders it flat.
 */
export function levelGroups(levels: Level[]): { group?: string; levels: Level[] }[] {
  const runs: { group?: string; levels: Level[] }[] = [];
  for (const level of levels) {
    const last = runs[runs.length - 1];
    if (last && last.group === level.group) last.levels.push(level);
    else runs.push({ group: level.group, levels: [level] });
  }
  return runs;
}

/** Resolve a stored level/chapter pair back to the chapter it names. */
export function findChapter(
  subjectId: string,
  levelId: string | null,
  chapterId: string | null,
): Chapter | null {
  if (!levelId || !chapterId) return null;
  return (
    levelsFor(subjectId)
      .find((l) => l.id === levelId)
      ?.chapters.find((c) => c.id === chapterId) ?? null
  );
}

/** Resolve one lesson from its full path through the curriculum. */
export function findLesson(
  subjectId: string,
  levelId: string,
  chapterId: string,
  lessonId: string,
): { level: Level; chapter: Chapter; lesson: Lesson } | null {
  const level = levelsFor(subjectId).find((l) => l.id === levelId);
  const chapter = level?.chapters.find((c) => c.id === chapterId);
  const lesson = chapter?.lessons.find((l) => l.id === lessonId);
  return level && chapter && lesson ? { level, chapter, lesson } : null;
}
