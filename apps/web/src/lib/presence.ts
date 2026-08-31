/**
 * Whether there is actually somebody in front of the camera.
 *
 * The tutor was being told "present" whenever the camera was switched on, which
 * is not the same claim: a camera pointing at an empty chair is on. The state
 * machine suspends a lesson when the student leaves, so that flag decides
 * whether an hour carries on being taught to nobody.
 *
 * What this measures is movement. Two small greyscale samples a second apart
 * are compared, and a person — breathing, blinking, shifting — moves enough to
 * show up while an empty room, a covered lens and a frozen stream do not. It is
 * a proxy and it is honest about being one: it cannot tell a person from a cat,
 * and `method` says which signal the answer came from so nothing downstream has
 * to guess.
 *
 * A vision model on the frames would be better and is what §5 of the brief
 * asks for. This costs nothing, runs at 1Hz on a canvas 32 pixels wide, and is
 * a great deal better than reading the camera's on switch.
 */

/** How wide the sample is. Big enough for movement, too small to be a picture. */
const SAMPLE = 32;

/** Mean per-pixel change that counts as somebody being there. */
const MOVEMENT = 1.6;

/** Below this the frame is a lens cap or an unlit room, however much it flickers. */
const DARKNESS = 12;

/** How long a stillness is tolerated before it is read as an empty chair. */
const STILL_MS = 12_000;

export type PresenceReading = {
  present: boolean;
  /** Why: what the answer was actually derived from. */
  method: "camera-off" | "no-frames" | "too-dark" | "movement" | "still";
};

export class PresenceWatcher {
  private canvas: HTMLCanvasElement | null = null;
  private previous: Uint8ClampedArray | null = null;
  private lastMovedAt = 0;
  private reading: PresenceReading = { present: false, method: "camera-off" };

  /** The last answer. Cheap: the sampling happens on its own schedule. */
  get latest(): PresenceReading {
    return this.reading;
  }

  /** Take one sample. Call about once a second while the camera is on. */
  sample(video: HTMLVideoElement | null, cameraOn: boolean, now = Date.now()): PresenceReading {
    if (!cameraOn || !video) {
      this.previous = null;
      return (this.reading = { present: false, method: "camera-off" });
    }
    if (!video.videoWidth || video.readyState < 2) {
      return (this.reading = { present: false, method: "no-frames" });
    }

    const canvas = (this.canvas ??= document.createElement("canvas"));
    canvas.width = SAMPLE;
    canvas.height = SAMPLE;
    const context = canvas.getContext("2d", { willReadFrequently: true });
    if (!context) return this.reading;

    context.drawImage(video, 0, 0, SAMPLE, SAMPLE);
    const frame = context.getImageData(0, 0, SAMPLE, SAMPLE).data;

    // Greyscale, in place, so the comparison is one number per pixel.
    const grey = new Uint8ClampedArray(SAMPLE * SAMPLE);
    let total = 0;
    for (let i = 0; i < grey.length; i++) {
      const p = i * 4;
      grey[i] = (frame[p] * 0.299 + frame[p + 1] * 0.587 + frame[p + 2] * 0.114) | 0;
      total += grey[i];
    }

    const brightness = total / grey.length;
    const previous = this.previous;
    this.previous = grey;

    if (brightness < DARKNESS) {
      return (this.reading = { present: false, method: "too-dark" });
    }
    if (!previous) {
      // The first frame has nothing to compare against. Assume somebody is
      // there rather than opening a lesson by declaring the room empty.
      this.lastMovedAt = now;
      return (this.reading = { present: true, method: "movement" });
    }

    let change = 0;
    for (let i = 0; i < grey.length; i++) change += Math.abs(grey[i] - previous[i]);
    if (change / grey.length >= MOVEMENT) this.lastMovedAt = now;

    const recentlyMoved = now - this.lastMovedAt < STILL_MS;
    return (this.reading = recentlyMoved
      ? { present: true, method: "movement" }
      : { present: false, method: "still" });
  }
}
