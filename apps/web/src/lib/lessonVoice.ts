/**
 * The tutor's voice, and the student's, using only what the browser already has.
 *
 * The language is passed in, never guessed here. It used to be looked up from
 * the subject id, which gave `en-GB` for "mathematics" — and the French maths
 * programme is taught in French, so every lesson in it was read aloud with an
 * English mouth. `speechLocale` in `lib/locales.ts` works it out from the
 * subject, the level's programme and the student, in that order.
 *
 * No API and no key on either side. `speechSynthesis` and `SpeechRecognition`
 * ship with the browser, cost nothing, and work offline; a hosted model would
 * be better at both and is not what an hour-long class can wait for a round
 * trip on. Both degrade to nothing rather than throwing, because a class where
 * the microphone is unavailable is a class you type in, not a broken one.
 *
 * `SpeechRecognition` is Chrome and Safari only, under a prefix. That is a real
 * limit and it is checked for rather than assumed.
 */

export const canSpeak = () =>
  typeof window !== "undefined" && "speechSynthesis" in window;

/**
 * Say something in the tutor's voice.
 *
 * A tutor speaking German picks a German voice where the browser has one, which
 * is what stops "Guten Morgen" being read with an English mouth. Anything the
 * tutor says replaces what it was saying: a student who has answered should not
 * sit through the end of the previous sentence.
 */
export function speak(text: string, tag: string): void {
  if (!canSpeak() || !text.trim()) return;
  const utterance = new SpeechSynthesisUtterance(text);
  utterance.lang = tag;

  // Voices load asynchronously and the list is empty on the first call in some
  // browsers. An unmatched voice is not a failure — the default one still
  // speaks, just with the wrong accent.
  utterance.voice = bestVoice(tag);
  utterance.rate = 0.95;

  window.speechSynthesis.cancel();
  window.speechSynthesis.speak(utterance);
}

/**
 * The best voice this browser has for a language, preferring a female one.
 *
 * Luna is a she and has sounded like one since the first Gemini session; a
 * lesson that switches to a male system voice halfway through is a different
 * teacher. Browsers do not expose gender, so this goes on the names macOS,
 * Windows and Chrome actually ship, then on quality markers, then falls back to
 * whatever matches the language at all.
 */
const FEMALE = new RegExp(
  [
    "amélie", "amelie", "audrey", "aurélie", "aurelie", "marie", "julie", "céline", "celine",
    "anna", "petra", "katrin", "helena", "paulina", "monica", "mónica", "elvira",
    "alice", "federica", "samantha", "karen", "moira", "tessa", "fiona", "serena",
    "allison", "ava", "susan", "zira", "hazel", "google français", "google deutsch",
    "google español", "google italiano", "google uk english female",
  ].join("|"),
  "i",
);

function bestVoice(tag: string): SpeechSynthesisVoice | null {
  const language = tag.split("-")[0];
  const candidates = window.speechSynthesis.getVoices()
    .filter((v) => v.lang === tag || v.lang.replace("_", "-").startsWith(language));
  if (!candidates.length) return null;

  const score = (v: SpeechSynthesisVoice) =>
    (FEMALE.test(v.name) ? 4 : 0) +
    // "Enhanced"/"Premium" are the downloadable voices; they are the ones worth
    // hearing for fifty minutes.
    (/enhanced|premium|neural|siri/i.test(v.name) ? 2 : 0) +
    (v.lang === tag ? 1 : 0);

  return [...candidates].sort((a, b) => score(b) - score(a))[0] ?? null;
}

/**
 * Say something, and resolve when it has finished being said.
 *
 * What makes writing and talking land together: the next line is not started
 * until this one has been spoken. Resolves rather than rejects when speech is
 * unavailable or cut short — an interrupted tutor is a normal event, not an
 * error, and the caller must not be left hanging on it.
 */
export function speakAndWait(text: string, tag: string): Promise<void> {
  return new Promise((done) => {
    if (!canSpeak() || !text.trim()) return done();
    const utterance = new SpeechSynthesisUtterance(text);
    utterance.lang = tag;
    utterance.voice = bestVoice(tag);
    utterance.rate = 0.95;
    utterance.onend = () => done();
    utterance.onerror = () => done();
    // No cancel() here. Cancelling before every line put a hard stop between
    // one sentence and the next, which is most of what made a four-step
    // explanation sound chopped up. Interrupting is the caller's business.
    window.speechSynthesis.speak(utterance);
  });
}

