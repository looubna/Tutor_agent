"use client";

/**
 * The tutor's face.
 *
 * A rendered person who lip-syncs, in real time, to the audio the lesson is
 * already producing. She does not have a voice of her own and is not asked to
 * think: Gemini teaches and speaks, natively, in the language of the class,
 * and every sample of that is streamed straight into her.
 *
 * Sending a transcript instead and letting the service speak it — which is what
 * this did before — was wrong three ways at once. The turn had to finish before
 * there was a final transcript, so she answered seconds late; the voice was a
 * different one from the lesson's; and a face driven by flat synthesis has
 * nothing to act with. Feeding her the real voice fixes all three, because all
 * three were the same mistake.
 */

/** The session, as the call screen needs it. */
export type TutorFace = {
  /**
   * Put her on a pair of elements. Both are needed: the video carries her
   * picture and the audio her voice, and the SDK insists on its own audio
   * element rather than muxing into one. Safe to call again — the call screen
   * moves the tutor between a large tile and a small one, which remounts them.
   */
  attach(video: HTMLVideoElement, audio: HTMLAudioElement): void;
  /**
   * A piece of the tutor's voice, base64 PCM at 24kHz — the frame exactly as
   * the lesson's socket delivered it. Resampled on the way in; see `toSimliRate`.
   */
  speakAudio(pcm24kBase64: string): void;
  /** The turn is over. Nothing is held back, so this only tidies the resampler. */
  endTurn(): void;
  /** Stop mid-sentence. The student has interrupted. */
  hush(): void;
  /** End the session. Safe to call twice. */
  stop(): void;
};

/** How long to wait for the first frame before giving up on the face. */
const STREAM_TIMEOUT_MS = 20_000;
/**
 * How long after being given audio she has to start moving her mouth.
 *
 * A session can connect, show a perfectly good picture of somebody and never
 * speak. There is no error and no failed promise; the avatar simply smiles at
 * the student for the rest of the hour. So the first audio she is given is also
 * a test, and failing it puts the voice back on the speaker.
 */
const FIRST_WORD_MS = 6_000;

/**
 * The two rates, which are not the same and are not ours to choose.
 *
 * Gemini's Live API speaks at 24kHz. Simli listens at 16kHz. Handing it 24kHz
 * and calling it 16kHz does not fail — it plays a third faster and a fifth
 * higher, so the tutor sounds like a chipmunk in a hurry and her mouth agrees
 * with it perfectly. The conversion is three input samples for every two out.
 */
const LESSON_RATE = 24_000;
const SIMLI_RATE = 16_000;

/**
 * Resample a chunk, keeping its place between calls.
 *
 * `phase` carries the fractional read position across packet boundaries. Resetting
 * it per packet would round the same tiny error a hundred times a minute, which
 * is audible as a faint tick on every chunk.
 */
function resampler() {
  const step = LESSON_RATE / SIMLI_RATE;
  let phase = 0;
  return {
    reset() { phase = 0; },
    take(input: Int16Array): Uint8Array {
      const out: number[] = [];
      let pos = phase;
      while (pos < input.length) {
        const index = Math.floor(pos);
        const between = pos - index;
        const here = input[index];
        const next = index + 1 < input.length ? input[index + 1] : here;
        out.push(Math.round(here + (next - here) * between));
        pos += step;
      }
      phase = pos - input.length;
      const bytes = new Uint8Array(out.length * 2);
      const view = new DataView(bytes.buffer);
      out.forEach((sample, i) => view.setInt16(i * 2, sample, true));
      return bytes;
    },
  };
}

const trace = (...what: unknown[]) => console.info("[tutor-face]", ...what);

/**
 * Open a session and wait until there is actually a picture.
 *
 * Resolving on "connected" is not enough: the room joins in under a second and
 * her first frame arrives several seconds later, so the tile would switch from
 * the portrait to a black rectangle and stay there.
 *
 * `onLost` is called if the session ends on its own. `onMute` is called if she
 * is there but never moves; see `FIRST_WORD_MS`.
 */
