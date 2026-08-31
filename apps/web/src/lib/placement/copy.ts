import type { Lang } from "@/lib/i18n";
import type { Cefr } from "@/lib/placement/questions";

export type PlacementCopy = {
  chooseHeading: string;
  chooseBody: string;
  introHeading: string;
  introBody: string;
  introNote: string;
  start: string;
  back: string;
  next: string;
  skip: string;
  detailsHeading: string;
  detailsBody: string;
  firstName: string;
  firstNamePlaceholder: string;
  email: string;
  emailPlaceholder: string;
  emailOptional: string;
  seeResults: string;
  sending: string;
  resultHeading: string;
  resultScore: string;
  resultLevelLabel: string;
  resultCta: string;
  resultRetake: string;
  emailSent: string;
  emailFailed: string;
  levels: Record<Cefr, { name: string; blurb: string }>;
};

const en: PlacementCopy = {
  chooseHeading: "Which language do you want to test?",
  chooseBody: "Pick a language and we'll place you on the CEFR ladder in about five minutes.",
  introHeading: "Find out your current {{language}} level",
  introBody:
    "Twelve questions, each one a little harder than the last. There's no time limit, and you'll see your level the moment you finish.",
  introNote: "No account needed. Nothing is saved unless you ask for your results by email.",
  start: "Start the test",
  back: "Back",
  next: "Next",
  skip: "Skip this",
  detailsHeading: "Well done — that's all twelve.",
  detailsBody: "Tell us where to send your results, or skip straight to them.",
  firstName: "First name",
  firstNamePlaceholder: "Jane",
  email: "Email",
  emailPlaceholder: "name@example.com",
  emailOptional: "Optional — we'll email a copy of your result and nothing else.",
  seeResults: "See my results",
  sending: "Sending…",
  resultHeading: "Your {{language}} level",
  resultScore: "You scored {{score}} out of {{total}}.",
  resultLevelLabel: "Start at",
  resultCta: "Book a free {{language}} lesson at {{level}}",
  resultRetake: "Take the test again",
  emailSent: "We've sent a copy to your inbox.",
  emailFailed: "We couldn't send the email, but your result is right here.",
  levels: {
    A1: { name: "Beginner", blurb: "You can handle greetings, introductions and everyday phrases about yourself and people you know." },
    A2: { name: "Elementary", blurb: "You can manage routine exchanges — shopping, directions, work and family — in simple, direct language." },
    B1: { name: "Intermediate", blurb: "You can follow straightforward texts and hold a conversation about familiar topics, travel and plans." },
    B2: { name: "Upper intermediate", blurb: "You can argue a point, follow detailed texts and speak fluently enough that neither side has to strain." },
    C1: { name: "Advanced", blurb: "You can use the language flexibly for study and work, and pick up implicit meaning without much effort." },
  },
};

const fr: PlacementCopy = {
  chooseHeading: "Quelle langue voulez-vous tester ?",
  chooseBody: "Choisissez une langue et nous vous situons sur l'échelle du CECRL en cinq minutes environ.",
  introHeading: "Découvrez votre niveau actuel en {{language}}",
  introBody:
    "Douze questions, chacune un peu plus difficile que la précédente. Sans limite de temps, et votre niveau s'affiche dès la fin.",
  introNote: "Aucun compte requis. Rien n'est enregistré, sauf si vous demandez vos résultats par e-mail.",
  start: "Commencer le test",
  back: "Retour",
  next: "Suivant",
  skip: "Passer",
  detailsHeading: "Bravo — les douze sont faites.",
  detailsBody: "Dites-nous où envoyer vos résultats, ou passez directement à ceux-ci.",
  firstName: "Prénom",
  firstNamePlaceholder: "Jeanne",
  email: "E-mail",
  emailPlaceholder: "nom@exemple.com",
  emailOptional: "Facultatif — nous envoyons une copie de votre résultat, rien d'autre.",
  seeResults: "Voir mes résultats",
  sending: "Envoi…",
  resultHeading: "Votre niveau en {{language}}",
  resultScore: "Vous avez obtenu {{score}} sur {{total}}.",
  resultLevelLabel: "Commencez en",
  resultCta: "Réserver un cours gratuit de {{language}} en {{level}}",
  resultRetake: "Repasser le test",
  emailSent: "Nous en avons envoyé une copie dans votre boîte mail.",
  emailFailed: "L'envoi de l'e-mail a échoué, mais votre résultat est juste ici.",
  levels: {
    A1: { name: "Débutant", blurb: "Vous gérez les salutations, les présentations et les phrases du quotidien sur vous et vos proches." },
    A2: { name: "Élémentaire", blurb: "Vous vous débrouillez dans les échanges courants — courses, itinéraires, travail, famille — en langue simple et directe." },
    B1: { name: "Intermédiaire", blurb: "Vous suivez des textes clairs et tenez une conversation sur des sujets familiers, les voyages et les projets." },
    B2: { name: "Intermédiaire supérieur", blurb: "Vous défendez un point de vue, suivez des textes détaillés et parlez assez couramment pour que l'échange reste fluide." },
    C1: { name: "Avancé", blurb: "Vous utilisez la langue avec souplesse pour les études et le travail, et saisissez l'implicite sans effort." },
  },
};

