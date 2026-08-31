"use client";

import {
  useCallback, useEffect, useRef, useState, useSyncExternalStore, type ReactNode,
} from "react";
import { useRouter } from "next/navigation";
import { completeBooking } from "@/app/actions/booking";
import { LessonPaper } from "@/components/LessonPaper";
import { Whiteboard } from "@/components/Whiteboard";
import { useT } from "@/lib/i18n";
import { TUTOR_NAME } from "@/lib/tutor";
import { PresenceWatcher } from "@/lib/presence";
import {
  canListen, canSpeak, listenContinuously, speak, speakAndWait, stopSpeaking,
} from "@/lib/lessonVoice";
import { canDoLiveAudio, startLiveLesson, type LiveSession } from "@/lib/liveLesson";
import { startTutorFace, type TutorFace } from "@/lib/tutorFace";

type Message = { role: "STUDENT" | "TUTOR"; content: string };

/**
 * One moment of a turn: a sentence and the line written while it is said, or a
 * page being turned to. They are played in the order they happened.
 */
type Beat =
  | { say: string; write: string; on: string; highlight?: number }
  | { turn_to: string };

/**
 * The column of faces beside a shared stage: how wide it may be, and where the
 * student's own choice of width is kept.
 */
const RAIL_MIN = 200;
const RAIL_MAX = 560;
const RAIL_DEFAULT = 320;
const RAIL_KEY = "lesson.railWidth";

/** Milliseconds a character takes to appear, at a readable writing pace. */
const HAND_MS = 45;

/** How long a silent avatar is given before the silence is worth explaining. */
const NO_AUDIO_MS = 12_000;
/** How long the lesson will wait for the tutor's face before starting without it. */
const FACE_HEADSTART_MS = 12_000;
const clampRail = (width: number) => Math.min(RAIL_MAX, Math.max(RAIL_MIN, Math.round(width)));

/** What the server can honestly say about a width kept in a browser. */
const railOnTheServer = () => RAIL_DEFAULT;

const readRail = () => {
  try {
    const kept = Number(window.localStorage.getItem(RAIL_KEY));
    return kept ? clampRail(kept) : RAIL_DEFAULT;
  } catch {
    // Private windows and blocked storage: the default is a fine answer.
    return RAIL_DEFAULT;
  }
};

const keepRail = (width: number) => {
  try {
    window.localStorage.setItem(RAIL_KEY, String(width));
  } catch {
    // Not being able to remember it is not a reason to lose it now.
  }
};

/** A capability the browser either has or does not; it never gains one midway. */
const neverChanges = () => () => {};
const notOnTheServer = () => false;

/** A piece of the lesson's material, put on the stage by the tutor. */
type SharedMaterial = {
  id: string;
  kind: string;
  title: string;
  instruction: string;
  content: string;
  exercises: { id: string; prompt: string; instructions: string; options: string[] }[];
};

