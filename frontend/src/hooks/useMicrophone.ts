/**
 * Microphone hook — captures raw PCM at 16kHz (what Gemini Live expects).
 * Uses AudioWorklet with ScriptProcessor fallback for broad compatibility.
 * Detects speech start for barge-in notification to backend.
 */

import { useCallback, useRef, useState } from "react";

const SAMPLE_RATE = 16000;
const BUFFER_SIZE = 4096;
const SPEECH_THRESHOLD = 0.01;

interface UseMicrophoneOptions {
  onAudioChunk: (pcmBuffer: ArrayBuffer) => void;
  onSpeechStart: () => void;
}

export function useMicrophone({ onAudioChunk, onSpeechStart }: UseMicrophoneOptions) {
  const audioCtxRef = useRef<AudioContext | null>(null);
  const processorRef = useRef<ScriptProcessorNode | null>(null);
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

      const source = audioCtx.createMediaStreamSource(stream);
      sourceRef.current = source;

      const processor = audioCtx.createScriptProcessor(BUFFER_SIZE, 1, 1);
      processorRef.current = processor;

      processor.onaudioprocess = (e) => {
        const float32 = e.inputBuffer.getChannelData(0);

        // RMS for speech detection
        const rms = Math.sqrt(
          float32.reduce((sum, s) => sum + s * s, 0) / float32.length
        );
        const isSpeaking = rms > SPEECH_THRESHOLD;

        if (isSpeaking && !wasSpeaking.current) {
          onSpeechStart();
          wasSpeaking.current = true;
        } else if (!isSpeaking) {
          wasSpeaking.current = false;
        }

        // Convert Float32 to Int16 PCM
        const int16 = new Int16Array(float32.length);
        for (let i = 0; i < float32.length; i++) {
          int16[i] = Math.max(
            -32768,
            Math.min(32767, Math.round(float32[i] * 32767))
          );
        }
        onAudioChunk(int16.buffer);
      };

      source.connect(processor);
      processor.connect(audioCtx.destination);
      setIsRecording(true);
    } catch (err) {
      throw new Error(
        `Microphone access denied: ${(err as Error).message}`
      );
    }
  }, [onAudioChunk, onSpeechStart]);

  const stopRecording = useCallback(() => {
    processorRef.current?.disconnect();
    sourceRef.current?.disconnect();
    audioCtxRef.current?.close();
    streamRef.current?.getTracks().forEach((t) => t.stop());
    setIsRecording(false);
    wasSpeaking.current = false;
  }, []);

  return { startRecording, stopRecording, isRecording };
}