const es: PlacementCopy = {
  chooseHeading: "¿Qué idioma quieres evaluar?",
  chooseBody: "Elige un idioma y te situamos en la escala del MCER en unos cinco minutos.",
  introHeading: "Descubre tu nivel actual de {{language}}",
  introBody:
    "Doce preguntas, cada una un poco más difícil que la anterior. Sin límite de tiempo, y verás tu nivel en cuanto termines.",
  introNote: "No hace falta cuenta. No guardamos nada salvo que pidas tus resultados por correo.",
  start: "Empezar la prueba",
  back: "Atrás",
  next: "Siguiente",
  skip: "Saltar esta",
  detailsHeading: "Muy bien: las doce están hechas.",
  detailsBody: "Dinos dónde enviarte los resultados, o pasa directamente a verlos.",
  firstName: "Nombre",
  firstNamePlaceholder: "Ana",
  email: "Correo electrónico",
  emailPlaceholder: "nombre@ejemplo.com",
  emailOptional: "Opcional: te enviamos una copia de tu resultado y nada más.",
  seeResults: "Ver mis resultados",
  sending: "Enviando…",
  resultHeading: "Tu nivel de {{language}}",
  resultScore: "Has acertado {{score}} de {{total}}.",
  resultLevelLabel: "Empieza en",
  resultCta: "Reserva una clase gratis de {{language}} en {{level}}",
  resultRetake: "Repetir la prueba",
  emailSent: "Te hemos enviado una copia a tu correo.",
  emailFailed: "No hemos podido enviar el correo, pero tu resultado está aquí mismo.",
  levels: {
    A1: { name: "Principiante", blurb: "Te manejas con saludos, presentaciones y frases cotidianas sobre ti y tu entorno." },
    A2: { name: "Elemental", blurb: "Resuelves intercambios habituales — compras, direcciones, trabajo y familia — con lenguaje sencillo y directo." },
    B1: { name: "Intermedio", blurb: "Sigues textos claros y mantienes una conversación sobre temas conocidos, viajes y planes." },
    B2: { name: "Intermedio alto", blurb: "Defiendes una postura, sigues textos detallados y hablas con fluidez suficiente para que nadie tenga que esforzarse." },
    C1: { name: "Avanzado", blurb: "Usas el idioma con flexibilidad para estudiar y trabajar, y captas lo implícito sin esfuerzo." },
  },
};

