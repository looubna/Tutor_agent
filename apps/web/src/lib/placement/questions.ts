export type Cefr = "A1" | "A2" | "B1" | "B2" | "C1";

export type PlacementQuestion = {
  /** The sentence, with ___ marking the gap. */
  prompt: string;
  options: [string, string, string];
  /** Index of the correct option. */
  answer: 0 | 1 | 2;
  band: Cefr;
};

/**
 * Twelve items per language, ordered easiest to hardest, so the number a
 * learner gets right maps onto a CEFR band. Written for Zanoba — each item
 * targets one grammar point at the level its band names.
 *
 * These are a first pass and should be reviewed by a teacher of each language
 * before the test is used to place real students.
 */
export const PLACEMENT_QUESTIONS: Record<string, PlacementQuestion[]> = {
  english: [
    { prompt: "She ___ from Brazil.", options: ["am", "is", "are"], answer: 1, band: "A1" },
    { prompt: "I ___ coffee every morning.", options: ["drink", "drinks", "drinking"], answer: 0, band: "A1" },
    { prompt: "We ___ to the cinema last night.", options: ["go", "gone", "went"], answer: 2, band: "A2" },
    { prompt: "There isn't ___ milk left.", options: ["some", "any", "many"], answer: 1, band: "A2" },
    { prompt: "If it rains, we ___ at home.", options: ["stay", "will stay", "stayed"], answer: 1, band: "A2" },
    { prompt: "I've lived here ___ 2019.", options: ["for", "from", "since"], answer: 2, band: "B1" },
    { prompt: "The report ___ by the team yesterday.", options: ["was finished", "finished", "has finished"], answer: 0, band: "B1" },
    { prompt: "She said she ___ call me later.", options: ["will", "would", "would have"], answer: 1, band: "B1" },
    { prompt: "He isn't used to ___ so early.", options: ["get up", "getting up", "got up"], answer: 1, band: "B2" },
    { prompt: "___ I known earlier, I would have helped.", options: ["If", "Have", "Had"], answer: 2, band: "B2" },
    { prompt: "The proposal is worth ___ before the deadline.", options: ["to consider", "considering", "consider"], answer: 1, band: "C1" },
    { prompt: "Little ___ that the deal had already collapsed.", options: ["he knew", "did he know", "knew he"], answer: 1, band: "C1" },
  ],
  french: [
    { prompt: "Je ___ étudiant.", options: ["suis", "es", "est"], answer: 0, band: "A1" },
    { prompt: "Elle ___ à Paris.", options: ["habites", "habite", "habitent"], answer: 1, band: "A1" },
    { prompt: "Hier, nous ___ au marché.", options: ["allons", "sommes allés", "irons"], answer: 1, band: "A2" },
    { prompt: "Je n'ai ___ frères.", options: ["pas de", "pas des", "pas les"], answer: 0, band: "A2" },
    { prompt: "Quand j'étais petit, je ___ souvent au parc.", options: ["allai", "allais", "irai"], answer: 1, band: "A2" },
    { prompt: "C'est le livre ___ je t'ai parlé.", options: ["que", "qui", "dont"], answer: 2, band: "B1" },
    { prompt: "Il faut que tu ___ patient.", options: ["es", "sois", "seras"], answer: 1, band: "B1" },
    { prompt: "Elle m'a dit qu'elle ___ en retard.", options: ["sera", "serait", "soit"], answer: 1, band: "B1" },
    { prompt: "Après ___ mangé, il est sorti.", options: ["avoir", "être", "ayant"], answer: 0, band: "B2" },
    { prompt: "Bien qu'il ___ fatigué, il continue.", options: ["est", "soit", "était"], answer: 1, band: "B2" },
    { prompt: "___ vous en pensiez, le projet avance.", options: ["Quoi que", "Quoique", "Quelque"], answer: 0, band: "C1" },
    { prompt: "Il s'en est fallu de peu qu'il ne ___.", options: ["tombe", "tombait", "tomberait"], answer: 0, band: "C1" },
  ],
  spanish: [
    { prompt: "Yo ___ española.", options: ["soy", "eres", "es"], answer: 0, band: "A1" },
    { prompt: "Ellos ___ en Madrid.", options: ["vive", "viven", "vivimos"], answer: 1, band: "A1" },
    { prompt: "Ayer ___ al cine.", options: ["voy", "fui", "iré"], answer: 1, band: "A2" },
    { prompt: "No hay ___ pan.", options: ["ningún", "ninguno", "nada"], answer: 0, band: "A2" },
    { prompt: "Cuando era niño, ___ mucho.", options: ["jugué", "jugaba", "jugaría"], answer: 1, band: "A2" },
    { prompt: "Espero que ___ pronto.", options: ["vienes", "vengas", "vendrás"], answer: 1, band: "B1" },
    { prompt: "El coche ___ ayer.", options: ["fue reparado", "reparó", "ha reparado"], answer: 0, band: "B1" },
    { prompt: "Si tuviera dinero, ___ un piso.", options: ["compro", "compraría", "compraré"], answer: 1, band: "B1" },
    { prompt: "Me alegro de que ___ venido.", options: ["has", "hayas", "habías"], answer: 1, band: "B2" },
    { prompt: "Llevo dos años ___ español.", options: ["estudio", "estudiando", "estudiar"], answer: 1, band: "B2" },
    { prompt: "Ojalá lo ___ sabido antes.", options: ["he", "hubiera", "había"], answer: 1, band: "C1" },
    { prompt: "Por más que lo ___, no lo entiendo.", options: ["intento", "intente", "intentaré"], answer: 1, band: "C1" },
  ],
  german: [
    { prompt: "Ich ___ Student.", options: ["bin", "bist", "ist"], answer: 0, band: "A1" },
    { prompt: "Wir ___ nach Berlin.", options: ["fahre", "fahren", "fährt"], answer: 1, band: "A1" },
    { prompt: "Gestern ___ ich ins Kino gegangen.", options: ["habe", "bin", "war"], answer: 1, band: "A2" },
    { prompt: "Ich helfe ___ Freund.", options: ["meinen", "meinem", "meines"], answer: 1, band: "A2" },
    { prompt: "Weil es regnet, ___ wir zu Hause.", options: ["bleiben", "bleiben wir", "wir bleiben"], answer: 0, band: "A2" },
    { prompt: "Das Buch, ___ ich gelesen habe, war gut.", options: ["der", "das", "dem"], answer: 1, band: "B1" },
    { prompt: "Der Brief ___ gestern geschrieben.", options: ["wurde", "wird", "worden"], answer: 0, band: "B1" },
    { prompt: "Wenn ich Zeit hätte, ___ ich mitkommen.", options: ["werde", "würde", "wurde"], answer: 1, band: "B1" },
    { prompt: "___ des Regens gingen wir spazieren.", options: ["Wegen", "Trotz", "Während"], answer: 1, band: "B2" },
    { prompt: "Er tut so, als ___ er alles wüsste.", options: ["ob", "wenn", "wie"], answer: 0, band: "B2" },
    { prompt: "Je mehr er übt, ___ besser wird er.", options: ["desto", "je", "umso mehr"], answer: 0, band: "C1" },
    { prompt: "Es ist nicht auszuschließen, dass er ___.", options: ["hat recht", "recht hat", "recht hatte"], answer: 1, band: "C1" },
  ],
  italian: [
    { prompt: "Io ___ italiano.", options: ["sono", "sei", "è"], answer: 0, band: "A1" },
    { prompt: "Loro ___ a Roma.", options: ["abita", "abitano", "abitiamo"], answer: 1, band: "A1" },
    { prompt: "Ieri ___ al cinema.", options: ["vado", "sono andato", "andrò"], answer: 1, band: "A2" },
    { prompt: "Mi piacciono ___ film.", options: ["questo", "questa", "questi"], answer: 2, band: "A2" },
    { prompt: "Da bambino ___ molto.", options: ["giocai", "giocavo", "giocherò"], answer: 1, band: "A2" },
    { prompt: "Spero che tu ___ presto.", options: ["vieni", "venga", "verrai"], answer: 1, band: "B1" },
    { prompt: "___ vuole molto tempo.", options: ["Ci", "Ne", "Si"], answer: 0, band: "B1" },
    { prompt: "Se avessi tempo, ___ con te.", options: ["vengo", "verrei", "verrò"], answer: 1, band: "B1" },
    { prompt: "Sono contento che tu ___ venuto.", options: ["sei", "sia", "eri"], answer: 1, band: "B2" },
    { prompt: "Dopo ___ mangiato, è uscito.", options: ["avere", "essere", "avendo"], answer: 0, band: "B2" },
    { prompt: "Per quanto ci ___, non ci riesce.", options: ["prova", "provi", "proverà"], answer: 1, band: "C1" },
    { prompt: "Sarebbe bastato che tu me lo ___.", options: ["dicevi", "dicessi", "dirai"], answer: 1, band: "C1" },
  ],
  arabic: [
    { prompt: "أنا ___ في المدرسة.", options: ["طالبٌ", "طالبًا", "طالبٍ"], answer: 0, band: "A1" },
    { prompt: "___ الطالبُ إلى المدرسة.", options: ["ذهب", "ذهبتْ", "ذهبوا"], answer: 0, band: "A1" },
    { prompt: "قرأتُ ___ الكتابَ.", options: ["هذا", "هذه", "هؤلاء"], answer: 0, band: "A2" },
    { prompt: "الطالباتُ ___ في الصفِّ.", options: ["يدرسُ", "يدرسنَ", "يدرسون"], answer: 1, band: "A2" },
    { prompt: "لم ___ إلى السوقِ أمسِ.", options: ["أذهبُ", "أذهبْ", "ذهبتُ"], answer: 1, band: "A2" },
    { prompt: "رأيتُ الرجلَ ___ يعملُ هنا.", options: ["الذي", "التي", "الذين"], answer: 0, band: "B1" },
    { prompt: "إنّ الطالبَ ___.", options: ["مجتهدٌ", "مجتهدًا", "مجتهدٍ"], answer: 0, band: "B1" },
    { prompt: "كان الطلابُ ___.", options: ["نائمون", "نائمين", "نائمًا"], answer: 1, band: "B1" },
    { prompt: "لن ___ غدًا.", options: ["أسافرُ", "أسافرَ", "أسافرْ"], answer: 1, band: "B2" },
    { prompt: "جاء الطالبُ ___.", options: ["مسرعٌ", "مسرعًا", "مسرعٍ"], answer: 1, band: "B2" },
    { prompt: "لولا اجتهادُه ___.", options: ["نجح", "لَما نجح", "لينجح"], answer: 1, band: "C1" },
    { prompt: "كلما اجتهدَ الطالبُ ___.", options: ["نجحَ", "ينجحْ", "لينجح"], answer: 0, band: "C1" },
  ],
  chinese: [
    { prompt: "我___中国人。", options: ["是", "在", "有"], answer: 0, band: "A1" },
    { prompt: "他有三___书。", options: ["个", "本", "张"], answer: 1, band: "A1" },
    { prompt: "我昨天没___电影。", options: ["看了", "看", "看过"], answer: 1, band: "A2" },
    { prompt: "他比我___。", options: ["很高", "高", "太高"], answer: 1, band: "A2" },
    { prompt: "我___去过日本。", options: ["没有", "不", "不会"], answer: 0, band: "A2" },
    { prompt: "他中文说___很流利。", options: ["的", "得", "地"], answer: 1, band: "B1" },
    { prompt: "我___北京住了三年。", options: ["在", "从", "对"], answer: 0, band: "B1" },
    { prompt: "___你有时间，我们就去。", options: ["因为", "如果", "虽然"], answer: 1, band: "B1" },
    { prompt: "请___窗户关上。", options: ["把", "被", "让"], answer: 0, band: "B2" },
    { prompt: "我的钱包___偷了。", options: ["把", "被", "给"], answer: 1, band: "B2" },
    { prompt: "___困难再大，我们也要坚持。", options: ["虽然", "即使", "因为"], answer: 1, band: "C1" },
    { prompt: "这件事___他决定。", options: ["由", "被", "把"], answer: 0, band: "C1" },
  ],
  korean: [
    { prompt: "저___ 학생입니다.", options: ["는", "를", "에"], answer: 0, band: "A1" },
    { prompt: "지금 어디___ 가요?", options: ["에", "에서", "도"], answer: 0, band: "A1" },
    { prompt: "어제 친구를 ___.", options: ["만나요", "만났어요", "만날 거예요"], answer: 1, band: "A2" },
    { prompt: "학교___ 공부해요.", options: ["에", "에서", "으로"], answer: 1, band: "A2" },
    { prompt: "밥을 ___ 싶어요.", options: ["먹어", "먹고", "먹으러"], answer: 1, band: "A2" },
    { prompt: "비가 ___ 집에 있었어요.", options: ["와서", "와도", "오면"], answer: 0, band: "B1" },
    { prompt: "선생님___ 오셨어요.", options: ["이", "가", "께서"], answer: 2, band: "B1" },
    { prompt: "내일 시간이 ___ 만날까요?", options: ["있으면", "있어서", "있지만"], answer: 0, band: "B1" },
    { prompt: "문이 바람에 ___.", options: ["열었어요", "열렸어요", "열어요"], answer: 1, band: "B2" },
    { prompt: "친구가 내일 ___ 했어요.", options: ["온다고", "오냐고", "오자고"], answer: 0, band: "B2" },
    { prompt: "노력한 ___ 좋은 결과가 나왔어요.", options: ["덕분에", "때문에", "대신에"], answer: 0, band: "C1" },
    { prompt: "회의가 끝나는 ___ 연락드리겠습니다.", options: ["대로", "동안", "김에"], answer: 0, band: "C1" },
  ],
};

/** Score out of 12 mapped onto the band a learner should start in. */
export function levelForScore(score: number): Cefr {
  if (score <= 2) return "A1";
  if (score <= 5) return "A2";
  if (score <= 8) return "B1";
  if (score <= 10) return "B2";
  return "C1";
}
