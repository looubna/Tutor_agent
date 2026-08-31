"use client";

/**
 * A spoken lesson: the browser's half.
 *
 * One websocket to the agent, carrying the microphone up as raw PCM and the
 * tutor's voice back down. Everything else the lesson does — turning a page,
 * writing on the paper, putting material up — arrives on the same socket as
 * small JSON frames, so the call screen stays in step without polling.
 *
 * The two sample rates are the Live API's, not ours, and they differ: 16kHz in,
 * 24kHz out. That is why there are two AudioContexts. One context resampling
 * for both directions sounds subtly wrong in a way that is very hard to trace
 * back from "the tutor sounds like a chipmunk".
 */

const INPUT_RATE = 16_000;
const OUTPUT_RATE = 24_000;

export type LiveEvent =
  | { type: "ready"; model: string; voice: string; language: string;
      paper_available: boolean; showing_page: string | null; notes: string[] }
  | { type: "transcript"; role: "STUDENT" | "TUTOR"; text: string; final?: boolean }
  | { type: "interrupted" }
  | { type: "turn_complete" }
  | { type: "tool"; name: string }
  | { type: "paper"; showing_page: string | null; marks: number;
      showing_material: unknown; board: string[];
      /**
       * The lines she has just written, in order. Sent so the browser can
       * trace them out rather than reloading the page with them already on it.
       */
      written?: { text: string; on: string }[] }
  | { type: "board"; lines: string[] }
  /**
   * The first sound the tutor has actually made. Until this arrives nothing
   * has been heard, whatever the socket says about itself — which is the
   * difference between a working call and a connected one.
   */
  | { type: "audio_started" }
  | { type: "closed"; detail: string }
  | { type: "error"; detail: string; fallback?: "text" };

/**
 * The tutor's voice. Kept out of `LiveEvent` because it is not an event the
 * call screen ever sees — it goes straight to the speaker, thousands of times
 * an hour, and nothing above this file should have to ignore it.
 */
type AudioFrame = { type: "audio"; data: string };

export type LiveSession = {
  /** Say something without speaking it. */
  say(text: string): void;
  /**
   * Mute the microphone without leaving the call — the mute button on any
   * video call. The socket stays open, the tutor keeps talking, and it simply
   * stops hearing the room.
   */
  setMuted(muted: boolean): void;
  /**
   * Send the tutor's voice somewhere other than the speaker.
   *
   * The avatar is the reason this exists. She has to lip-sync to the voice, so
   * she needs the audio itself rather than a transcript of it — and the words
   * must not also come out of the speaker, or the tutor talks over herself.
   *
   * The sink is handed the frame exactly as it arrived, base64 PCM at 24kHz,
   * because that is already the format the avatar wants. Decoding it here to
   * re-encode it there would be work done twice on the audio thread.
   *
   * `null` puts the voice back on the speaker.
   */
  setVoiceSink(sink: ((pcm24kBase64: string) => void) | null): void;
  /**
   * How loud the tutor is, right now, from 0 to 1.
   *
   * Reported off the audio on its way to the speaker rather than measured
   * again from it, because the samples are already decoded here and nobody
   * else should have to do that work twice. It exists so a tutor who is only
   * a photograph can still visibly be the one talking.
   */
  setVoiceLevel(watcher: ((level: number) => void) | null): void;
  /** End the lesson's audio. Safe to call twice. */
  stop(): void;
};

/**
 * How loud a frame of the tutor's voice is, 0 to 1.
 *
 * Root mean square over every eighth sample: speech is smooth enough at this
 * timescale that reading all of them buys nothing, and this runs on the same
 * thread as the lesson. The scaling is empirical — a speaking voice sits well
 * below full scale, so raw RMS barely moves anything it drives.
 */
function loudness(bytes: Uint8Array): number {
  const samples = new Int16Array(bytes.buffer, bytes.byteOffset,
                                 Math.floor(bytes.byteLength / 2));
  if (!samples.length) return 0;
  let sum = 0;
  let counted = 0;
  for (let i = 0; i < samples.length; i += 8) {
    const value = samples[i] / 32768;
    sum += value * value;
    counted++;
  }
  return Math.min(1, Math.sqrt(sum / counted) * 4);
}

export const canDoLiveAudio = () =>
  typeof window !== "undefined" &&
  "AudioWorkletNode" in window &&
  Boolean(navigator.mediaDevices?.getUserMedia);

/**
 * Open the microphone and start talking to the tutor.
 *
 * Resolves once the socket is open and the agent has said it is ready; rejects
 * if the microphone is refused or the agent turns the ticket down. Everything
 * after that arrives through `onEvent`.
 */