export function stopSpeaking(): void {
  if (canSpeak()) window.speechSynthesis.cancel();
}

/* ── listening ───────────────────────────────────────────────────────────── */

type Result = ArrayLike<{ transcript: string }> & { isFinal?: boolean };

type Recognition = {
  lang: string;
  continuous: boolean;
  interimResults: boolean;
  start(): void;
  stop(): void;
  onresult: ((event: { results: ArrayLike<Result> }) => void) | null;
  onerror: (() => void) | null;
  onend: (() => void) | null;
};

function recognitionClass(): (new () => Recognition) | null {
  if (typeof window === "undefined") return null;
  const w = window as unknown as {
    SpeechRecognition?: new () => Recognition;
    webkitSpeechRecognition?: new () => Recognition;
  };
  return w.SpeechRecognition ?? w.webkitSpeechRecognition ?? null;
}

export const canListen = () => recognitionClass() !== null;

/**
 * Keep listening, the way a call does.
 *
 * The browser's own recogniser, used when the live audio session cannot hear —
 * which, with the preview live models, is often. It is not push-to-talk: the
 * microphone stays open and each finished sentence is handed over, so the
 * student just talks.
 *
 * Browsers end a recognition session on their own every minute or so, and some
 * end it on every result. So it restarts itself until it is stopped, and the
 * only way out is the returned function.
 *
 * Returns a function that stops listening.
 */
export function listenContinuously(
  tag: string,
  onHeard: (text: string) => void,
  onProblem: (reason: string) => void,
): () => void {
  /**
   * The tutor stops talking when the student SPEAKS — not when they cough.
   *
   * This used to hang off `onspeechstart`, which fires on any sound the voice
   * detector likes the look of: a cough, a chair, someone else's radio. It cut
   * the tutor off constantly. Interim results are words the recogniser has
   * actually made out, so waiting for one costs a fraction of a second and
   * distinguishes talking from noise.
   */
  const hush = (text: string) => {
    if (/\p{L}{2,}/u.test(text)) stopSpeaking();
  };
  const Recognition = recognitionClass();
  if (!Recognition) {
    onProblem("This browser cannot listen. Chrome and Safari can.");
    return () => {};
  }

  let stopped = false;
  let recognition: Recognition | null = null;

  const start = () => {
    if (stopped) return;
    const session = new Recognition();
    recognition = session;
    session.lang = tag;
    session.continuous = true;
    // On, so the tutor can be interrupted by the first word rather than by the
    // first noise — or by a whole finished sentence, which is far too late.
    session.interimResults = true;

    session.onresult = (event) => {
      const results = Array.from({ length: event.results.length },
                                 (_, i) => event.results[i]);
      const heard = results.map((r) => r[0].transcript).join(" ").trim();
      hush(heard);
      // Only a finished sentence is sent on. Interim text is for stopping the
      // tutor, not for answering it — half a word is not an answer.
      const settled = results.every((r) => (r as { isFinal?: boolean }).isFinal);
      if (settled && heard) onHeard(heard);
    };
    // A browser-ended session is normal and is simply restarted. Only a real
    // failure — a refused microphone — is worth telling anyone about.
    session.onerror = () => { /* reported by onend restarting or not */ };
    session.onend = () => { if (!stopped) setTimeout(start, 300); };

    try {
      session.start();
    } catch {
      onProblem("The microphone could not be started.");
    }
  };

  start();
  return () => { stopped = true; recognition?.stop(); };
}

/** One utterance, then stop. Kept for callers that want a single answer. */
export function listenOnce(
  tag: string,
  onHeard: (text: string) => void,
  onDone: () => void,
): () => void {
  const Recognition = recognitionClass();
  if (!Recognition) {
    onDone();
    return () => {};
  }

  const recognition = new Recognition();
  recognition.lang = tag;
  recognition.continuous = false;
  recognition.interimResults = false;

  recognition.onresult = (event) => {
    const heard = Array.from({ length: event.results.length }, (_, i) =>
      event.results[i][0].transcript,
    ).join(" ").trim();
    if (heard) onHeard(heard);
  };
  recognition.onerror = onDone;
  recognition.onend = onDone;

  try {
    recognition.start();
  } catch {
    onDone();
  }
  return () => recognition.stop();
}