export function CallScreen({
  bookingId,
  initialMessages,
  subjectName,
  studentName,
  studentImage,
  hasPaper,
  voiceTag,
}: {
  bookingId: string;
  initialMessages: Message[];
  /** The subject being taught, for the label over the tutor's video. */
  subjectName: string | null;
  /** The learner, for their tile: their picture, or the initial it falls back to. */
  studentName: string;
  studentImage: string | null;
  /** Whether a worksheet has been published for this class. */
  hasPaper: boolean;
  /**
   * BCP-47 tag for the language this class is spoken in — resolved by
   * `speechLocale`, not guessed from the subject. It is what the tutor's voice
   * and the microphone are both set to.
   */
  voiceTag: string;
}) {
  const router = useRouter();

  const localVideoRef = useRef<HTMLVideoElement>(null);
  const streamRef = useRef<MediaStream | null>(null);
  const screenStreamRef = useRef<MediaStream | null>(null);
  const screenVideoRef = useRef<HTMLVideoElement>(null);

  // The class itself. Seeded from what is already in the database so a student
  // who refreshes mid-lesson does not lose the first half of it.
  const [messages, setMessages] = useState<Message[]>(initialMessages);
  const [draft, setDraft] = useState("");
  const [thinking, setThinking] = useState(false);
  const [tutorProblem, setTutorProblem] = useState<string | null>(null);
  const transcriptEnd = useRef<HTMLDivElement>(null);

  // Voice. Muting the tutor is a lesson preference, not an audio bug, so it is
  // remembered in state rather than by cancelling every utterance.
  const [tutorMuted, setTutorMuted] = useState(false);
  // Mirrored, because the live session's event handler outlives the render that
  // created it: muting mid-lesson has to reach a closure made minutes ago.
  const muted = useRef(false);
  useEffect(() => { muted.current = tutorMuted; }, [tutorMuted]);

  // Voices load asynchronously, and the list is empty on the first call in
  // Chrome — which means the first thing the tutor ever says comes out in the
  // default system voice, whatever `bestVoice` would have chosen. Touching the
  // list on mount makes it ready before it is needed.
  useEffect(() => {
    if (!canSpeak()) return;
    window.speechSynthesis.getVoices();
  }, []);
  // Whether this browser can speak and listen. Read through
  // `useSyncExternalStore` because the honest answer differs between the server
  // (no) and the browser (it depends), and that is a hydration mismatch rather
  // than a feature check if it is read during render. Nothing ever changes it,
  // so the subscription is a no-op.
  const voice = {
    speak: useSyncExternalStore(neverChanges, canSpeak, notOnTheServer),
    live: useSyncExternalStore(neverChanges, canDoLiveAudio, notOnTheServer),
    listen: useSyncExternalStore(neverChanges, canListen, notOnTheServer),
  };

  // Whether there is actually somebody in front of the camera, rather than
  // whether the camera is switched on.
  const presence = useRef(new PresenceWatcher());
  const [presentNow, setPresentNow] = useState(false);

  // What the tutor has put on the stage beside the paper.
  const [material, setMaterial] = useState<SharedMaterial | null>(null);

  // The spoken lesson. While it is running the tutor hears the room directly
  // and answers in its own voice, so the typed turn loop and the browser's
  // speech synthesis both stand down — two tutors talking at once is worse
  // than either alone.
  const live = useRef<LiveSession | null>(null);
  /**
   * Whether the spoken tutor has actually made a sound.
   *
   * A socket that is open is not a tutor you can hear: the live models
   * sometimes connect, transcribe you, call their tools and never say a word.
   * The browser's own voice used to stand down the moment a session existed,
   * so a mute live session took the fallback with it and the student heard
   * nothing at all. It stands down only once something has genuinely been
   * heard.
   */
  const heardLiveAudio = useRef(false);
  /** Stops the browser's own recogniser, when it is the one listening. */
  const stopEar = useRef<() => void>(() => {});
  const [earOpen, setEarOpen] = useState(false);
  const [liveState, setLiveState] = useState<"off" | "starting" | "on">("off");
  const [liveNote, setLiveNote] = useState<string | null>(null);

  /**
   * The tutor's face: a live avatar in the tutor tile, in place of the
   * portrait.
   *
   * It is the tutor's mouth as well as its face — every line goes to it rather
   * than to the browser's voice, and the socket's own audio is muted while it
   * has the floor. A lesson taught by a still photograph and a synthesiser is
   * a phone call with a stock image on it; this is a person, who looks at you
   * and moves while she explains.
   *
   * A ref, not state, because the handlers that speak were made minutes ago
   * and have to reach the session that exists now. `faceUp` is the same fact
   * for the renderer.
   */
  const face = useRef<TutorFace | null>(null);
  const faceStarting = useRef(false);
  const faceVideo = useRef<HTMLVideoElement | null>(null);
  const faceAudio = useRef<HTMLAudioElement | null>(null);

  /** Put her on whichever pair of elements is currently mounted. */
  const showHer = () => {
    if (faceVideo.current && faceAudio.current) {
      face.current?.attach(faceVideo.current, faceAudio.current);
    }
  };
  const [faceUp, setFaceUp] = useState(false);
  /**
   * Set once she has been asked to speak and demonstrably has not.
   *
   * She stays on screen — a quiet face is still a person in the room, and the
   * session is paid for either way — but she stops being the mouth, and the
   * voice goes back to the socket or the browser.
   */
  const faceMute = useRef(false);
  /**
   * Whether the spoken lesson has the floor.
   *
   * Two tutors were audible at once and stopping the one that was talking was
   * never enough, because the written lesson does not speak from one place: a
   * beat, the sentence after a beat, the tail of a turn that was already in
   * flight when the audio was joined. Each was guarded separately and each
   * guard was true at a slightly different moment. This is the single fact
   * they all needed — while the socket is the voice, the browser is not — and
   * it is a ref because the turn that is about to speak was built minutes ago.
   */
  const liveOwnsVoice = useRef(false);
  /**
   * The tile the tutor's stillness is animated on.
   *
   * Written to directly rather than through state: the level changes fifty
   * times a second and re-rendering a call screen at that rate to move a
   * photograph a fraction of a percent would be absurd. One custom property,
   * set on a node, read by the stylesheet.
   */
  const stillTile = useRef<HTMLDivElement>(null);
  const showVoice = (level: number) =>
    stillTile.current?.style.setProperty("--voice", level.toFixed(3));
  /** Her ear, with a note taken the first time anything actually goes in it. */
  const herEar = () => {
    const her = face.current;
    if (!her || faceMute.current) return null;
    return (pcm24kBase64: string) => {
      if (!fedFace.current) console.info("[tutor-face] lesson audio is reaching her");
      fedFace.current = true;
      her.speakAudio(pcm24kBase64);
    };
  };
  /**
   * Whether the lesson's voice has ever actually reached her.
   *
   * The difference between "the avatar is broken" and "there was nothing to
   * say" is invisible on screen — both are a person sitting there — and it is
   * the first thing anybody needs to know when she is quiet. It costs a
   * boolean to tell them apart.
   */
  const fedFace = useRef(false);
  // The shared whiteboard as the tutor has written it. The student's own pen
  // draws over the top; these are the lines that came from the lesson.
  const [board, setBoard] = useState<string[]>([]);

  // Translated at render rather than when it happens, so switching interface
  // language rewrites the message instead of freezing the one it was raised in.
  const [cameraDenied, setCameraDenied] = useState(false);
  const t = useT();
  const [micMuted, setMicMuted] = useState(false);
  const [cameraOff, setCameraOff] = useState(true);
  const [sharing, setSharing] = useState(false);
  const [boardOpen, setBoardOpen] = useState(false);
  // The paper opens with the class rather than waiting to be found. A lesson
  // taught on a worksheet the student never opened is a lesson taught at them.
  const [paperOpen, setPaperOpen] = useState(hasPaper);
  const [nudgeDismissed, setNudgeDismissed] = useState(false);
  const [leaving, setLeaving] = useState(false);
  // Closed until asked for. A spoken lesson is heard and watched, not read —
  // the transcript is a record to check back on, and giving it a third of the
  // screen from the first second pushes the tutor and the paper aside for
  // something nobody is looking at yet. The control bar opens it.
  const [panelOpen, setPanelOpen] = useState(false);
  const [elapsed, setElapsed] = useState(0);

  // Elapsed time counts from arriving on the call, which is what a learner
  // means by "how long have we been going" — not the booked start time.
  useEffect(() => {
    const id = setInterval(() => setElapsed((s) => s + 1), 1000);
    return () => clearInterval(id);
  }, []);

  const [, setMarks] = useState(0);
  const showingPage = useRef<string | null>(null);
  /** The student's handwriting, waiting to be shown to the tutor. */
  const ink = useRef<string | null>(null);
  const inkSent = useRef<string | null>(null);
  /** The line the tutor is writing this instant, revealed as it is spoken. */
  const [nibAt, setNibAt] = useState<string | null>(null);
  const [nibOn, setNibOn] = useState<string | null>(null);
  const [nibStep, setNibStep] = useState(0);
  /** True while a line is still being written, so the paper shows a nib. */
  const [nibBusy, setNibBusy] = useState(false);
  /** Which explanation this is, so the last one's lines can be cleared. */
  const [nibRun, setNibRun] = useState(0);
  /** The page the explanation has reached, which is not always the last one. */
  const [turnedTo, setTurnedTo] = useState<string | null>(null);
  const [explaining, setExplaining] = useState(false);
  const playing = useRef(0);

  /**
   * Bring to the front whatever the tutor just used.
   *
   * It would say "regarde, j'écris ça" while the student was looking at the
   * tutor's face, and the writing was real but on a surface nobody had open.
   * A teacher who writes on the board is standing at the board; the screen
   * follows the same way, and the student can still switch back by hand.
   */
  const followTheTutor = useCallback(
    (next: { board?: string[]; page?: string | null; marks?: number }) => {
      // Actually turn to it, not just remember which page she is on.
      //
      // The written lesson turns pages through a `turn_to` beat, and that was
      // the only thing in the room that ever moved the paper. A spoken lesson
      // has no beats: it calls its tool, the agent reports the new page here,
      // and this recorded it and opened the paper at whatever page was already
      // showing. So the tutor said "let me show you the next page", the page
      // she meant was real, and the student sat looking at the old one.
      if (next.page && next.page !== showingPage.current) setTurnedTo(next.page);

      setBoard((was) => {
        const lines = next.board ?? was;
        if (lines.length > was.length) {
          setBoardOpen(true);
          setPaperOpen(false);
        }
        return lines;
      });
      setMarks((was) => {
        const now = next.marks ?? was;
        const turned = Boolean(next.page && next.page !== showingPage.current);
        if (now > was || turned) {
          setBoardOpen(false);
          setPaperOpen(true);
        }
        showingPage.current = next.page ?? showingPage.current;
        return now;
      });
    },
    [],
  );

  /**
   * Bring the tutor's face up.
   *
   * Spent on the same gesture that joins the audio, for two reasons: a browser
   * will not play a stream with sound in it without one, and a session nobody
   * is listening to still costs the minutes it runs for. If it does not come
   * up the class is unchanged — the portrait stays, and the voice is whichever
   * one would have spoken anyway.
   */
  const showFace = useCallback(async () => {
    if (face.current || faceStarting.current) return;
    faceStarting.current = true;
    faceMute.current = false;
    try {
      const opened = await startTutorFace({
        onLost: () => {
          face.current = null;
          faceStarting.current = false;
          setFaceUp(false);
          live.current?.setVoiceSink(null);
        },
        // On screen, but nothing is coming out of her. Put the voice back on
        // the speaker rather than letting the hour run on in silence.
        onMute: () => {
          faceMute.current = true;
          live.current?.setVoiceSink(null);
          setLiveNote(t("lesson.tutorFaceMute", { name: TUTOR_NAME }));
        },
      });
      face.current = opened;
      showHer();
      setFaceUp(true);
      // The tutor's voice stops going to the speaker and starts going to her
      // mouth. If the socket is not up yet, `startTalking` does this instead.
      fedFace.current = false;

      // She is up. If nothing has been given to her by now, the quiet is not
      // hers — the spoken lesson is not producing any audio to give.
      window.setTimeout(() => {
        if (!face.current || fedFace.current) return;
        console.info("[tutor-face] no lesson audio ever reached her");
        setLiveNote(t("lesson.tutorFaceNoAudio", { name: TUTOR_NAME }));
      }, NO_AUDIO_MS);
    } catch (problem) {
      // Said rather than swallowed: "she did not appear" is not something the
      // student can act on, and it is not something the next person to look at
      // this can debug either.
      const detail = problem instanceof Error ? problem.message : "";
      setLiveNote(
        `${t("lesson.tutorFaceFallback", { name: TUTOR_NAME })}${detail ? ` (${detail})` : ""}`,
      );
    } finally {
      faceStarting.current = false;
    }
  }, [t]);

  /**
   * Say something in the tutor's voice, whichever one that is today.
   *
   * With the avatar up it is hers, out of the video tile, with a face moving
   * to match. Without it, the browser's synthesiser, exactly as before.
   */
  const sayAloud = useCallback((text: string) => {
    if (liveOwnsVoice.current) return;
    speak(text, voiceTag);
  }, [voiceTag]);

  /** The same, waiting until the sentence has actually been said. */
  const sayAloudAndWait = useCallback(async (text: string) => {
    if (liveOwnsVoice.current) return;
    await speakAndWait(text, voiceTag);
  }, [voiceTag]);

  /** Stop mid-sentence, whoever is talking. */
  const hush = useCallback(() => {
    face.current?.hush();
    stopSpeaking();
  }, []);

  /**
   * The element the avatar is playing on.
   *
   * A callback ref rather than a plain one, because the tutor moves between a
   * large tile and a small one and React rebuilds the element under her when
   * she does. A media element rebuilt is a media element with no stream on it;
   * this puts her back on whichever one is on screen now.
   */
  const holdFace = useCallback((element: HTMLVideoElement | null) => {
    faceVideo.current = element;
    showHer();
  }, []);

  const holdFaceAudio = useCallback((element: HTMLAudioElement | null) => {
    faceAudio.current = element;
    showHer();
  }, []);

  /**
   * Play a turn as it happened: each line written while it is being said.
   *
   * The tutor used to answer in a paragraph and then have its marks appear all
   * at once, at the end, in silence — the writing and the explaining were two
   * separate events and neither pointed at the other. A beat is one sentence
   * and the one line that goes with it, and they are played together: the text
   * types out at roughly the pace of the speech, the next beat waits for this
   * one to finish being said.
   *
   * `playing` is a token, not a boolean: if the student interrupts, the token
   * moves and any beat still running abandons itself rather than typing over
   * whatever comes next.
   */
  const playBeats = useCallback(async (beats: Beat[]) => {
    const mine = ++playing.current;
    // Put the paper in front of them before the first word. Waiting for the
    // mark count to change left the writing happening on a surface nobody had
    // open — the lines were real, and on a page the student was not looking at.
    if (beats.length) {
      setBoardOpen(false);
      setPaperOpen(true);
      setExplaining(true);
      // A new explanation. Whatever the last one left on the page is cleared,
      // or its lines sit there while these are written under them — which read
      // as the tutor writing the same thing twice.
      setNibRun(mine);
    }
    for (const [index, beat] of beats.entries()) {
      if (playing.current !== mine) return;

      // A page turn happens at the point in the explanation where the tutor
      // actually turned it, not at the start because the server got there
      // first. Half a beat's pause so it does not snap under the last word.
      if ("turn_to" in beat) {
        setTurnedTo(beat.turn_to);
        await new Promise((r) => setTimeout(r, 600));
        continue;
      }

      setMessages((all) => [...all, { role: "TUTOR", content: beat.say }]);
      setNibOn(beat.on);
      setNibStep(index);

      // Typed at a pace that lands with the sentence rather than racing it.
      const perCharacter = Math.max(18, Math.min(60,
        (beat.say.length * 55) / Math.max(beat.write.length, 1)));
      let shown = "";
      const typing = window.setInterval(() => {
        if (playing.current !== mine) return;
        shown = beat.write.slice(0, shown.length + 1);
        setNibAt(shown);
      }, perCharacter);

      if (!muted.current) await sayAloudAndWait(beat.say);
      else await new Promise((r) => setTimeout(r, beat.write.length * perCharacter));

      window.clearInterval(typing);
      if (playing.current !== mine) return;
      setNibAt(beat.write);   // left on the page; the reload replaces it in place
      setNibBusy(false);
      // A breath, not a gap. Longer and the explanation reads as a slideshow.
      await new Promise((r) => setTimeout(r, 150));
    }
    if (playing.current === mine) {
      // Not cleared: the line stays on the paper until the reload puts the
      // real mark in the same place. Clearing it made the writing appear and
      // then vanish, which is the thing that looked broken.
      // Now the paper may catch up: one reload, at the end, instead of one per
      // line in the middle of the explanation.
      setExplaining(false);
    }
  }, [sayAloudAndWait]);

  /**
   * Trace out what the tutor has just written, a character at a time.
   *
   * A spoken lesson has no beats — the pacing of the written one comes from
   * the sentence being said alongside each line, and here the sentence is
   * audio. So the paper only ever reloaded, and a whole line appeared at once
   * on a page the student had not been watching: she said "look, I'll write it
   * down", and the writing was already there.
   *
   * This is the same nib the written lesson uses, driven by the marks the
   * agent reports as it makes them. `explaining` holds the reload until the
   * last character is down, so what streams in is replaced in place by the
   * real mark rather than appearing twice.
   */
  const traceHerWriting = useCallback(async (lines: { text: string; on: string }[]) => {
    if (!lines.length) return;
    const mine = ++playing.current;
    setBoardOpen(false);
    setPaperOpen(true);
    setNibRun(mine);

    for (const [index, line] of lines.entries()) {
      if (playing.current !== mine) return;
      setNibOn(line.on);
      setNibStep(index);
      setNibBusy(true);
      let shown = "";
      await new Promise<void>((written) => {
        const pen = window.setInterval(() => {
          if (playing.current !== mine) {
            window.clearInterval(pen);
            return written();
          }
          shown = line.text.slice(0, shown.length + 1);
          setNibAt(shown);
          if (shown.length >= line.text.length) {
            window.clearInterval(pen);
            written();
          }
        }, HAND_MS);
      });
      if (playing.current !== mine) return;
      setNibAt(line.text);
      setNibBusy(false);
      // A breath between lines, not a gap.
      await new Promise((r) => setTimeout(r, 150));
    }
    if (playing.current === mine) setExplaining(false);
  }, []);

  /**
   * One turn with the tutor.
   *
   * The student's words go on screen before the request leaves, because a
   * message that appears only once a model has answered feels like it was not
   * heard. `said` empty is the opening turn — the tutor greets rather than
   * waiting to be spoken to first.
   */
  const takeTurn = useCallback(async (said: string) => {
    setThinking(true);
    // Hold the paper from here, not from when the beats start playing.
    //
    // The marks are written server-side before the reply comes back, so the
    // two-second poll could see them and reload the paper while the answer was
    // still in flight. Then the explanation typed the same lines in on top of
    // the real ones, and the tutor appeared to write everything twice.
    setExplaining(true);
    try {
      const response = await fetch(`/api/lesson/${bookingId}/turn`, {
        method: "POST",
        headers: { "content-type": "application/json" },
        // Presence is only ever reported false when we actually know it.
        //
        // The camera is the only detector there is, so with it switched off
        // there is nothing to detect with and the answer is "present" — the
        // learner is in the call. Reporting the watcher's `false` there would
        // suspend every lesson taught with the camera off, which is most of
        // them: the app nudges people to turn it on precisely because they
        // have not. And somebody who just spoke or typed is present whatever
        // the camera thinks.
        body: JSON.stringify({
          said,
          present: Boolean(said) || cameraOff || presence.current.latest.present,
          // Only when it has changed: the same page of handwriting sent every
          // turn would have the tutor marking the same answer over and over.
          work: ink.current !== inkSent.current ? ink.current : null,
        }),
      });
      const body = await response.json();
      if (!response.ok) {
        setTutorProblem(body?.error ?? null);
        setExplaining(false);
        return;
      }
      setTutorProblem(null);
      inkSent.current = ink.current;
      setMaterial(body.showing_material ?? null);
      followTheTutor({ board: body.board, page: body.showing_page,
                       marks: body.marks_made });
      // The beats are the explanation, played line by line; `said` is whatever
      // was not part of one — usually the question at the end. It comes AFTER
      // them, or the two voices talk over each other.
      const beats = (body.beats ?? []) as Beat[];
      const rest = body.said?.trim() ?? "";
      if (!beats.length) setExplaining(false);
      if (beats.length) {
        void playBeats(beats).then(() => {
          if (!rest) return;
          setMessages((all) => [...all, { role: "TUTOR", content: rest }]);
          if (!muted.current && !heardLiveAudio.current) sayAloud(rest);
        });
      } else if (rest) {
        setMessages((all) => [...all, { role: "TUTOR", content: rest }]);
        if (!tutorMuted && !heardLiveAudio.current) sayAloud(rest);
      }
    } catch {
      setTutorProblem(t("lesson.tutorUnreachable", { name: TUTOR_NAME }));
      setExplaining(false);
    } finally {
      setThinking(false);
    }
  }, [bookingId, cameraOff, followTheTutor, playBeats, sayAloud, t, tutorMuted]);

  // Presence, sampled once a second off the video the learner can already see.
  // Nothing leaves the browser but the boolean.
  useEffect(() => {
    const id = setInterval(() => {
      const reading = presence.current.sample(localVideoRef.current, !cameraOff);
      setPresentNow(reading.present);
    }, 1000);
    return () => clearInterval(id);
  }, [cameraOff]);

  // The opening turn, once, when the student arrives. The guard is a ref rather
  // than the message list: in development the effect runs twice, and a lesson
  // that greets you twice looks broken.
  const opened = useRef(false);
  useEffect(() => {
    if (opened.current || live.current) return;
    opened.current = true;
    takeTurn("");
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  // Follow the conversation down as it grows.
  useEffect(() => {
    transcriptEnd.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages.length, thinking]);

  const send = async () => {
    const said = draft.trim();
    if (!said || thinking) return;
    // Answering is interrupting: whatever the tutor was still saying is about
    // the previous question, and any line still typing out belongs to it.
    hush();
    playing.current += 1;
    setNibAt(null);
    setNibBusy(false);
    setExplaining(false);
    setDraft("");
    setMessages((all) => [...all, { role: "STUDENT", content: said }]);
    // In a spoken lesson the socket is the channel: typing goes down it too,
    // so the tutor answers out loud rather than in a separate written turn.
    // A live session that has never made a sound is not a channel to send an
    // answer down: it goes through the typed turn, which always replies.
    if (live.current && heardLiveAudio.current) live.current.say(said);
    else await takeTurn(said);
  };

  /**
   * Listen with the browser instead of the socket.
   *
   * Used when the live session cannot hear — which, with the preview live
   * models, is most of the time: it connects, plays an introduction and then
   * takes nothing in, so the student talks into a socket that is not listening
   * and the lesson looks frozen. The browser's own recogniser drives the typed
   * turn loop, which has never failed, and the tutor answers in the browser's
   * voice. Not as good as native audio; it works.
   */
  const openEar = useCallback(() => {
    if (!voice.listen) return;
    stopEar.current();
    setEarOpen(true);
    stopEar.current = listenContinuously(
      voiceTag,
      (heard) => {
        setMessages((all) => [...all, { role: "STUDENT", content: heard }]);
        void takeTurn(heard);
      },
      (reason) => { setEarOpen(false); setLiveNote(reason); },
    );
  }, [takeTurn, voice.listen, voiceTag]);

  const closeEar = useCallback(() => {
    stopEar.current();
    stopEar.current = () => {};
    setEarOpen(false);
  }, []);

  /**
   * Hand the lesson over to voice.
   *
   * Transcript lines arrive in fragments as the model recognises them, so a
   * fragment from the same speaker extends the last line rather than starting a
   * new one — otherwise a sentence arrives as eight separate messages.
   */
  const startTalking = useCallback(async () => {
    if (liveState !== "off") return;
    setLiveState("starting");
    setLiveNote(null);
    heardLiveAudio.current = false;
    liveOwnsVoice.current = true;
    hush();
    // Abandon the written lesson, not just the sentence it is on.
    //
    // The class opens on the typed loop, which explains beat by beat in the
    // browser's own voice. Joining the audio starts a second tutor saying the
    // same greeting out of the avatar's mouth, and cancelling one utterance is
    // not enough — the loop simply moves to the next beat and speaks again, so
    // the student hears two teachers talking over each other. Moving the token
    // makes any explanation still running stand down, which is exactly what
    // answering mid-sentence already does.
    playing.current += 1;
    setNibAt(null);
    setNibBusy(false);
    setExplaining(false);
    // Her first, then the socket — but never for long.
    //
    // The tutor opens the hour the moment the socket is ready, and she takes
    // several seconds longer than that to arrive. Started alongside, her
    // greeting was over before she was on screen, so a lesson began with a
    // disembodied voice and a photograph. Waiting means the first words the
    // student hears come out of her mouth. The cap is there because a class
    // must never be held up by a face: past it, the lesson starts without her
    // and she joins when she can.
    await Promise.race([
      showFace(),
      new Promise((done) => window.setTimeout(done, FACE_HEADSTART_MS)),
    ]);
    try {
      live.current = await startLiveLesson(bookingId, (event) => {
        if (event.type === "audio_started") {
          // The socket really is a call. The browser's ear stands down so the
          // two are not both listening.
          heardLiveAudio.current = true;
          closeEar();
        }
        // The student has talked over the tutor. Her mouth stops with the rest
        // of the turn — an avatar that finishes the sentence anyway is not
        // listening, whatever the socket has already done about it.
        if (event.type === "interrupted") { face.current?.hush(); showVoice(0); }
        // The turn is finished, so the tail of it should not sit in the buffer
        // waiting for a packet's worth of audio that is never coming.
        if (event.type === "turn_complete") { face.current?.endTurn(); showVoice(0); }
        if (event.type === "transcript") {
          setMessages((all) => {
            const last = all[all.length - 1];
            const sameSpeaker = last?.role === event.role;
            // Fragments build a running caption as the words are recognised;
            // the final frame repeats the whole turn, so it replaces the
            // caption rather than being appended to it.
            if (sameSpeaker && event.final) {
              return [...all.slice(0, -1), { role: last.role, content: event.text }];
            }
            if (sameSpeaker) {
              return [...all.slice(0, -1),
                      { role: last.role, content: last.content + event.text }];
            }
            return [...all, { role: event.role, content: event.text }];
          });
        }
        // Heard nothing, but the tutor said something: read it aloud. This is
        // the floor — whatever else fails, the student hears the lesson. The
        // avatar is not part of it: she is fed the socket's audio directly, so
        // when there is audio she is already saying it, and when there is not
        // there is nothing for her to say.
        if (event.type === "transcript" && event.final && event.role === "TUTOR"
            && !heardLiveAudio.current && !muted.current) {
          sayAloud(event.text);
        }
        if (event.type === "paper") {
          const written = event.written ?? [];
          // Before the mark count reaches the paper, or it reloads with the
          // line already on it and there is nothing left to trace.
          if (written.length) setExplaining(true);
          setMaterial((event.showing_material as SharedMaterial | null) ?? null);
          followTheTutor({ board: event.board, page: event.showing_page,
                           marks: event.marks });
          void traceHerWriting(written);
        }
        if (event.type === "board") followTheTutor({ board: event.lines });
        if (event.type === "closed") {
          setLiveState("off");
          liveOwnsVoice.current = false;
          live.current = null;
          setLiveNote(event.detail);
        }
        if (event.type === "error") {
          // The spoken tutor is gone, so the call falls back to the typed loop
          // the lesson has always had rather than sitting there silent.
          setLiveNote(event.detail);
          setLiveState("off");
          live.current = null;
          heardLiveAudio.current = false;
          liveOwnsVoice.current = false;
          openEar();
        }
      });
      // Before the state change, because the greeting starts arriving inside
      // the same tick and the effect above cannot run until React renders. A
      // frame that misses the sink is a word out of the speaker instead of her
      // mouth, which is the echo the student hears.
      const ear = herEar();
      if (ear) live.current.setVoiceSink(ear);
      // Only meaningful while she is a photograph: with a real avatar the
      // audio never reaches the speaker to be measured, and her own mouth is
      // moving anyway.
      live.current.setVoiceLevel(showVoice);
      setLiveState("on");

      // Give the socket a few seconds to actually make a sound. If it does not,
      // it is not going to: end it, so the microphone is not feeding a session
      // that cannot hear, and listen with the browser instead.
      window.setTimeout(() => {
        if (!heardLiveAudio.current && live.current) {
          live.current.stop();
          live.current = null;
          setLiveState("off");
          liveOwnsVoice.current = false;
          setLiveNote(t("lesson.voiceFallback", { name: TUTOR_NAME }));
          openEar();
        }
      }, 8000);
    } catch {
      setLiveState("off");
      live.current = null;
      liveOwnsVoice.current = false;
      // No live audio at all — the browser can still listen and speak.
      openEar();
    }
  }, [bookingId, closeEar, followTheTutor, hush, liveState, openEar, sayAloud,
      showFace, t, traceHerWriting]);

  /**
   * Point the lesson's voice at the tutor's mouth, once both exist.
   *
   * They arrive independently and in either order — the socket in a second or
   * two, the avatar in closer to ten — and this used to be wired at whichever
   * of the two happened to finish. Both misses were silent: the socket looked
   * for a face that had not arrived, the face looked for a socket that the
   * eight-second watchdog had already torn down, and the result either way was
   * a tutor sitting there perfectly connected with nothing ever reaching her.
   * Reconciling it here means it does not matter which one is late.
   */
  useEffect(() => {
    if (liveState !== "on") return;
    const ear = herEar();
    if (ear) live.current?.setVoiceSink(ear);
  }, [liveState, faceUp]);

  const stopTalking = useCallback(() => {
    live.current?.stop();
    live.current = null;
    heardLiveAudio.current = false;
    liveOwnsVoice.current = false;
    setLiveState("off");
  }, []);

  // A lesson left behind should not keep listening — or keep a paid avatar
  // session running in a tab nobody is in.
  useEffect(() => () => {
    live.current?.stop();
    stopEar.current();
    face.current?.stop();
  }, []);

  // Whatever is showing on the main stage. The paper, the board and a screen
  // share take it over; the tutor drops to a small tile beside the learner
  // while they do.
  const stage: "tutor" | "screen" | "board" | "paper" =
    sharing ? "screen" : boardOpen ? "board" : paperOpen ? "paper" : "tutor";

  // The webcam is requested only when asked for, so arriving at a class never
  // trips a permission prompt and the browser light stays off until wanted.
  const startCamera = useCallback(async () => {
    setNudgeDismissed(true);
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ video: true, audio: false });
      streamRef.current = stream;
      if (localVideoRef.current) localVideoRef.current.srcObject = stream;
      setCameraDenied(false);
      setCameraOff(false);
    } catch {
      setCameraDenied(true);
    }
  }, []);

  const stopCamera = useCallback(() => {
    streamRef.current?.getTracks().forEach((tr) => tr.stop());
    streamRef.current = null;
    if (localVideoRef.current) localVideoRef.current.srcObject = null;
    setCameraOff(true);
  }, []);

  // Screen share. Ending it from the browser's own "Stop sharing" bar has to put
  // the stage back too, hence the track listener rather than only our button.
  const startShare = useCallback(async () => {
    try {
      const stream = await navigator.mediaDevices.getDisplayMedia({ video: true, audio: false });
      screenStreamRef.current = stream;
      setSharing(true);
      setBoardOpen(false);
      stream.getVideoTracks()[0]?.addEventListener("ended", () => {
        screenStreamRef.current = null;
        setSharing(false);
      });
    } catch {
      // The learner dismissed the picker — nothing to report.
    }
  }, []);

  const stopShare = useCallback(() => {
    screenStreamRef.current?.getTracks().forEach((tr) => tr.stop());
    screenStreamRef.current = null;
    setSharing(false);
  }, []);

  useEffect(() => {
    if (sharing && screenVideoRef.current && screenStreamRef.current) {
      screenVideoRef.current.srcObject = screenStreamRef.current;
    }
  }, [sharing]);

  // Stop every track on unmount, however the learner left. The tutor's voice
  // has to be cancelled explicitly — speech synthesis outlives the page that
  // started it, and a lesson you have left should not keep talking.
  useEffect(
    () => () => {
      streamRef.current?.getTracks().forEach((tr) => tr.stop());
      screenStreamRef.current?.getTracks().forEach((tr) => tr.stop());
      stopSpeaking();
      face.current?.stop();
    },
    []
  );

  const toggleMic = () => {
    // On a call the microphone button mutes; it does not hold a channel open
    // while pressed. If the audio has not been joined yet, pressing it joins —
    // a browser will not open a microphone without a gesture, and this is the
    // obvious one to spend.
    if (liveState === "off" && !earOpen) {
      if (voice.live) void startTalking();
      else {
        // `startTalking` brings the face up itself; this is the other way in.
        void showFace();
        openEar();
      }
      return;
    }
    setMicMuted((m) => {
      const next = !m;
      live.current?.setMuted(next);
      // The browser's recogniser has no mute, so muting closes it and
      // unmuting opens it again.
      if (next) closeEar(); else if (!heardLiveAudio.current) openEar();
      return next;
    });
  };

  const toggleCamera = () => {
    if (cameraOff) startCamera();
    else stopCamera();
  };

  const leaveCall = async () => {
    setLeaving(true);
    streamRef.current?.getTracks().forEach((t) => t.stop());
    screenStreamRef.current?.getTracks().forEach((t) => t.stop());
    face.current?.stop();
    // Tell the tutor the room is empty, so it stops holding the hour open and
    // flushes anything it has not yet written on the paper. Best effort: a
    // student leaving is never blocked by the agent.
    await fetch(`/api/lesson/${bookingId}/end`, { method: "POST" }).catch(() => {});
    await completeBooking(bookingId);
    router.push("/dashboard");
  };

  /**
   * How much room the two of you get while something else is on the stage.
   *
   * A fixed strip down the side was too mean to read a face in: the tutor was
   * a thumbnail beside a worksheet, which is the wrong way round for a class
   * where somebody is teaching you. It is a width the student sets by dragging
   * the edge, remembered between lessons, and it can be folded away entirely
   * when the paper is the only thing that matters.
   */
  const [railOpen, setRailOpen] = useState(true);
  /**
   * The width the student last chose, read the same way as every other fact
   * that differs between the server and the browser. Reading it during render
   * would hydrate a 320px column over a 420px one; reading it in an effect
   * would set state on mount just to correct the guess.
   */
  const storedRail = useSyncExternalStore(neverChanges, readRail, railOnTheServer);
  /** The width while it is being dragged, which outranks the stored one. */
  const [draggedRail, setDraggedRail] = useState<number | null>(null);
  const railWidth = draggedRail ?? storedRail;
  const dragging = useRef(false);

  const dragRail = useCallback((event: React.PointerEvent<HTMLDivElement>) => {
    dragging.current = true;
    event.currentTarget.setPointerCapture(event.pointerId);
  }, []);

  const moveRail = useCallback((event: React.PointerEvent<HTMLDivElement>) => {
    if (!dragging.current) return;
    // Measured from the right edge of the window, because that is the edge the
    // rail is pinned to; from the left it drifts whenever the panel opens.
    setDraggedRail(clampRail(window.innerWidth - event.clientX));
  }, []);

  const dropRail = useCallback((event: React.PointerEvent<HTMLDivElement>) => {
    if (!dragging.current) return;
    dragging.current = false;
    event.currentTarget.releasePointerCapture(event.pointerId);
    keepRail(clampRail(window.innerWidth - event.clientX));
  }, []);

  const nudgeRail = useCallback((by: number) => {
    setDraggedRail((width) => {
      const next = clampRail((width ?? readRail()) + by);
      keepRail(next);
      return next;
    });
  }, []);

  const tutorLabel = subjectName ? `${TUTOR_NAME} · ${subjectName}` : TUTOR_NAME;

  const tutorTile = (
    <div
      className="relative h-full min-h-0 overflow-hidden rounded-2xl bg-[#17181c]"
    >
      {/* The tutor herself, filmed and rendered as she speaks. Never muted:
          her voice is on this track, and it is the lesson's voice. */}
      <video
        ref={holdFace}
        autoPlay
        playsInline
        muted
        className={`h-full w-full object-cover ${faceUp ? "" : "hidden"}`}
      />
      {/* Her voice. Separate from the picture because the SDK renders the two
          onto separate elements, and never muted — this is the lesson. */}
      <audio ref={holdFaceAudio} autoPlay />
      {!faceUp && (
        <div ref={stillTile} className="tutor-still h-full w-full">
          <TutorPortrait />
          <span aria-hidden="true" className="tutor-still-glow" />
        </div>
      )}

      <div className="absolute bottom-2 left-2 z-10 flex flex-wrap items-center gap-2">
        <span className="flex items-center gap-2 rounded-md bg-black/60 px-2.5 py-1 text-xs font-medium">
          {stage === "tutor" ? tutorLabel : TUTOR_NAME}
        </span>
      </div>
    </div>
  );

  const studentTile = (
    <div
      className="relative h-full min-h-0 overflow-hidden rounded-2xl bg-[#26272b]"
    >
      <video
        ref={localVideoRef}
        autoPlay
        playsInline
        muted
        className={`h-full w-full object-cover ${cameraOff ? "hidden" : ""}`}
      />
      {/* Camera off shows who you are, not a dead rectangle: your picture if you
          have one, otherwise your initial. */}
      {cameraOff && (
        <div className="flex h-full w-full items-center justify-center">
          {studentImage ? (
            // eslint-disable-next-line @next/next/no-img-element
            <img
              src={studentImage}
              alt=""
              className={`rounded-full object-cover ${stage === "tutor" ? "h-28 w-28" : "h-12 w-12"}`}
            />
          ) : (
            <span
              className={`flex items-center justify-center rounded-full bg-[#3f4048] font-semibold ${
                stage === "tutor" ? "h-28 w-28 text-4xl" : "h-12 w-12 text-lg"
              }`}
            >
              {studentName.trim().slice(0, 1).toUpperCase() || "?"}
            </span>
          )}
        </div>
      )}
      <span className="absolute bottom-2 left-2 rounded-md bg-black/60 px-2.5 py-1 text-xs font-medium">
        {t("lesson.you")}
      </span>
    </div>
  );

  return (
    <div className="flex h-dvh w-full flex-col bg-[#0b0b0d] text-[#e8e9ed]">
      {/* Meeting bar. Zoom keeps identity and elapsed time out of the way at the
          top so the stage stays the whole focus. */}
      <header className="flex items-center gap-3 px-4 py-2.5 text-xs">
        <span className="flex items-center gap-2 font-medium">
          <span aria-hidden="true" className="h-2 w-2 rounded-full bg-[#22c55e]" />
          {tutorLabel}
        </span>
        <span className="ml-auto tabular-nums text-[#9a9ca5]">{formatElapsed(elapsed)}</span>
      </header>

      <div className="flex min-h-0 flex-1 gap-2 px-2 pb-2">
        {/* Two layouts, one set of tiles. Nothing is shared: the class is the
            two of you, side by side. Something is shared: it takes the stage
            and the pair stand down the right, tutor first. */}
        {stage === "tutor" ? (
          <div className="grid min-h-0 flex-1 grid-rows-2 gap-2 sm:grid-cols-2 sm:grid-rows-1">
            {tutorTile}
            {studentTile}
          </div>
        ) : (
          <>
            <main className="relative min-w-0 flex-1 overflow-hidden rounded-xl bg-[#17181c]">
              {stage === "screen" ? (
                <video
                  ref={screenVideoRef}
                  autoPlay
                  playsInline
                  muted
                  className="h-full w-full object-contain"
                />
              ) : stage === "board" ? (
                <Whiteboard tutorLines={board} onClose={() => setBoardOpen(false)} />
              ) : (
                <LessonPaper
                  bookingId={bookingId}
                  onClose={() => setPaperOpen(false)}
                  onInk={(png) => { ink.current = png; }}
                  writing={nibAt}
                  writingOn={nibOn}
                  writingStep={nibStep}
                  writingBusy={nibBusy}
                  writingRun={nibRun}
                  page={turnedTo}
                  hold={explaining}
                />
              )}

              {/* What the tutor has put up. It covers the paper rather than
                  sitting beside it: a student looking at two documents is
                  looking at neither, and the paper is one click away. */}
              {material && stage !== "screen" && (
                <SharedMaterialPanel material={material} onClose={() => setMaterial(null)} />
              )}
              {sharing && (
                <span className="absolute left-3 top-3 rounded-md bg-black/60 px-2.5 py-1 text-[11px] text-[#9a9ca5]">
                  {t("lesson.sharingBanner")}
                </span>
              )}
            </main>

            {/* The handle between the stage and the pair. `separator` with a
                value is what a screen reader needs to say "you can move this",
                and the arrow keys do the same job as the drag for anyone not
                using a pointer. */}
            {railOpen && (
              <div
                role="separator"
                aria-orientation="vertical"
                aria-label={t("lesson.resizeTiles")}
                aria-valuenow={railWidth}
                aria-valuemin={RAIL_MIN}
                aria-valuemax={RAIL_MAX}
                tabIndex={0}
                onPointerDown={dragRail}
                onPointerMove={moveRail}
                onPointerUp={dropRail}
                onKeyDown={(event) => {
                  const step = event.shiftKey ? 48 : 16;
                  if (event.key === "ArrowLeft") nudgeRail(step);
                  else if (event.key === "ArrowRight") nudgeRail(-step);
                  else return;
                  event.preventDefault();
                }}
                className="group hidden w-2 shrink-0 cursor-col-resize touch-none items-center justify-center rounded-full focus-visible:outline focus-visible:outline-2 focus-visible:outline-[#0e71eb] sm:flex"
              >
                <span
                  aria-hidden="true"
                  className="h-10 w-1 rounded-full bg-white/15 transition-colors group-hover:bg-white/40"
                />
              </div>
            )}

            <div
              className="relative flex shrink-0 flex-col gap-2 overflow-y-auto"
              style={{ width: railOpen ? `${railWidth}px` : "5.5rem" }}
            >
              <button
                onClick={() => setRailOpen((open) => !open)}
                aria-expanded={railOpen}
                className="absolute right-2 top-2 z-20 flex h-7 w-7 items-center justify-center rounded-full bg-black/60 text-[#e8e9ed] transition-colors hover:bg-black/80"
                title={railOpen ? t("lesson.foldTiles") : t("lesson.unfoldTiles")}
              >
                <span aria-hidden="true" className="text-sm leading-none">
                  {railOpen ? "›" : "‹"}
                </span>
                <span className="sr-only">
                  {railOpen ? t("lesson.foldTiles") : t("lesson.unfoldTiles")}
                </span>
              </button>

              {/* Square, and only as tall as they are wide. Stretching two tiles
                  down the whole column made a person into a letterbox. */}
              <div className="aspect-square min-h-0 shrink-0">{tutorTile}</div>
              <div className="aspect-square min-h-0 shrink-0">{studentTile}</div>
            </div>
          </>
        )}

        {panelOpen && (
          <aside className="hidden w-80 shrink-0 flex-col rounded-xl bg-[#17181c] md:flex">
            <h2 className="border-b border-white/10 px-4 py-3 text-sm font-semibold">
              {t("lesson.transcript")}
            </h2>
            <div className="flex flex-1 flex-col gap-3 overflow-y-auto p-4">
              {messages.length === 0 && !thinking && (
                <p className="text-sm text-[#9a9ca5]">{t("lesson.transcriptEmpty")}</p>
              )}
              {messages.map((m, i) => (
                <div key={i}>
                  <p className="text-[11px] font-medium text-[#9a9ca5]">
                    {m.role === "TUTOR" ? TUTOR_NAME : t("lesson.you")}
                  </p>
                  <p className="mt-0.5 text-sm leading-relaxed">{m.content}</p>
                </div>
              ))}
              {thinking && (
                <p className="flex items-center gap-2 text-[11px] font-medium text-[#9a9ca5]">
                  <span aria-hidden="true" className="h-1.5 w-1.5 animate-pulse rounded-full bg-[#22c55e]" />
                  {t("lesson.tutorThinking", { name: TUTOR_NAME })}
                </p>
              )}
              {(liveState === "on" || earOpen) && (
                <p className="flex items-center gap-2 text-[11px] font-medium text-[#22c55e]">
                  <span aria-hidden="true" className="h-1.5 w-1.5 animate-pulse rounded-full bg-[#22c55e]" />
                  {t("lesson.speaking")}
                </p>
              )}
              {liveNote && (
                <p className="rounded-lg bg-white/5 px-3 py-2 text-xs text-[#9a9ca5]">
                  {liveNote}
                </p>
              )}
              {tutorProblem && (
                <p className="rounded-lg bg-[#e02d3c]/15 px-3 py-2 text-xs text-[#ff8a94]">
                  {tutorProblem}
                </p>
              )}
              <div ref={transcriptEnd} />
            </div>

            {/* Typing, not talking. Speech is the lesson's natural channel and
                this is not it — but a class you cannot answer in is a video,
                and this is what makes it a conversation today. */}
            <form
              onSubmit={(e) => {
                e.preventDefault();
                send();
              }}
              className="flex items-center gap-2 border-t border-white/10 p-3"
            >
              <input
                value={draft}
                onChange={(e) => setDraft(e.target.value)}
                placeholder={t("lesson.answerPlaceholder")}
                aria-label={t("lesson.answerPlaceholder")}
                className="min-w-0 flex-1 rounded-lg bg-[#26272b] px-3 py-2 text-sm outline-none placeholder:text-[#6e7079] focus:ring-1 focus:ring-[#0e71eb]"
              />
              <button
                type="submit"
                disabled={thinking || !draft.trim()}
                className="rounded-lg bg-[#0e71eb] px-3 py-2 text-xs font-semibold text-white transition-opacity hover:opacity-90 disabled:opacity-40"
              >
                {t("lesson.answerSend")}
              </button>
            </form>
          </aside>
        )}
      </div>

      {/* A call you have to find the audio in is not a call. This sits where
          the camera nudge does, and goes away the moment the tutor can hear. */}
      {(voice.live || voice.listen) && liveState === "off" && !earOpen && (
        <div className="mx-2 mb-2 flex flex-wrap items-center gap-3 rounded-lg bg-[#17181c] px-4 py-3">
          <p className="min-w-0 flex-1 text-sm text-[#c9cbd2]">{t("lesson.joinAudioNudge", { name: TUTOR_NAME })}</p>
          <button
            onClick={() => void startTalking()}
            className="rounded-lg bg-[#0e71eb] px-3 py-1.5 text-xs font-semibold text-white transition-opacity hover:opacity-90"
          >
            {t("lesson.joinAudio")}
          </button>
        </div>
      )}

      {cameraOff && !nudgeDismissed && !cameraDenied && (
        <div className="mx-2 mb-2 flex flex-wrap items-center gap-3 rounded-lg bg-[#17181c] px-4 py-3">
          <p className="min-w-0 flex-1 text-sm text-[#c9cbd2]">{t("lesson.cameraNudge")}</p>
          <button
            onClick={startCamera}
            className="rounded-lg bg-[#0e71eb] px-3 py-1.5 text-xs font-semibold text-white transition-opacity hover:opacity-90"
          >
            {t("lesson.cameraNudgeYes")}
          </button>
          <button
            onClick={() => setNudgeDismissed(true)}
            className="rounded-lg px-3 py-1.5 text-xs font-medium text-[#9a9ca5] transition-colors hover:bg-white/10"
          >
            {t("lesson.cameraNudgeNo")}
          </button>
        </div>
      )}

      {cameraDenied && (
        <div className="mx-2 mb-2 rounded-lg bg-[#e02d3c]/15 px-4 py-2 text-sm text-[#ff8a94]">
          {t("lesson.cameraDenied")}
        </div>
      )}

      {/* Control bar: icon above label, leave held apart on the right. */}
      <footer className="flex items-center gap-1 bg-[#1c1d22] px-3 py-2.5 pb-[max(0.625rem,env(safe-area-inset-bottom))]">
        <ControlButton
          onClick={toggleMic}
          active={liveState === "on" && micMuted}
          label={
            liveState === "starting" ? t("lesson.connecting")
            : liveState === "off" && !earOpen ? t("lesson.joinAudio")
            : micMuted ? t("lesson.unmute")
            : t("lesson.mute")
          }
          icon={(liveState === "on" || earOpen) && !micMuted ? <MicIcon /> : <MicOffIcon />}
        />
        <ControlButton
          onClick={toggleCamera}
          active={cameraOff}
          label={
            cameraOff ? t("lesson.startCamera")
            : presentNow ? t("lesson.cameraSeesYou")
            : t("lesson.cameraSeesNobody")
          }
          icon={cameraOff ? <VideoOffIcon /> : <VideoIcon />}
        />
        {voice.speak && (
          <ControlButton
            onClick={() => {
              setTutorMuted((m) => !m);
              hush();
              // A spoken lesson's voice comes down the socket, so muting it
              // means ending the socket rather than cancelling an utterance.
              // The face stays: a tutor who has stopped talking is still in the
              // room, and she is not free to bring back.
              if (liveState !== "off") stopTalking();
            }}
            active={tutorMuted}
            label={tutorMuted ? t("lesson.unmuteTutor") : t("lesson.muteTutor")}
            icon={tutorMuted ? <SpeakerOffIcon /> : <SpeakerIcon />}
          />
        )}
        <ControlButton
          onClick={sharing ? stopShare : startShare}
          active={sharing}
          label={sharing ? t("lesson.stopShare") : t("lesson.share")}
          icon={<ShareIcon />}
        />
        <ControlButton
          onClick={() => {
            setPaperOpen((o) => !o);
            setBoardOpen(false);
            if (sharing) stopShare();
          }}
          active={paperOpen}
          label={paperOpen ? t("lesson.closePaper") : t("lesson.paper")}
          icon={<PaperIcon />}
        />
        <ControlButton
          onClick={() => {
            setBoardOpen((o) => !o);
            if (sharing) stopShare();
          }}
          active={boardOpen}
          label={boardOpen ? t("lesson.closeBoard") : t("lesson.board")}
          icon={<BoardIcon />}
        />
        <ControlButton
          onClick={() => setPanelOpen((o) => !o)}
          className="hidden md:flex"
          label={t("lesson.transcript")}
          icon={<TranscriptIcon />}
        />

        <button
          onClick={leaveCall}
          disabled={leaving}
          className="ml-auto rounded-lg bg-[#e02d3c] px-4 py-2 text-sm font-semibold text-white transition-opacity hover:opacity-90 disabled:opacity-60"
        >
          {leaving ? t("lesson.leaving") : t("lesson.leave")}
        </button>
      </footer>
    </div>
  );
}

