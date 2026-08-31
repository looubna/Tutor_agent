import type { Lang } from "@/lib/i18n";

export type SubjectGroup = "language" | "science";

/**
 * A subject Zanoba teaches, plus the line of chalk the tutor leaves on the
 * hero board for it. The chalk is deliberately native to the subject — a
 * conjugation for a language, a formula for a science — so switching subjects
 * in the banner rewrites the board rather than just swapping a label.
 */
export type Subject = {
  id: string;
  group: SubjectGroup;
  /** Two-letter tag shown in the board's corner, like a timetable code. */
  tag: string;
  /** Flag for a language, instrument or symbol for a science. */
  emoji: string;
  /** The chalk line itself. Not translated — it is written in the subject. */
  chalk: string;
  /** Arabic and other right-to-left chalk needs its own text direction. */
  rtl?: boolean;
  /**
   * BCP-47 tag for a language subject: what the browser should listen for and
   * speak in during a lesson. Without it the call screen transcribes a German
   * lesson as English. Sciences have none — they are taught in the interface
   * language, not a target language.
   */
  locale?: string;
  name: Record<Lang, string>;
  /** The unit the chalk line belongs to, captioned under the board. */
  note: Record<Lang, string>;
  /**
   * CEFR range taught, for languages. Sciences have no equivalent ladder, so
   * their cards fall back to the unit in `note`.
   */
  level?: Record<Lang, string>;
};

/** Every language runs the same ladder, so the range is written once. */
const A1_TO_C1: Record<Lang, string> = {
  en: "From A1 to C1",
  fr: "De A1 à C1",
  es: "De A1 a C1",
  de: "Von A1 bis C1",
  it: "Dall'A1 al C1",
  ar: "من A1 إلى C1",
  zh: "从 A1 到 C1",
  ko: "A1부터 C1까지",
};