export async function startTutorFace(
  { onLost, onMute }: { onLost: () => void; onMute: () => void },
): Promise<TutorFace> {
  const minted = await fetch("/api/simli/token", { method: "POST" });
  const grant = await minted.json();
  if (!minted.ok) throw new Error(grant?.error ?? "The tutor's face could not be reached.");

  // Loaded here rather than imported at the top: the SDK brings LiveKit with
  // it, and a student who never joins the audio never pays for either.
  //
  // Reached past its own entry point on purpose. `simli-client@3.0.2` ships a
  // `dist/index.js` that requires `./Client` while the file on disk is
  // `client.js`, so the package resolves only on a case-insensitive filesystem:
  // fine on this Mac, a build failure under Turbopack and on any Linux box,
  // which includes the container this deploys in. Importing the module the
  // entry point was pointing at sidesteps it and keeps the types.
  const { SimliClient, LogLevel } = await import("simli-client/dist/client");

  let stopped = false;
  let spoken = false;
  let gaveUp = false;
  let started = false;
  const rate = resampler();

  // The elements the SDK renders into. They belong to this module rather than
  // to the call screen because the SDK takes them in its constructor, before
  // the tile they will live in has necessarily been mounted; `attach` moves
  // what it produces onto whichever elements are on screen now.
  const video = document.createElement("video");
  video.autoplay = true;
  video.playsInline = true;
  const audio = document.createElement("audio");
  audio.autoplay = true;

  // LiveKit rather than the default peer-to-peer transport: p2p refuses to
  // start without ICE servers, and the only way to get those is an endpoint
  // that wants the API key in the browser. This one needs neither.
  const client = new SimliClient(
    grant.token, video, audio, null, LogLevel.ERROR, "livekit", "websockets",
  );

  client.on("speaking", () => {
    if (!spoken) trace("she has started speaking");
    spoken = true;
  });
  client.on("error", (detail: string) => {
    if (stopped) return;
    stopped = true;
    trace("session error:", detail);
    onLost();
  });
  client.on("stop", () => {
    if (stopped) return;
    stopped = true;
    onLost();
  });

  await Promise.race([
    client.start(),
    new Promise((_, reject) =>
      window.setTimeout(
        () => reject(new Error("The tutor's face did not arrive in time.")),
        STREAM_TIMEOUT_MS,
      )),
  ]);
  trace("stream ready — she is on screen");

  return {
    // The SDK's own elements are the source; the tile's are where they are
    // shown. Copying the stream across is what survives the tutor being moved
    // between the large tile and the small one.
    attach: (tileVideo, tileAudio) => {
      tileVideo.srcObject = video.srcObject;
      tileAudio.srcObject = audio.srcObject;
      void tileVideo.play().catch(() => {});
      void tileAudio.play().catch(() => {});
    },

    speakAudio: (pcm24kBase64) => {
      if (stopped || !pcm24kBase64) return;
      const binary = atob(pcm24kBase64);
      const bytes = new Uint8Array(binary.length);
      for (let i = 0; i < binary.length; i++) bytes[i] = binary.charCodeAt(i);
      const samples = new Int16Array(bytes.buffer, 0, Math.floor(bytes.length / 2));
      if (!samples.length) return;

      client.sendAudioData(rate.take(samples));

      if (started) return;
      started = true;
      trace("first audio sent to her");
      window.setTimeout(() => {
        if (spoken || gaveUp || stopped) return;
        gaveUp = true;
        trace("audio was sent but she never moved — giving the voice back");
        onMute();
      }, FIRST_WORD_MS);
    },

    endTurn: () => rate.reset(),

    hush: () => {
      if (stopped) return;
      rate.reset();
      try {
        client.ClearBuffer();
      } catch {
        // Nothing buffered to drop.
      }
    },

    stop: () => {
      if (stopped) return;
      stopped = true;
      void client.stop();
    },
  };
}