/**
 * A piece of the lesson's material, as the tutor put it up.
 *
 * Rendered from the fields the agent sends and nothing else — there is no
 * answer key in the payload, so there is none to leak here. The markdown is
 * shown as written rather than parsed: a lesson's content is short, and a
 * markdown parser in a call screen is a dependency and an injection surface
 * for one bold word.
 */
function SharedMaterialPanel({
  material,
  onClose,
}: {
  material: SharedMaterial;
  onClose: () => void;
}) {
  const t = useT();
  return (
    <div className="absolute inset-0 z-10 overflow-y-auto bg-[#f4f2ef] p-6 text-[#17181c] sm:p-10">
      <div className="mx-auto max-w-2xl">
        <div className="flex items-start gap-4">
          <div className="min-w-0 flex-1">
            <p className="text-[11px] font-semibold uppercase tracking-widest text-[#7b3fe4]">
              {material.kind.replace(/_/g, " ")}
            </p>
            <h2 className="mt-1 text-2xl font-bold leading-tight">{material.title}</h2>
            {material.instruction && (
              <p className="mt-1 text-sm italic text-[#5b5f66]">{material.instruction}</p>
            )}
          </div>
          <button
            onClick={onClose}
            aria-label={t("lesson.closeMaterial")}
            className="shrink-0 rounded-lg px-3 py-1.5 text-xs font-medium text-[#5b5f66] transition-colors hover:bg-black/5"
          >
            {t("lesson.closeMaterial")}
          </button>
        </div>

        {material.content && (
          <p className="mt-5 whitespace-pre-wrap text-[15px] leading-relaxed">
            {material.content}
          </p>
        )}

        {material.exercises.length > 0 && (
          <ol className="mt-6 space-y-3">
            {material.exercises.map((exercise, i) => (
              <li key={exercise.id} className="flex gap-3 text-[15px]">
                <span className="w-5 shrink-0 font-semibold text-[#7b3fe4]">{i + 1}.</span>
                <span className="min-w-0">
                  {exercise.instructions && (
                    <span className="mr-2 italic text-[#5b5f66]">{exercise.instructions}</span>
                  )}
                  {exercise.prompt}
                  {exercise.options.length > 0 && (
                    <span className="ml-2 text-[#5b5f66]">({exercise.options.join(" · ")})</span>
                  )}
                </span>
              </li>
            ))}
          </ol>
        )}
      </div>
    </div>
  );
}

