import type { CallSession } from "../../data/call";

interface LiveCallbacks {
  onReady: () => void;
  onTranscript: (text: string) => void;
  onSnapshot: (snapshot: CallSession) => void;
  onInterrupted: () => void;
  onTurnComplete: () => void;
  onError: (message: string) => void;
}

function pcm16(samples: Float32Array, inputRate: number): ArrayBuffer {
  const count = Math.floor(samples.length * 16000 / inputRate);
  const bytes = new ArrayBuffer(count * 2);
  const output = new DataView(bytes);
  for (let index = 0; index < count; index++) {
    const position = index * inputRate / 16000;
    const left = Math.floor(position);
    const fraction = position - left;
    const sample = samples[left] * (1 - fraction) + samples[Math.min(left + 1, samples.length - 1)] * fraction;
    output.setInt16(index * 2, Math.max(-1, Math.min(1, sample)) * 32767, true);
  }
  return bytes;
}

export class GeminiLiveVoice {
  private socket: WebSocket | null = null;
  private context: AudioContext | null = null;
  private stream: MediaStream | null = null;
  private microphone: MediaStreamAudioSourceNode | null = null;
  private processor: ScriptProcessorNode | null = null;
  private silentOutput: GainNode | null = null;
  private playback = new Set<AudioBufferSourceNode>();
  private nextPlaybackTime = 0;
  private stopped = false;

  constructor(private sessionId: string, private callbacks: LiveCallbacks, private apiBase = "/api/callers") {}

  async start(): Promise<void> {
    this.context = new AudioContext();
    await this.context.resume();
    try {
      this.stream = await navigator.mediaDevices.getUserMedia({
        audio: { echoCancellation: true, noiseSuppression: true, autoGainControl: true },
      });
      const base = new URL((import.meta.env.VITE_API_URL as string | undefined) || window.location.origin, window.location.origin);
      base.protocol = base.protocol === "https:" ? "wss:" : "ws:";
      const socket = new WebSocket(new URL(`${this.apiBase}/sessions/${this.sessionId}/live`, base));
      this.socket = socket;
      socket.binaryType = "arraybuffer";
      await new Promise<void>((resolve, reject) => {
        const timeout = window.setTimeout(() => reject(new Error("Gemini Live did not connect.")), 15000);
        socket.onmessage = (event) => {
          if (event.data instanceof ArrayBuffer) {
            this.play(event.data);
            return;
          }
          const message = JSON.parse(event.data as string);
          if (message.type === "ready") {
            window.clearTimeout(timeout);
            resolve();
            this.callbacks.onReady();
          } else if (message.type === "error") {
            window.clearTimeout(timeout);
            reject(new Error(message.message));
          } else if (message.type === "transcript") {
            this.callbacks.onTranscript(message.text);
          } else if (message.type === "snapshot") {
            this.callbacks.onSnapshot(message.value);
          } else if (message.type === "interrupted") {
            this.clearPlayback();
            this.callbacks.onInterrupted();
          } else if (message.type === "turn_complete") {
            this.callbacks.onTurnComplete();
          }
        };
        socket.onerror = () => {
          window.clearTimeout(timeout);
          reject(new Error("Gemini Live connection failed."));
        };
        socket.onclose = () => {
          window.clearTimeout(timeout);
          if (!this.stopped) this.callbacks.onError("การเชื่อมต่อ Gemini Live สิ้นสุด กรุณาเริ่มสนทนาใหม่");
          reject(new Error("Gemini Live connection closed."));
        };
      });
      if (this.stopped) return;
      this.microphone = this.context.createMediaStreamSource(this.stream);
      this.processor = this.context.createScriptProcessor(2048, 1, 1);
      this.silentOutput = this.context.createGain();
      this.silentOutput.gain.value = 0;
      this.processor.onaudioprocess = (event) => {
        const current = this.socket;
        if (current?.readyState !== WebSocket.OPEN || current.bufferedAmount > 256_000) return;
        current.send(pcm16(event.inputBuffer.getChannelData(0), event.inputBuffer.sampleRate));
      };
      this.microphone.connect(this.processor);
      this.processor.connect(this.silentOutput);
      this.silentOutput.connect(this.context.destination);
    } catch (error) {
      this.stop();
      throw error;
    }
  }

  clearPlayback(): void {
    for (const source of this.playback) {
      try { source.stop(); } catch { /* Already ended. */ }
    }
    this.playback.clear();
    this.nextPlaybackTime = this.context?.currentTime ?? 0;
  }

  private play(bytes: ArrayBuffer): void {
    const context = this.context;
    if (!context || this.stopped) return;
    const pcm = new DataView(bytes);
    const buffer = context.createBuffer(1, Math.floor(bytes.byteLength / 2), 24000);
    const samples = buffer.getChannelData(0);
    for (let index = 0; index < samples.length; index++) {
      samples[index] = pcm.getInt16(index * 2, true) / 32768;
    }
    const source = context.createBufferSource();
    source.buffer = buffer;
    source.connect(context.destination);
    source.onended = () => this.playback.delete(source);
    this.playback.add(source);
    const start = Math.max(context.currentTime + 0.02, this.nextPlaybackTime);
    source.start(start);
    this.nextPlaybackTime = start + buffer.duration;
  }

  stop(): void {
    if (this.stopped) return;
    this.stopped = true;
    this.clearPlayback();
    this.processor?.disconnect();
    this.microphone?.disconnect();
    this.silentOutput?.disconnect();
    this.stream?.getTracks().forEach((track) => track.stop());
    this.socket?.close();
    void this.context?.close();
  }
}