const de: PlacementCopy = {
  chooseHeading: "Welche Sprache möchtest du testen?",
  chooseBody: "Wähle eine Sprache, und wir ordnen dich in etwa fünf Minuten auf der GER-Skala ein.",
  introHeading: "Finde dein aktuelles Niveau in {{language}} heraus",
  introBody:
    "Zwölf Fragen, jede etwas schwerer als die vorige. Ohne Zeitlimit, und dein Niveau siehst du sofort am Ende.",
  introNote: "Kein Konto nötig. Es wird nichts gespeichert, außer du möchtest dein Ergebnis per E-Mail.",
  start: "Test starten",
  back: "Zurück",
  next: "Weiter",
  skip: "Überspringen",
  detailsHeading: "Gut gemacht — alle zwölf geschafft.",
  detailsBody: "Sag uns, wohin wir dein Ergebnis schicken sollen, oder geh direkt weiter.",
  firstName: "Vorname",
  firstNamePlaceholder: "Anna",
  email: "E-Mail",
  emailPlaceholder: "name@beispiel.de",
  emailOptional: "Optional — wir schicken eine Kopie deines Ergebnisses und sonst nichts.",
  seeResults: "Mein Ergebnis ansehen",
  sending: "Wird gesendet…",
  resultHeading: "Dein Niveau in {{language}}",
  resultScore: "Du hast {{score}} von {{total}} richtig.",
  resultLevelLabel: "Starte bei",
  resultCta: "Kostenlose {{language}}-Stunde auf {{level}} buchen",
  resultRetake: "Test wiederholen",
  emailSent: "Wir haben dir eine Kopie ins Postfach geschickt.",
  emailFailed: "Die E-Mail ließ sich nicht senden, aber dein Ergebnis steht hier.",
  levels: {
    A1: { name: "Anfänger", blurb: "Du kommst mit Begrüßungen, Vorstellungen und Alltagssätzen über dich und dein Umfeld zurecht." },
    A2: { name: "Grundstufe", blurb: "Du meisterst Routinesituationen — Einkauf, Wegbeschreibung, Arbeit und Familie — in einfacher, direkter Sprache." },
    B1: { name: "Mittelstufe", blurb: "Du verstehst klare Texte und führst Gespräche über vertraute Themen, Reisen und Pläne." },
    B2: { name: "Fortgeschritten", blurb: "Du vertrittst einen Standpunkt, folgst detaillierten Texten und sprichst flüssig genug, dass sich niemand anstrengen muss." },
    C1: { name: "Oberstufe", blurb: "Du nutzt die Sprache flexibel für Studium und Beruf und erfasst Gemeintes ohne große Mühe." },
  },
};

const it: PlacementCopy = {
  chooseHeading: "Quale lingua vuoi testare?",
  chooseBody: "Scegli una lingua e ti collochiamo sulla scala del QCER in circa cinque minuti.",
  introHeading: "Scopri il tuo livello attuale di {{language}}",
  introBody:
    "Dodici domande, ognuna un po' più difficile della precedente. Nessun limite di tempo, e il livello appare appena finisci.",
  introNote: "Nessun account necessario. Non salviamo nulla, a meno che tu non chieda i risultati via e-mail.",
  start: "Inizia il test",
  back: "Indietro",
  next: "Avanti",
  skip: "Salta",
  detailsHeading: "Bravo — tutte e dodici.",
  detailsBody: "Dicci dove inviare i risultati, oppure vai direttamente a vederli.",
  firstName: "Nome",
  firstNamePlaceholder: "Giulia",
  email: "E-mail",
  emailPlaceholder: "nome@esempio.it",
  emailOptional: "Facoltativo — inviamo una copia del risultato e nient'altro.",
  seeResults: "Vedi i risultati",
  sending: "Invio…",
  resultHeading: "Il tuo livello di {{language}}",
  resultScore: "Hai totalizzato {{score}} su {{total}}.",
  resultLevelLabel: "Parti da",
  resultCta: "Prenota una lezione gratuita di {{language}} al livello {{level}}",
  resultRetake: "Rifai il test",
  emailSent: "Ti abbiamo inviato una copia via e-mail.",
  emailFailed: "Non siamo riusciti a inviare l'e-mail, ma il risultato è qui.",
  levels: {
    A1: { name: "Principiante", blurb: "Te la cavi con saluti, presentazioni e frasi quotidiane su di te e su chi conosci." },
    A2: { name: "Elementare", blurb: "Gestisci scambi di routine — spesa, indicazioni, lavoro e famiglia — con un linguaggio semplice e diretto." },
    B1: { name: "Intermedio", blurb: "Segui testi chiari e sostieni una conversazione su temi familiari, viaggi e progetti." },
    B2: { name: "Intermedio superiore", blurb: "Sostieni una tesi, segui testi dettagliati e parli abbastanza fluentemente da non far faticare nessuno." },
    C1: { name: "Avanzato", blurb: "Usi la lingua con flessibilità per studio e lavoro e cogli l'implicito senza sforzo." },
  },
};