/**
 * The tutor when there is no live avatar to show.
 *
 * A photograph filling the tile, not a badge in the middle of one: the tile is
 * a person's place on a call, and a circle floating in the dark reads as an
 * account rather than a teacher. It is the same framing a switched-off camera
 * would leave behind, which is what this is.
 *
 * The stillness is the honest part — nothing here pretends to be lip sync. It
 * breathes and brightens with the voice, so it is visibly her speaking and not
 * a frozen image over somebody else's audio.
 */
function TutorPortrait() {
  return (
    // eslint-disable-next-line @next/next/no-img-element
    <img
      src="/marketing/tutor-marieke.jpg"
      alt={TUTOR_NAME}
      className="tutor-still-face h-full w-full object-cover"
    />
  );
}

/** mm:ss, or h:mm:ss once a lesson runs past the hour. */
function formatElapsed(seconds: number) {
  const s = String(seconds % 60).padStart(2, "0");
  const m = Math.floor(seconds / 60);
  if (m < 60) return `${String(m).padStart(2, "0")}:${s}`;
  return `${Math.floor(m / 60)}:${String(m % 60).padStart(2, "0")}:${s}`;
}

/**
 * Icon over label, the shape Zoom uses. `active` marks the state that needs
 * noticing — muted, camera off — rather than the resting state.
 */
