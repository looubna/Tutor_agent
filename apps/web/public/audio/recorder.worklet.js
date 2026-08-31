/**
 * Microphone capture for a spoken lesson.
 *
 * The Live API takes raw 16-bit little-endian PCM at 16kHz, mono, and nothing
 * else — so the AudioContext is created at that rate and the only work here is
 * turning Web Audio's float samples into the integers the API expects.
 *
 * A worklet rather than a ScriptProcessor because this runs on the audio
 * thread: a class where the tutor's voice stutters whenever React re-renders
 * is not a class anybody stays in.
 */
class RecorderProcessor extends AudioWorkletProcessor {
  process(inputs, outputs) {
    const channel = inputs[0]?.[0];

    // Write silence out. This node sits on a path to the destination — it has
    // to, or the graph never pulls it and nothing is ever captured — so it is
    // producing sound whether we like it or not. Zeroing it here as well as at
    // the gain node means a bug in the graph cannot become a howl in the
    // student's headphones.
    const out = outputs[0]?.[0];
    if (out) out.fill(0);

    if (!channel) return true;

    // Float [-1, 1] to signed 16-bit. Clamped first: a sample slightly over 1
    // wraps to a large negative number, which is heard as a click.
    const pcm = new Int16Array(channel.length);
    for (let i = 0; i < channel.length; i++) {
      const sample = Math.max(-1, Math.min(1, channel[i]));
      pcm[i] = sample * 0x7fff;
    }
    this.port.postMessage(pcm.buffer, [pcm.buffer]);
    return true;
  }
}

registerProcessor("lesson-recorder", RecorderProcessor);