const ar: PlacementCopy = {
  chooseHeading: "أي لغة تريد اختبارها؟",
  chooseBody: "اختر لغة وسنحدّد موقعك على سلّم الإطار الأوروبي المرجعي في خمس دقائق تقريبًا.",
  introHeading: "اكتشف مستواك الحالي في {{language}}",
  introBody:
    "اثنا عشر سؤالًا، كل واحد أصعب قليلًا من سابقه. لا حدّ زمني، وستظهر لك النتيجة فور انتهائك.",
  introNote: "لا حاجة إلى حساب. ولا نحفظ شيئًا إلا إذا طلبت نتيجتك بالبريد الإلكتروني.",
  start: "ابدأ الاختبار",
  back: "رجوع",
  next: "التالي",
  skip: "تخطَّ هذا السؤال",
  detailsHeading: "أحسنت — انتهت الأسئلة الاثنا عشر.",
  detailsBody: "أخبرنا أين نرسل نتيجتك، أو انتقل إليها مباشرة.",
  firstName: "الاسم الأول",
  firstNamePlaceholder: "سارة",
  email: "البريد الإلكتروني",
  emailPlaceholder: "name@example.com",
  emailOptional: "اختياري — نرسل نسخة من نتيجتك ولا شيء غير ذلك.",
  seeResults: "عرض نتيجتي",
  sending: "جارٍ الإرسال…",
  resultHeading: "مستواك في {{language}}",
  resultScore: "أصبت {{score}} من {{total}}.",
  resultLevelLabel: "ابدأ من",
  resultCta: "احجز درسًا مجانيًا في {{language}} بمستوى {{level}}",
  resultRetake: "إعادة الاختبار",
  emailSent: "أرسلنا نسخة إلى بريدك.",
  emailFailed: "تعذّر إرسال البريد، لكن نتيجتك أمامك هنا.",
  levels: {
    A1: { name: "مبتدئ", blurb: "تتعامل مع التحيات والتعريف بالنفس والعبارات اليومية عنك وعمّن تعرفهم." },
    A2: { name: "ما قبل المتوسط", blurb: "تدير المواقف المعتادة — التسوق والاتجاهات والعمل والعائلة — بلغة بسيطة ومباشرة." },
    B1: { name: "متوسط", blurb: "تتابع النصوص الواضحة وتجري محادثة حول مواضيع مألوفة والسفر والخطط." },
    B2: { name: "فوق المتوسط", blurb: "تدافع عن رأيك وتتابع النصوص المفصّلة وتتحدث بطلاقة تكفي ليسير الحوار دون عناء." },
    C1: { name: "متقدم", blurb: "تستخدم اللغة بمرونة في الدراسة والعمل، وتلتقط المعنى الضمني دون جهد يُذكر." },
  },
};

