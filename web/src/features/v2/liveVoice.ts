import { wsOrigin } from "../../data/wsOrigin";
/**
 * A Gemini Live voice call with the intake agent (server: api/v2/live.py). Adapted from Earth's
 * microphone → 16 kHz PCM over a WebSocket; Gemini's 24 kHz voice back.
 */
import { demoRoom } from "../../data/room";
import type { TurnResult } from "./api";

export interface LiveEvents {
  onReady: () => void;
  onCaption?: (speaker: "heard" | "said", text: string) => void;
  onFallback?: (text: string) => void;
  onCaller: (text: string) => void;
  onTurn: (r: TurnResult) => void;
  onEnd: (message?: string) => void;
}

function pcm16(samples: Float32Array, inputRate: number): ArrayBuffer {
  const count = Math.floor((samples.length * 16000) / inputRate);
  const bytes = new ArrayBuffer(count * 2);
  const out = new DataView(bytes);
  for (let i = 0; i < count; i++) {
    const p = (i * inputRate) / 16000;
    const l = Math.floor(p);
    const f = p - l;
    const s = samples[l] * (1 - f) + samples[Math.min(l + 1, samples.length - 1)] * f;
    out.setInt16(i * 2, Math.max(-1, Math.min(1, s)) * 32767, true);
  }
  return bytes;
}

export class LiveCall {
  private ws: WebSocket | null = null;
  private ctx: AudioContext | null = null;
  private stream: MediaStream | null = null;
  private node: ScriptProcessorNode | null = null;
  private src: MediaStreamAudioSourceNode | null = null;
  private mute: GainNode | null = null;
  private playing = new Set<AudioBufferSourceNode>();
  private next = 0;
  private stopped = false;
  private muted = false;
  private tap: MediaStreamAudioDestinationNode | null = null;
  private recorder: MediaRecorder | null = null;
  private tapResult: Promise<string> | null = null;

  constructor(private sessionId: string, private ev: LiveEvents, private outbound?: "safetyCheck" | "lostContact") {}

  async start(): Promise<void> {
    this.ctx = new AudioContext();
    await this.ctx.resume();
    if (new URLSearchParams(window.location.search).get("rec") === "1") {
      this.tap = this.ctx.createMediaStreamDestination();
      this.recorder = new MediaRecorder(this.tap.stream);
      const chunks: BlobPart[] = [];
      this.tapResult = new Promise<string>((resolve, reject) => {
        this.recorder!.ondataavailable = e => { if (e.data.size) chunks.push(e.data); };
        this.recorder!.onstop = () => {
          const reader = new FileReader();
          reader.onload = () => resolve(String(reader.result).split(",")[1]);
          reader.onerror = () => reject(reader.error);
          reader.readAsDataURL(new Blob(chunks, { type: this.recorder!.mimeType }));
        };
      });
      window.__rpLiveAudioTap = { stop: () => {
        if (this.recorder?.state !== "inactive") this.recorder?.stop();
        return this.tapResult!;
      } };
      this.recorder.start();
    }
    this.stream = await navigator.mediaDevices.getUserMedia({ audio: { echoCancellation: true, noiseSuppression: true, autoGainControl: true } });
    const base = wsOrigin(window.location.origin);
    const ws = new WebSocket(new URL(`/api/v2/chat/sessions/${this.sessionId}/live?room=${encodeURIComponent(demoRoom())}${this.outbound ? `&mode=outbound&kind=${this.outbound}` : ""}`, base));
    ws.binaryType = "arraybuffer";
    this.ws = ws;
    await new Promise<void>((resolve, reject) => {
      const t = window.setTimeout(() => reject(new Error("Gemini Live did not connect.")), 15000);
      ws.onmessage = (e) => {
        if (e.data instanceof ArrayBuffer) return this.play(e.data);
        const m = JSON.parse(e.data as string);
        if (m.type === "ready") { window.clearTimeout(t); resolve(); this.ev.onReady(); }
        else if (m.type === "error") { window.clearTimeout(t); reject(new Error(m.message)); this.ev.onEnd(m.message); }
        else if (m.type === "heard" || m.type === "said") this.ev.onCaption?.(m.type, m.text);
        else if (m.type === "fallback") this.ev.onFallback?.(m.text);
        else if (m.type === "caller") this.ev.onCaller(m.text);
        else if (m.type === "turn") this.ev.onTurn(m.value);
        else if (m.type === "interrupted") this.clear();
      };
      ws.onerror = () => { window.clearTimeout(t); reject(new Error("Gemini Live connection failed.")); if (!this.stopped) this.ev.onEnd("Gemini Live connection failed."); };
      ws.onclose = () => { window.clearTimeout(t); reject(new Error("Gemini Live connection closed.")); if (!this.stopped) this.ev.onEnd(); };
    });
    if (this.stopped) return;
    this.src = this.ctx.createMediaStreamSource(this.stream);
    this.node = this.ctx.createScriptProcessor(2048, 1, 1);
    this.mute = this.ctx.createGain();
    this.mute.gain.value = 0;
    this.node.onaudioprocess = (e) => {
      const s = this.ws;
      if (this.muted || s?.readyState !== WebSocket.OPEN || s.bufferedAmount > 256_000) return;
      s.send(pcm16(e.inputBuffer.getChannelData(0), e.inputBuffer.sampleRate));
    };
    this.src.connect(this.node);
    this.node.connect(this.mute);
    this.mute.connect(this.ctx.destination);
  }

  /** Typed words during a call go to Gemini the same way as speech. */
  say(text: string) {
    if (this.ws?.readyState === WebSocket.OPEN) this.ws.send(JSON.stringify({ type: "text", text }));
  }

  private clear() {
    for (const s of this.playing) { try { s.stop(); } catch { /* ended */ } }
    this.playing.clear();
    this.next = this.ctx?.currentTime ?? 0;
  }

  private play(bytes: ArrayBuffer) {
    const ctx = this.ctx;
    if (!ctx || this.stopped) return;
    const pcm = new DataView(bytes);
    const buf = ctx.createBuffer(1, Math.floor(bytes.byteLength / 2), 24000);
    const ch = buf.getChannelData(0);
    for (let i = 0; i < ch.length; i++) ch[i] = pcm.getInt16(i * 2, true) / 32768;
    const s = ctx.createBufferSource();
    s.buffer = buf;
    s.connect(ctx.destination);
    if (this.tap) s.connect(this.tap);
    s.onended = () => this.playing.delete(s);
    this.playing.add(s);
    const at = Math.max(ctx.currentTime + 0.02, this.next);
    s.start(at);
    this.next = at + buf.duration;
  }

  setMuted(muted: boolean) { this.muted = muted; }

  stop() {
    if (this.stopped) return;
    this.stopped = true;
    this.clear();
    if (this.recorder?.state === "recording") this.recorder.stop();
    this.node?.disconnect();
    this.src?.disconnect();
    this.mute?.disconnect();
    this.stream?.getTracks().forEach((t) => t.stop());
    this.ws?.close();
    void this.ctx?.close();
  }
}

 declare global { interface Window { __rpLiveAudioTap?: { stop: () => Promise<string> } } }
