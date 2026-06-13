// Downsample the native capture rate (usually 48 kHz) mono Float32 → 16 kHz
// Int16 PCM and post chunks to the main thread. Each chunk is ~100 ms
// (1600 samples at 16 kHz).
class MicCaptureProcessor extends AudioWorkletProcessor {
  constructor() {
    super();
    this.ratio = Math.max(1, Math.round(sampleRate / 16000));
    this.chunkSize = 1600;
    this.accum = [];
    this.sumBuf = 0;
    this.count = 0;
  }

  process(inputs) {
    const input = inputs[0];
    if (!input || input.length === 0) return true;
    const samples = input[0];
    if (!samples) return true;
    for (let i = 0; i < samples.length; i += 1) {
      this.sumBuf += samples[i];
      this.count += 1;
      if (this.count >= this.ratio) {
        const avg = this.sumBuf / this.count;
        const clamped = Math.max(-1, Math.min(1, avg));
        const int16 = clamped < 0 ? clamped * 0x8000 : clamped * 0x7fff;
        this.accum.push(int16 | 0);
        this.sumBuf = 0;
        this.count = 0;
      }
    }
    while (this.accum.length >= this.chunkSize) {
      const slice = this.accum.splice(0, this.chunkSize);
      const out = new Int16Array(slice);
      this.port.postMessage(out.buffer, [out.buffer]);
    }
    return true;
  }
}

registerProcessor("mic-capture", MicCaptureProcessor);
