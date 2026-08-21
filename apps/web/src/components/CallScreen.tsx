"use client";

import { useCallback, useEffect, useRef, useState } from "react";
import { useRouter } from "next/navigation";
import {
  LiveAvatarSession,
  SessionEvent,
  SessionState,
  AgentEventsEnum,
} from "@heygen/liveavatar-web-sdk";
import { completeBooking } from "@/app/actions/booking";
import { PlottedCurve } from "@/components/PlottedCurve";

type Message = { role: "STUDENT" | "TUTOR"; content: string };
type AvatarMode = "checking" | "heygen" | "voice-only";

type SpeechRecognitionLike = {
  continuous: boolean;
  interimResults: boolean;
  lang: string;
  start: () => void;
  stop: () => void;
  onresult: ((event: SpeechRecognitionEventLike) => void) | null;
  onerror: ((event: { error: string }) => void) | null;
  onend: (() => void) | null;
};
type SpeechRecognitionEventLike = {
  resultIndex: number;
  results: { [i: number]: { 0: { transcript: string }; isFinal: boolean }; length: number };
};

export function CallScreen({
  bookingId,
  initialMessages,
}: {
  bookingId: string;
  initialMessages: Message[];
}) {
  const router = useRouter();

  const localVideoRef = useRef<HTMLVideoElement>(null);
  const tutorVideoRef = useRef<HTMLVideoElement>(null);
  const sessionRef = useRef<LiveAvatarSession | null>(null);
  const streamRef = useRef<MediaStream | null>(null);
  const recognitionRef = useRef<SpeechRecognitionLike | null>(null);
  const shouldListenRef = useRef(true);
  const busyRef = useRef(false);

  const [messages, setMessages] = useState<Message[]>(initialMessages);
  const [connectionState, setConnectionState] = useState<SessionState>(SessionState.INACTIVE);
  const [avatarMode, setAvatarMode] = useState<AvatarMode>("checking");
  const [error, setError] = useState<string | null>(null);
  const [speechSupported] = useState(
    () =>
      typeof window !== "undefined" &&
      !!((window as unknown as { SpeechRecognition?: unknown; webkitSpeechRecognition?: unknown })
        .SpeechRecognition ??
        (window as unknown as { webkitSpeechRecognition?: unknown }).webkitSpeechRecognition)
  );
  const [micMuted, setMicMuted] = useState(false);
  const [cameraOff, setCameraOff] = useState(false);
  const [tutorSpeaking, setTutorSpeaking] = useState(false);
  const [leaving, setLeaving] = useState(false);

  const appendMessage = useCallback((msg: Message) => {
    setMessages((prev) => [...prev, msg]);
  }, []);

  const speak = useCallback(
    (text: string) => {
      if (avatarMode === "heygen") {
        sessionRef.current?.repeat(text);
        return;
      }
      if (typeof window === "undefined" || !("speechSynthesis" in window)) return;
      const utterance = new SpeechSynthesisUtterance(text);
      utterance.onstart = () => {
        shouldListenRef.current = false;
        setTutorSpeaking(true);
      };
      utterance.onend = () => {
        shouldListenRef.current = true;
        setTutorSpeaking(false);
      };
      window.speechSynthesis.speak(utterance);
    },
    [avatarMode]
  );

  const handleUserUtterance = useCallback(
    async (text: string) => {
      if (!text.trim() || busyRef.current) return;
      busyRef.current = true;
      appendMessage({ role: "STUDENT", content: text });

      try {
        const res = await fetch(`/api/lesson/${bookingId}/turn`, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ text }),
        });
        const data = await res.json();
        if (!res.ok) throw new Error(data.error ?? "The tutor could not respond.");

        appendMessage({ role: "TUTOR", content: data.reply });
        speak(data.reply);
      } catch (err) {
        setError((err as Error).message);
      } finally {
        busyRef.current = false;
      }
    },
    [bookingId, appendMessage, speak]
  );

  // Local webcam
  useEffect(() => {
    let cancelled = false;
    navigator.mediaDevices
      .getUserMedia({ video: true, audio: false })
      .then((stream) => {
        if (cancelled) {
          stream.getTracks().forEach((t) => t.stop());
          return;
        }
        streamRef.current = stream;
        if (localVideoRef.current) localVideoRef.current.srcObject = stream;
      })
      .catch(() => setError("Camera access was denied. You can still continue the lesson without video."));

    return () => {
      cancelled = true;
      streamRef.current?.getTracks().forEach((t) => t.stop());
    };
  }, []);

  // Speech recognition
  useEffect(() => {
    if (!speechSupported) return;

    const Recognition =
      (window as unknown as { SpeechRecognition?: new () => SpeechRecognitionLike }).SpeechRecognition ??
      (window as unknown as { webkitSpeechRecognition?: new () => SpeechRecognitionLike })
        .webkitSpeechRecognition;
    if (!Recognition) return;

    const recognition = new Recognition();
    recognition.continuous = true;
    recognition.interimResults = false;
    recognition.lang = "en-US";

    recognition.onresult = (event) => {
      if (!shouldListenRef.current) return;
      const result = event.results[event.resultIndex];
      if (result?.isFinal) {
        handleUserUtterance(result[0].transcript);
      }
    };
    recognition.onerror = (event) => {
      if (event.error !== "no-speech" && event.error !== "aborted") {
        setError(`Speech recognition error: ${event.error}`);
      }
    };
    recognition.onend = () => {
      if (!leaving) recognition.start();
    };

    recognitionRef.current = recognition;
    recognition.start();

    return () => {
      recognition.onend = null;
      recognition.stop();
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  // HeyGen live avatar session — falls back to voice-only (browser speech
  // synthesis, no avatar video) if HeyGen isn't configured or fails to connect.
  useEffect(() => {
    let cancelled = false;

    async function connect() {
      try {
        const res = await fetch("/api/heygen/token", { method: "POST" });
        if (!res.ok) {
          if (!cancelled) setAvatarMode("voice-only");
          return;
        }
        const data = await res.json();
        if (cancelled) return;

        const session = new LiveAvatarSession(data.token, { voiceChat: false });
        sessionRef.current = session;

        session.on(SessionEvent.SESSION_STATE_CHANGED, (state) => setConnectionState(state));
        session.on(SessionEvent.SESSION_STREAM_READY, () => {
          if (tutorVideoRef.current) session.attach(tutorVideoRef.current);
        });
        session.on(SessionEvent.SESSION_DISCONNECTED, () => setConnectionState(SessionState.DISCONNECTED));
        session.on(AgentEventsEnum.AVATAR_SPEAK_STARTED, () => {
          shouldListenRef.current = false;
          setTutorSpeaking(true);
        });
        session.on(AgentEventsEnum.AVATAR_SPEAK_ENDED, () => {
          shouldListenRef.current = true;
          setTutorSpeaking(false);
        });

        await session.start();
        if (!cancelled) setAvatarMode("heygen");
      } catch {
        if (!cancelled) setAvatarMode("voice-only");
      }
    }

    connect();
    return () => {
      cancelled = true;
    };
  }, []);

  // Greet once the avatar mode (HeyGen vs. voice-only) has settled.
  useEffect(() => {
    if (avatarMode === "checking" || messages.length > 0) return;
    const greeting = "Hi! I'm your AI Math tutor. What would you like to work on today?";
    // eslint-disable-next-line react-hooks/set-state-in-effect -- one-time greeting once the async avatar connection settles, not a render-derivable value
    appendMessage({ role: "TUTOR", content: greeting });
    speak(greeting);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [avatarMode]);

  const toggleMic = () => {
    shouldListenRef.current = micMuted;
    setMicMuted((m) => !m);
  };

  const toggleCamera = () => {
    const track = streamRef.current?.getVideoTracks()[0];
    if (track) track.enabled = cameraOff;
    setCameraOff((c) => !c);
  };

  const leaveCall = async () => {
    setLeaving(true);
    shouldListenRef.current = false;
    recognitionRef.current?.stop();
    streamRef.current?.getTracks().forEach((t) => t.stop());
    if (typeof window !== "undefined" && "speechSynthesis" in window) window.speechSynthesis.cancel();
    await sessionRef.current?.stop().catch(() => {});
    await completeBooking(bookingId);
    router.push("/dashboard");
  };

  const connecting =
    avatarMode === "checking" || (avatarMode === "heygen" && connectionState !== SessionState.CONNECTED);

  return (
    <div className="flex h-screen w-full flex-col bg-board">
      <div className="relative flex flex-1 gap-4 overflow-hidden p-4">
        <div className="relative flex-1 overflow-hidden rounded-2xl bg-black">
          {avatarMode === "heygen" ? (
            <video ref={tutorVideoRef} autoPlay playsInline className="h-full w-full object-cover" />
          ) : (
            <div className="bg-grid-paper flex h-full w-full items-center justify-center bg-gradient-to-br from-accent/15 via-board to-black">
              <div
                className={`flex h-32 w-32 items-center justify-center rounded-full bg-primary shadow-lg transition-transform duration-300 ${
                  tutorSpeaking ? "scale-110" : "scale-100"
                }`}
              >
                <svg viewBox="0 0 48 48" className="h-16 w-16" fill="none" aria-hidden="true">
                  <path
                    d="M13 25 L20 32 L35 15"
                    stroke="var(--board-foreground)"
                    strokeWidth="3.5"
                    strokeLinecap="round"
                    strokeLinejoin="round"
                  />
                </svg>
              </div>
            </div>
          )}
          {connecting && (
            <div className="absolute inset-0 flex flex-col items-center justify-center gap-4 bg-board/85">
              <PlottedCurve animate className="h-16 w-44" />
              <span className="text-sm text-board-foreground">Connecting to your AI tutor…</span>
            </div>
          )}
          {tutorSpeaking && (
            <span className="absolute bottom-4 left-4 rounded-full bg-primary px-3 py-1 text-xs font-medium text-white">
              Speaking…
            </span>
          )}
          <span className="absolute left-4 top-4 rounded-md bg-black/50 px-2 py-1 text-xs font-medium text-board-foreground">
            AI Math Tutor
          </span>
          {avatarMode === "voice-only" && (
            <span className="absolute right-4 top-4 rounded-md bg-black/50 px-2 py-1 text-xs font-medium text-board-foreground/80">
              Voice-only mode — add a HeyGen key for live avatar video
            </span>
          )}
        </div>

        <div className="absolute bottom-8 right-8 h-40 w-56 overflow-hidden rounded-xl border-2 border-board-foreground/20 bg-black shadow-lg">
          <video ref={localVideoRef} autoPlay playsInline muted className="h-full w-full object-cover" />
          {cameraOff && (
            <div className="absolute inset-0 flex items-center justify-center bg-black text-xs text-board-foreground/70">
              Camera off
            </div>
          )}
        </div>

        <aside className="hidden w-80 shrink-0 flex-col rounded-2xl border border-board-foreground/10 bg-board-foreground/[0.06] p-4 md:flex">
          <h2 className="mb-3 text-sm font-semibold text-board-foreground font-display">Transcript</h2>
          <div className="flex flex-1 flex-col gap-3 overflow-y-auto pr-1">
            {messages.map((m, i) => (
              <div
                key={i}
                className={`rounded-lg px-3 py-2 text-sm ${
                  m.role === "TUTOR" ? "bg-primary-tint text-primary" : "ml-6 bg-board-foreground/10 text-board-foreground"
                }`}
              >
                {m.content}
              </div>
            ))}
          </div>
        </aside>
      </div>

      {!speechSupported && (
        <div className="mx-4 mb-2 rounded-lg bg-danger/10 px-4 py-2 text-sm text-danger">
          Speech recognition isn&apos;t supported in this browser. Try Chrome.
        </div>
      )}
      {error && (
        <div className="mx-4 mb-2 rounded-lg bg-danger/10 px-4 py-2 text-sm text-danger">{error}</div>
      )}

      <div className="flex items-center justify-center gap-4 pb-8">
        <button
          onClick={toggleMic}
          className={`rounded-full px-5 py-3 text-sm font-medium text-board-foreground ${
            micMuted ? "bg-accent" : "bg-board-foreground/10 hover:bg-board-foreground/20"
          }`}
        >
          {micMuted ? "Unmute" : "Mute"}
        </button>
        <button
          onClick={toggleCamera}
          className={`rounded-full px-5 py-3 text-sm font-medium text-board-foreground ${
            cameraOff ? "bg-accent" : "bg-board-foreground/10 hover:bg-board-foreground/20"
          }`}
        >
          {cameraOff ? "Start Camera" : "Stop Camera"}
        </button>
        <button
          onClick={leaveCall}
          disabled={leaving}
          className="rounded-full bg-danger px-6 py-3 text-sm font-semibold text-white hover:opacity-90 disabled:opacity-60"
        >
          {leaving ? "Leaving…" : "Leave lesson"}
        </button>
      </div>
    </div>
  );
}
