/**
 * The tutor's voice, played as it arrives.
 *
 * Output is 16-bit PCM at 24kHz, in chunks that do not line up with the
 * browser's 128-sample render quantum — so this holds a queue of chunks and
 * pours them into each render block, rather than scheduling one buffer per
 * message. Scheduling per message leaves a seam at every boundary, and a voice
 * with a click every 200ms sounds broken even when every sample is correct.
 *
 * Running dry is silence, not a stall: the tutor pauses between sentences and
 * that has to sound like a pause.
 */
class PlayerProcessor extends AudioWorkletProcessor {
  constructor() {
    super();
    this.queue = [];
    this.offset = 0;
    this.port.onmessage = (event) => {
      if (event.data === "flush") {
        // The student interrupted. Drop what the tutor was going to say rather
        // than talking over them for another two seconds.
        this.queue = [];
        this.offset = 0;
        return;
      }
      this.queue.push(new Int16Array(event.data));
    };
  }

  process(_inputs, outputs) {
    const channel = outputs[0]?.[0];
    if (!channel) return true;

    for (let i = 0; i < channel.length; i++) {
      const chunk = this.queue[0];
      if (!chunk) {
        channel[i] = 0;
        continue;
      }
      channel[i] = chunk[this.offset++] / 0x8000;
      if (this.offset >= chunk.length) {
        this.queue.shift();
        this.offset = 0;
      }
    }
    return true;
  }
}

registerProcessor("lesson-player", PlayerProcessor);
