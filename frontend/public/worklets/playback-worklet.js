// Queued PCM playback. The main thread pushes Float32 chunks derived from
// Gemini's 24 kHz Int16 stream. The worklet drains the queue into the output
// buffer, zero-filling on underrun. A "flush" message empties the queue for
// barge-in.
class PlaybackProcessor extends AudioWorkletProcessor {
  constructor() {
    super();
    this.queue = [];
    this.currentChunk = null;
    this.currentPos = 0;
    this.port.onmessage = (event) => {
      const msg = event.data;
      if (!msg) return;
      if (msg.type === "flush") {
        this.queue = [];
        this.currentChunk = null;
        this.currentPos = 0;
        return;
      }
      if (msg.type === "push" && msg.samples instanceof Float32Array) {
        this.queue.push(msg.samples);
      }
    };
  }

  process(_inputs, outputs) {
    const out = outputs[0]?.[0];
    if (!out) return true;
    for (let i = 0; i < out.length; i += 1) {
      if (!this.currentChunk || this.currentPos >= this.currentChunk.length) {
        this.currentChunk = this.queue.shift() || null;
        this.currentPos = 0;
      }
      if (this.currentChunk) {
        out[i] = this.currentChunk[this.currentPos];
        this.currentPos += 1;
      } else {
        out[i] = 0;
      }
    }
    return true;
  }
}

registerProcessor("playback", PlaybackProcessor);
