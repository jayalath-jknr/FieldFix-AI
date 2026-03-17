/**
 * Microphone hook — captures raw PCM at 16kHz (what Gemini Live expects).
 * Uses AudioWorkletNode (ScriptProcessorNode is deprecated).
 * Accumulates 1024-sample (64ms) chunks for low-latency streaming.
 * Detects speech start for barge-in notification to backend.
 */

import { useCallback, useRef, useState } from "react";

const SAMPLE_RATE = 16000;
const SPEECH_THRESHOLD = 0.01;

// Inline AudioWorklet processor: accumulates 1024 samples, converts to
// Int16 PCM, computes RMS, and posts both back to the main thread.
const WORKLET_CODE = `
class PCMProcessor extends AudioWorkletProcessor {
  constructor() {
    super();
    this._buf = new Float32Array(1024);
    this._idx = 0;
  }
  process(inputs) {
    const ch = inputs[0] && inputs[0][0];
    if (!ch) return true;
    for (let i = 0; i < ch.length; i++) {
      this._buf[this._idx++] = ch[i];
      if (this._idx >= 1024) {
        const int16 = new Int16Array(1024);
        let sum = 0;
        for (let j = 0; j < 1024; j++) {
          const s = this._buf[j];
          sum += s * s;
          int16[j] = Math.max(-32768, Math.min(32767, Math.round(s * 32767)));
        }
        this.port.postMessage({ pcm: int16.buffer, rms: Math.sqrt(sum / 1024) }, [int16.buffer]);
        this._idx = 0;
      }
    }
    return true;
  }
}
registerProcessor('pcm-processor', PCMProcessor);
`;

interface UseMicrophoneOptions {
  onAudioChunk: (pcmBuffer: ArrayBuffer) => void;
  onSpeechStart: () => void;
}

export function useMicrophone({ onAudioChunk, onSpeechStart }: UseMicrophoneOptions) {
  const audioCtxRef = useRef<AudioContext | null>(null);
  const workletNodeRef = useRef<AudioWorkletNode | null>(null);
  const sourceRef = useRef<MediaStreamAudioSourceNode | null>(null);
  const streamRef = useRef<MediaStream | null>(null);
  const [isRecording, setIsRecording] = useState(false);
  const wasSpeaking = useRef(false);

  const startRecording = useCallback(async () => {
    try {
      const stream = await navigator.mediaDevices.getUserMedia({
        audio: {
          sampleRate: SAMPLE_RATE,
          channelCount: 1,
          echoCancellation: true,
          noiseSuppression: true,
          autoGainControl: true,
        },
      });
      streamRef.current = stream;

      const audioCtx = new AudioContext({ sampleRate: SAMPLE_RATE });
      audioCtxRef.current = audioCtx;

      // Load processor from a Blob URL so no separate file is needed
      const blob = new Blob([WORKLET_CODE], { type: "application/javascript" });
      const url = URL.createObjectURL(blob);
      await audioCtx.audioWorklet.addModule(url);
      URL.revokeObjectURL(url);

      const source = audioCtx.createMediaStreamSource(stream);
      sourceRef.current = source;

      const workletNode = new AudioWorkletNode(audioCtx, "pcm-processor");
      workletNodeRef.current = workletNode;

      workletNode.port.onmessage = (e: MessageEvent<{ pcm: ArrayBuffer; rms: number }>) => {
        const { pcm, rms } = e.data;
        const isSpeaking = rms > SPEECH_THRESHOLD;
        if (isSpeaking && !wasSpeaking.current) {
          onSpeechStart();
          wasSpeaking.current = true;
        } else if (!isSpeaking) {
          wasSpeaking.current = false;
        }
        onAudioChunk(pcm);
      };

      source.connect(workletNode);
      // Connect to destination to keep the graph alive (output is silent)
      workletNode.connect(audioCtx.destination);
      setIsRecording(true);
    } catch (err) {
      throw new Error(
        `Microphone access denied: ${(err as Error).message}`
      );
    }
  }, [onAudioChunk, onSpeechStart]);

  const stopRecording = useCallback(() => {
    workletNodeRef.current?.port.close();
    workletNodeRef.current?.disconnect();
    sourceRef.current?.disconnect();
    audioCtxRef.current?.close();
    streamRef.current?.getTracks().forEach((t) => t.stop());
    setIsRecording(false);
    wasSpeaking.current = false;
  }, []);

  return { startRecording, stopRecording, isRecording };
}