function ControlButton({
  onClick,
  onPointerDown,
  onPointerUp,
  onPointerLeave,
  icon,
  label,
  active = false,
  className = "",
}: {
  onClick?: () => void;
  /** Press-and-hold, for the talk button. */
  onPointerDown?: () => void;
  onPointerUp?: () => void;
  onPointerLeave?: () => void;
  icon: ReactNode;
  label: string;
  active?: boolean;
  className?: string;
}) {
  return (
    <button
      onClick={onClick}
      onPointerDown={onPointerDown}
      onPointerUp={onPointerUp}
      onPointerLeave={onPointerLeave}
      aria-pressed={active}
      className={`flex min-w-[4.5rem] flex-col items-center gap-1 rounded-lg px-3 py-1.5 text-[11px] font-medium transition-colors ${
        active ? "bg-[#e02d3c]/20 text-[#ff8a94]" : "text-[#e8e9ed] hover:bg-white/10"
      } ${className}`}
    >
      <span aria-hidden="true">{icon}</span>
      {label}
    </button>
  );
}

const ICON = "h-5 w-5";

function MicIcon() {
  return (
    <svg viewBox="0 0 24 24" fill="none" className={ICON} stroke="currentColor" strokeWidth="1.8">
      <rect x="9" y="3" width="6" height="11" rx="3" />
      <path d="M5 11a7 7 0 0 0 14 0M12 18v3" strokeLinecap="round" />
    </svg>
  );
}