const zh: PlacementCopy = {
  chooseHeading: "你想测试哪门语言？",
  chooseBody: "选一门语言，我们用大约五分钟把你定位到 CEFR 等级上。",
  introHeading: "了解你目前的{{language}}水平",
  introBody: "十二道题，一题比一题难一点。没有时间限制，做完立刻看到你的等级。",
  introNote: "无需注册。除非你要求把结果发到邮箱，否则我们不保存任何内容。",
  start: "开始测试",
  back: "上一题",
  next: "下一题",
  skip: "跳过这题",
  detailsHeading: "做得好——十二题都完成了。",
  detailsBody: "告诉我们把结果发到哪里，或者直接查看结果。",
  firstName: "名字",
  firstNamePlaceholder: "小明",
  email: "电子邮箱",
  emailPlaceholder: "name@example.com",
  emailOptional: "可选——我们只会发送一份结果副本，不做别的。",
  seeResults: "查看我的结果",
  sending: "发送中…",
  resultHeading: "你的{{language}}水平",
  resultScore: "你答对了 {{total}} 题中的 {{score}} 题。",
  resultLevelLabel: "建议起点",
  resultCta: "预约一节 {{level}} 级别的免费{{language}}课",
  resultRetake: "再测一次",
  emailSent: "我们已把副本发到你的邮箱。",
  emailFailed: "邮件没能发送，不过结果就在这里。",
  levels: {
    A1: { name: "入门", blurb: "你能应付问候、自我介绍，以及关于自己和身边人的日常表达。" },
    A2: { name: "初级", blurb: "你能用简单直接的语言处理日常事务——购物、问路、工作和家庭。" },
    B1: { name: "中级", blurb: "你能读懂清晰的文章，也能就熟悉的话题、旅行和计划进行交谈。" },
    B2: { name: "中高级", blurb: "你能为观点辩护、读懂细节丰富的文章，说得足够流利，双方都不费力。" },
    C1: { name: "高级", blurb: "你能在学习和工作中灵活运用这门语言，并轻松领会言外之意。" },
  },
};

const ko: PlacementCopy = {
  chooseHeading: "어떤 언어를 테스트할까요?",
  chooseBody: "언어를 고르면 약 5분 만에 CEFR 등급에서 위치를 알려 드립니다.",
  introHeading: "현재 {{language}} 실력을 확인해 보세요",
  introBody: "열두 문제, 뒤로 갈수록 조금씩 어려워집니다. 시간 제한은 없고, 끝나는 즉시 등급이 나옵니다.",
  introNote: "계정이 필요 없습니다. 결과를 이메일로 요청하지 않는 한 아무것도 저장하지 않습니다.",
  start: "테스트 시작",
  back: "이전",
  next: "다음",
  skip: "이 문제 건너뛰기",
  detailsHeading: "수고하셨습니다 — 열두 문제를 모두 마쳤습니다.",
  detailsBody: "결과를 어디로 보낼지 알려 주시거나, 바로 결과를 확인하세요.",
  firstName: "이름",
  firstNamePlaceholder: "지민",
  email: "이메일",
  emailPlaceholder: "name@example.com",
  emailOptional: "선택 사항 — 결과 사본만 보내 드리며 그 외에는 아무것도 보내지 않습니다.",
  seeResults: "결과 보기",
  sending: "보내는 중…",
  resultHeading: "당신의 {{language}} 등급",
  resultScore: "{{total}}문제 중 {{score}}문제를 맞혔습니다.",
  resultLevelLabel: "시작 레벨",
  resultCta: "{{level}} 레벨 {{language}} 무료 수업 예약하기",
  resultRetake: "다시 테스트하기",
  emailSent: "사본을 이메일로 보내 드렸습니다.",
  emailFailed: "이메일을 보내지 못했지만 결과는 여기 있습니다.",
  levels: {
    A1: { name: "입문", blurb: "인사와 자기소개, 그리고 자신과 주변 사람에 대한 일상 표현을 다룰 수 있습니다." },
    A2: { name: "초급", blurb: "쇼핑, 길 묻기, 직장, 가족 같은 일상적인 상황을 쉽고 직접적인 말로 해결할 수 있습니다." },
    B1: { name: "중급", blurb: "명확한 글을 따라가고 익숙한 주제, 여행, 계획에 대해 대화를 이어 갈 수 있습니다." },
    B2: { name: "중상급", blurb: "주장을 펼치고 자세한 글을 이해하며, 서로 애쓰지 않아도 될 만큼 유창하게 말합니다." },
    C1: { name: "고급", blurb: "학업과 업무에서 언어를 유연하게 쓰고, 함축된 의미도 큰 어려움 없이 파악합니다." },
  },
};

const COPY: Record<Lang, PlacementCopy> = { en, fr, es, de, it, ar, zh, ko };

export function placementCopy(lang: Lang): PlacementCopy {
  return COPY[lang] ?? COPY.en;
}

export function fill(template: string, vars: Record<string, string | number>) {
  let out = template;
  for (const [k, v] of Object.entries(vars)) out = out.replaceAll(`{{${k}}}`, String(v));
  return out;
}