export const SUBJECTS: Subject[] = [
  {
    id: "english",
    group: "language",
    locale: "en-US",
    tag: "EN",
    emoji: "🇬🇧",
    chalk: "if I had known, I would have gone",
    name: {
      en: "English",
      fr: "Anglais",
      es: "Inglés",
      de: "Englisch",
      it: "Inglese",
      ar: "الإنجليزية",
      zh: "英语",
      ko: "영어",
    },
    note: {
      en: "Third conditional",
      fr: "Conditionnel de type 3",
      es: "Tercer condicional",
      de: "If-Satz Typ III",
      it: "Terzo condizionale",
      ar: "الشرط من النوع الثالث",
      zh: "第三类条件句",
      ko: "가정법 과거완료",
    },
    level: A1_TO_C1,
  },
  {
    id: "french",
    group: "language",
    locale: "fr-FR",
    tag: "FR",
    emoji: "🇫🇷",
    chalk: "il faut que tu saches",
    name: {
      en: "French",
      fr: "Français",
      es: "Francés",
      de: "Französisch",
      it: "Francese",
      ar: "الفرنسية",
      zh: "法语",
      ko: "프랑스어",
    },
    note: {
      en: "The subjunctive",
      fr: "Le subjonctif",
      es: "El subjuntivo",
      de: "Der Subjonctif",
      it: "Il congiuntivo",
      ar: "صيغة السوبجونكتيف",
      zh: "虚拟式",
      ko: "접속법",
    },
    level: A1_TO_C1,
  },
  {
    id: "spanish",
    group: "language",
    locale: "es-ES",
    tag: "ES",
    emoji: "🇪🇸",
    chalk: "ojalá hubiera sabido",
    name: {
      en: "Spanish",
      fr: "Espagnol",
      es: "Español",
      de: "Spanisch",
      it: "Spagnolo",
      ar: "الإسبانية",
      zh: "西班牙语",
      ko: "스페인어",
    },
    note: {
      en: "Pluperfect subjunctive",
      fr: "Subjonctif plus-que-parfait",
      es: "Pluscuamperfecto de subjuntivo",
      de: "Subjuntivo im Plusquamperfekt",
      it: "Congiuntivo trapassato",
      ar: "الماضي التام في صيغة الشرط",
      zh: "虚拟式过去完成时",
      ko: "접속법 대과거",
    },
    level: A1_TO_C1,
  },
  {
    id: "german",
    group: "language",
    locale: "de-DE",
    tag: "DE",
    emoji: "🇩🇪",
    chalk: "weil ich es gesehen habe",
    name: {
      en: "German",
      fr: "Allemand",
      es: "Alemán",
      de: "Deutsch",
      it: "Tedesco",
      ar: "الألمانية",
      zh: "德语",
      ko: "독일어",
    },
    note: {
      en: "Verb-final subordinate clauses",
      fr: "Le verbe en fin de subordonnée",
      es: "El verbo al final de la subordinada",
      de: "Verbletztstellung im Nebensatz",
      it: "Il verbo alla fine della subordinata",
      ar: "الفعل في آخر الجملة التابعة",
      zh: "从句动词后置",
      ko: "종속절의 동사 후치",
    },
    level: A1_TO_C1,
  },
  {
    id: "italian",
    group: "language",
    locale: "it-IT",
    tag: "IT",
    emoji: "🇮🇹",
    chalk: "ci vuole / ci vogliono",
    name: {
      en: "Italian",
      fr: "Italien",
      es: "Italiano",
      de: "Italienisch",
      it: "Italiano",
      ar: "الإيطالية",
      zh: "意大利语",
      ko: "이탈리아어",
    },
    note: {
      en: "Impersonal verbs",
      fr: "Les verbes impersonnels",
      es: "Los verbos impersonales",
      de: "Unpersönliche Verben",
      it: "I verbi impersonali",
      ar: "الأفعال غير الشخصية",
      zh: "无人称动词",
      ko: "비인칭 동사",
    },
    level: A1_TO_C1,
  },
  {
    id: "arabic",
    group: "language",
    locale: "ar-SA",
    tag: "AR",
    emoji: "🇸🇦",
    chalk: "كَتَبَ ← يَكْتُبُ",
    rtl: true,
    name: {
      en: "Arabic",
      fr: "Arabe",
      es: "Árabe",
      de: "Arabisch",
      it: "Arabo",
      ar: "العربية",
      zh: "阿拉伯语",
      ko: "아랍어",
    },
    note: {
      en: "Form I verb patterns",
      fr: "Les schèmes du verbe (forme I)",
      es: "Los esquemas del verbo (forma I)",
      de: "Verbstämme (Form I)",
      it: "Gli schemi del verbo (forma I)",
      ar: "أوزان الفعل المجرد",
      zh: "第一式动词词形",
      ko: "1형 동사 어형",
    },
    level: A1_TO_C1,
  },
  {
    id: "chinese",
    group: "language",
    locale: "zh-CN",
    tag: "ZH",
    emoji: "🇨🇳",
    chalk: "我把书放在桌子上了",
    name: {
      en: "Chinese",
      fr: "Chinois",
      es: "Chino",
      de: "Chinesisch",
      it: "Cinese",
      ar: "الصينية",
      zh: "中文",
      ko: "중국어",
    },
    note: {
      en: "The 把 construction",
      fr: "La construction avec 把",
      es: "La construcción con 把",
      de: "Die 把-Konstruktion",
      it: "La costruzione con 把",
      ar: "تركيب 把",
      zh: "把字句",
      ko: "把 구문",
    },
    level: A1_TO_C1,
  },
  {
    id: "korean",
    group: "language",
    locale: "ko-KR",
    tag: "KO",
    emoji: "🇰🇷",
    chalk: "비가 와서 못 갔어요",
    name: {
      en: "Korean",
      fr: "Coréen",
      es: "Coreano",
      de: "Koreanisch",
      it: "Coreano",
      ar: "الكورية",
      zh: "韩语",
      ko: "한국어",
    },
    note: {
      en: "The -아서/어서 connective",
      fr: "Le connecteur -아서/어서",
      es: "El conector -아서/어서",
      de: "Der Konnektor -아서/어서",
      it: "Il connettivo -아서/어서",
      ar: "أداة الربط -아서/어서",
      zh: "连接词 -아서/어서",
      ko: "연결어미 -아서/어서",
    },
    level: A1_TO_C1,
  },
  {
    id: "mathematics",
    group: "science",
    tag: "MA",
    emoji: "🧮",
    chalk: "∫ sin x dx = −cos x + C",
    name: {
      en: "Mathematics",
      fr: "Mathématiques",
      es: "Matemáticas",
      de: "Mathematik",
      it: "Matematica",
      ar: "الرياضيات",
      zh: "数学",
      ko: "수학",
    },
    note: {
      en: "Antiderivatives",
      fr: "Primitives",
      es: "Primitivas",
      de: "Stammfunktionen",
      it: "Primitive",
      ar: "الدوال الأصلية",
      zh: "不定积分",
      ko: "부정적분",
    },
    /**
     * Maths is the one science taught to named national syllabuses, so its card
     * advertises them the way a language card advertises CEFR.
     */
    level: {
      en: "French syllabus, Pre-K–8, high school and college",
      fr: "Programme français, Pre-K–8, lycée et université",
      es: "Programa francés, Pre-K–8, secundaria y universidad",
      de: "Französischer Lehrplan, Pre-K–8, High School und College",
      it: "Programma francese, Pre-K–8, liceo e università",
      ar: "البرنامج الفرنسي، ومن الروضة إلى الجامعة",
      zh: "法国课程大纲，Pre-K 至八年级，高中与大学",
      ko: "프랑스 교육과정, Pre-K–8, 고교·대학",
    },
  },
  {
    id: "physics",
    group: "science",
    tag: "PH",
    emoji: "🪐",
    chalk: "F = −kx",
    name: {
      en: "Physics",
      fr: "Physique",
      es: "Física",
      de: "Physik",
      it: "Fisica",
      ar: "الفيزياء",
      zh: "物理",
      ko: "물리",
    },
    note: {
      en: "Simple harmonic motion",
      fr: "Le mouvement harmonique simple",
      es: "El movimiento armónico simple",
      de: "Harmonische Schwingung",
      it: "Il moto armonico semplice",
      ar: "الحركة التوافقية البسيطة",
      zh: "简谐运动",
      ko: "단순조화운동",
    },
  },
  {
    id: "chemistry",
    group: "science",
    tag: "CH",
    emoji: "⚗️",
    chalk: "2H₂ + O₂ → 2H₂O",
    name: {
      en: "Chemistry",
      fr: "Chimie",
      es: "Química",
      de: "Chemie",
      it: "Chimica",
      ar: "الكيمياء",
      zh: "化学",
      ko: "화학",
    },
    note: {
      en: "Balancing equations",
      fr: "Équilibrer une équation",
      es: "Ajustar ecuaciones",
      de: "Reaktionsgleichungen ausgleichen",
      it: "Bilanciare le equazioni",
      ar: "موازنة المعادلات",
      zh: "配平化学方程式",
      ko: "화학 반응식 균형 맞추기",
    },
  },
  {
    id: "biology",
    group: "science",
    tag: "BI",
    emoji: "🌱",
    chalk: "ATP → ADP + Pᵢ",
    name: {
      en: "Biology",
      fr: "Biologie",
      es: "Biología",
      de: "Biologie",
      it: "Biologia",
      ar: "الأحياء",
      zh: "生物",
      ko: "생물",
    },
    note: {
      en: "Cellular respiration",
      fr: "La respiration cellulaire",
      es: "La respiración celular",
      de: "Zellatmung",
      it: "La respirazione cellulare",
      ar: "التنفس الخلوي",
      zh: "细胞呼吸",
      ko: "세포 호흡",
    },
  },
  {
    id: "computer-science",
    group: "science",
    tag: "CS",
    emoji: "🤖",
    chalk: "T(n) = 2T(n/2) + n",
    name: {
      en: "Computer science",
      fr: "Informatique",
      es: "Informática",
      de: "Informatik",
      it: "Informatica",
      ar: "علوم الحاسوب",
      zh: "计算机科学",
      ko: "컴퓨터 과학",
    },
    note: {
      en: "The master theorem",
      fr: "Le théorème général",
      es: "El teorema maestro",
      de: "Das Master-Theorem",
      it: "Il teorema principale",
      ar: "المبرهنة الرئيسية",
      zh: "主定理",
      ko: "마스터 정리",
    },
  },
  {
    id: "statistics",
    group: "science",
    tag: "ST",
    emoji: "🎲",
    chalk: "P(H|E) ∝ P(E|H)·P(H)",
    name: {
      en: "Statistics",
      fr: "Statistiques",
      es: "Estadística",
      de: "Statistik",
      it: "Statistica",
      ar: "الإحصاء",
      zh: "统计学",
      ko: "통계",
    },
    note: {
      en: "Bayes' rule",
      fr: "Le théorème de Bayes",
      es: "El teorema de Bayes",
      de: "Der Satz von Bayes",
      it: "Il teorema di Bayes",
      ar: "قاعدة بايز",
      zh: "贝叶斯定理",
      ko: "베이즈 정리",
    },
  },
];

export const LANGUAGE_SUBJECTS = SUBJECTS.filter((s) => s.group === "language");
export const SCIENCE_SUBJECTS = SUBJECTS.filter((s) => s.group === "science");

/**
 * A subject's display name, from the id stored on a booking. Falls back to the
 * id itself for bookings made before subjects existed, so old rows still read
 * as something rather than blank.
 */
export function subjectLabel(id: string, lang: Lang = "en"): string {
  return SUBJECTS.find((s) => s.id === id)?.name[lang] ?? id;
}