function MicOffIcon() {
  return (
    <svg viewBox="0 0 24 24" fill="none" className={ICON} stroke="currentColor" strokeWidth="1.8">
      <path d="M9 9v2a3 3 0 0 0 4.6 2.5M15 11V6a3 3 0 0 0-5.9-.7" strokeLinecap="round" />
      <path d="M5 11a7 7 0 0 0 10.9 5.8M12 18v3M4 3l16 18" strokeLinecap="round" />
    </svg>
  );
}

function VideoIcon() {
  return (
    <svg viewBox="0 0 24 24" fill="none" className={ICON} stroke="currentColor" strokeWidth="1.8">
      <rect x="3" y="6" width="12" height="12" rx="2" />
      <path d="m15 11 6-3v8l-6-3z" strokeLinejoin="round" />
    </svg>
  );
}

function VideoOffIcon() {
  return (
    <svg viewBox="0 0 24 24" fill="none" className={ICON} stroke="currentColor" strokeWidth="1.8">
      <path d="M15 10.5V8a2 2 0 0 0-2-2H8M3 8v8a2 2 0 0 0 2 2h8" strokeLinecap="round" />
      <path d="m15 11 6-3v8M4 3l16 18" strokeLinecap="round" strokeLinejoin="round" />
    </svg>
  );
}