export async function startLiveLesson(
  bookingId: string,
  onEvent: (event: LiveEvent) => void,
): Promise<LiveSession> {
  const permission = await fetch(`/api/lesson/${bookingId}/live-ticket`, { method: "POST" });
  const grant = await permission.json();
  if (!permission.ok) throw new Error(grant?.error ?? "Could not start the spoken lesson.");

  // The microphone first: if it is refused, nothing else is worth setting up,
  // and asking before opening a socket keeps the failure legible.
  const microphone = await navigator.mediaDevices.getUserMedia({
    audio: {
      channelCount: 1,
      echoCancellation: true,
      noiseSuppression: true,
      autoGainControl: true,
    },
  });

  const listening = new AudioContext({ sampleRate: INPUT_RATE });
  const speaking = new AudioContext({ sampleRate: OUTPUT_RATE });
  await listening.audioWorklet.addModule("/audio/recorder.worklet.js");
  await speaking.audioWorklet.addModule("/audio/player.worklet.js");
  // A context created outside a user gesture starts suspended, and a suspended
  // context renders nothing at all — no capture, no playback, no error.
  await Promise.all([listening.resume(), speaking.resume()]);

  const socket = new WebSocket(grant.url);
  socket.binaryType = "arraybuffer";

  const player = new AudioWorkletNode(speaking, "lesson-player");
  player.connect(speaking.destination);

  const recorder = new AudioWorkletNode(listening, "lesson-recorder");
  listening.createMediaStreamSource(microphone).connect(recorder);

  // The recorder has to reach the destination or it never runs.
  //
  // Web Audio renders on demand, pulling from the destination backwards: a node
  // connected to nothing is not part of any path to an output, so its
  // `process()` is never called. The microphone was open, the socket was open,
  // and not one sample was ever captured — the tutor simply could not hear.
  //
  // The gain is zero because the one thing we must not do is play the
  // microphone back at the student.
  const silence = listening.createGain();
  silence.gain.value = 0;
  recorder.connect(silence).connect(listening.destination);

  recorder.port.onmessage = (event: MessageEvent<ArrayBuffer>) => {
    if (socket.readyState === WebSocket.OPEN) socket.send(event.data);
  };

  let closed = false;
  let spoken = false;
  let voiceSink: ((pcm24kBase64: string) => void) | null = null;
  let voiceLevel: ((level: number) => void) | null = null;
  const stop = () => {
    if (closed) return;
    closed = true;
    if (socket.readyState === WebSocket.OPEN) {
      socket.send(JSON.stringify({ type: "bye" }));
      socket.close();
    }
    microphone.getTracks().forEach((track) => track.stop());
    recorder.port.onmessage = null;
    recorder.disconnect();
    silence.disconnect();
    void listening.close();
    void speaking.close();
  };

  return new Promise<LiveSession>((resolve, reject) => {
    socket.onopen = () => socket.send(JSON.stringify({ ticket: grant.ticket, ...grant.hello }));

    socket.onmessage = (message) => {
      const frame = JSON.parse(message.data as string) as LiveEvent | AudioFrame;

      if (frame.type === "audio") {
        if (!spoken) {
          spoken = true;
          onEvent({ type: "audio_started" });
        }
        // Handed on rather than decoded: something else is the mouth right now,
        // and it wants the audio in exactly the shape it arrived in.
        if (voiceSink) {
          voiceSink(frame.data);
          return;
        }
        // Base64 rather than a binary frame, because it shares the socket with
        // the JSON events and one framing is simpler than two.
        const binary = atob(frame.data);
        const bytes = new Uint8Array(binary.length);
        for (let i = 0; i < binary.length; i++) bytes[i] = binary.charCodeAt(i);
        // Before the buffer is posted, because posting transfers it and a
        // transferred buffer is empty on this side.
        if (voiceLevel) voiceLevel(loudness(bytes));
        player.port.postMessage(bytes.buffer, [bytes.buffer]);
        return;
      }

      // The student has talked over the tutor. Everything queued for the
      // speaker is an answer to the previous question, so it goes.
      if (frame.type === "interrupted") player.port.postMessage("flush");

      if (frame.type === "ready") {
        resolve({ say, setMuted, setVoiceSink, setVoiceLevel, stop });
      }
      // An error after the session is up is not a rejection — the promise has
      // already resolved — so it also has to end the session, or the page keeps
      // a microphone open for a tutor that is not listening.
      if (frame.type === "error") {
        reject(new Error(frame.detail));
        stop();
      }
      if (frame.type === "closed") stop();
      onEvent(frame);
    };

    socket.onerror = () => reject(new Error("The tutor's audio could not be reached."));
    socket.onclose = () => {
      if (!closed) stop();
    };

    function setMuted(muted: boolean) {
      // The track, not the socket: stopping the stream would end the call, and
      // muting is not leaving.
      microphone.getAudioTracks().forEach((track) => { track.enabled = !muted; });
      if (muted) player.port.postMessage("flush");
    }

    function setVoiceLevel(watcher: ((level: number) => void) | null) {
      voiceLevel = watcher;
    }

    function setVoiceSink(sink: ((pcm24kBase64: string) => void) | null) {
      voiceSink = sink;
      // Whatever is already queued for the speaker was said before the avatar
      // took over, and would play out over the top of her.
      if (sink) player.port.postMessage("flush");
    }

    function say(text: string) {
      if (socket.readyState !== WebSocket.OPEN) return;
      // Whatever the tutor was mid-sentence about is no longer the answer to
      // what was just asked.
      player.port.postMessage("flush");
      socket.send(JSON.stringify({ type: "text", text }));
    }
  });
}