function ShareIcon() {
  return (
    <svg viewBox="0 0 24 24" fill="none" className={ICON} stroke="currentColor" strokeWidth="1.8">
      <rect x="3" y="4" width="18" height="13" rx="2" />
      <path d="M9 21h6M12 8v5M9.5 10.5 12 8l2.5 2.5" strokeLinecap="round" strokeLinejoin="round" />
    </svg>
  );
}

function SpeakerIcon() {
  return (
    <svg viewBox="0 0 24 24" fill="none" className={ICON} stroke="currentColor" strokeWidth="1.8">
      <path d="M4 9v6h3.5L12 19V5L7.5 9H4z" strokeLinejoin="round" />
      <path d="M16 9.5a3.5 3.5 0 0 1 0 5M18.5 7a7 7 0 0 1 0 10" strokeLinecap="round" />
    </svg>
  );
}

function SpeakerOffIcon() {
  return (
    <svg viewBox="0 0 24 24" fill="none" className={ICON} stroke="currentColor" strokeWidth="1.8">
      <path d="M4 9v6h3.5L12 19V5L7.5 9H4z" strokeLinejoin="round" />
      <path d="m16 10 5 5m0-5-5 5" strokeLinecap="round" />
    </svg>
  );
}

function PaperIcon() {
  return (
    <svg viewBox="0 0 24 24" fill="none" className={ICON} stroke="currentColor" strokeWidth="1.8">
      <path d="M6 3h9l4 4v14H6z" strokeLinejoin="round" />
      <path d="M14 3v5h5" strokeLinejoin="round" />
      <path d="M9 12h6M9 15.5h4" strokeLinecap="round" />
    </svg>
  );
}

function BoardIcon() {
  return (
    <svg viewBox="0 0 24 24" fill="none" className={ICON} stroke="currentColor" strokeWidth="1.8">
      <rect x="3" y="4" width="18" height="12" rx="2" />
      <path d="M12 16v5M8 20h8M7 11l3-3 2.5 2.5L16 7" strokeLinecap="round" strokeLinejoin="round" />
    </svg>
  );
}

function TranscriptIcon() {
  return (
    <svg viewBox="0 0 24 24" fill="none" className={ICON} stroke="currentColor" strokeWidth="1.8">
      <path d="M4 5h16v11H8l-4 4V5z" strokeLinejoin="round" />
      <path d="M8 9h8M8 12.5h5" strokeLinecap="round" />
    </svg>
  );
}
