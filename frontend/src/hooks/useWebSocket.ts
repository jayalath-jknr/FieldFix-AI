/**
 * WebSocket hook — handles:
 * - Connection lifecycle with exponential backoff reconnect
 * - Multiplexing binary audio and JSON control messages
 * - Barge-in detection (when user speaks while agent is speaking)
 */

import { useCallback, useEffect, useRef, useState } from "react";
import { useSessionStore } from "../store/sessionStore";

const WS_URL = import.meta.env.VITE_WS_URL || "ws://localhost:8000";
const MAX_RECONNECT_ATTEMPTS = 5;
const RECONNECT_BASE_MS = 1000;

// Audio playback via Web Audio API
let audioCtx: AudioContext | null = null;
let nextPlayTime = 0;
// If nextPlayTime has drifted more than this many seconds into the future,
// we suspect a stale queue and snap back to play immediately.
const MAX_QUEUE_AHEAD_SEC = 0.5;

function playAudioChunk(buffer: ArrayBuffer) {
  if (!audioCtx) audioCtx = new AudioContext({ sampleRate: 24000 });
  if (audioCtx.state === "suspended") audioCtx.resume();

  const pcm = new Int16Array(buffer);
  const float32 = new Float32Array(pcm.length);
  for (let i = 0; i < pcm.length; i++) {
    float32[i] = pcm[i] / 32768.0;
  }

  const audioBuffer = audioCtx.createBuffer(1, float32.length, 24000);
  audioBuffer.copyToChannel(float32, 0);

  const source = audioCtx.createBufferSource();
  source.buffer = audioBuffer;
  source.connect(audioCtx.destination);

  const now = audioCtx.currentTime;
  // Reset if the queue has drifted too far behind real-time (e.g. after a
  // tab switch or a long silence) to avoid a stale backlog.
  if (nextPlayTime < now - MAX_QUEUE_AHEAD_SEC) nextPlayTime = now;
  const startTime = Math.max(now, nextPlayTime);
  source.start(startTime);
  nextPlayTime = startTime + audioBuffer.duration;
}

export function useWebSocket() {
  const wsRef = useRef<WebSocket | null>(null);
  const reconnectAttempts = useRef(0);
  const reconnectTimer = useRef<ReturnType<typeof setTimeout>>(undefined);
  const [isConnecting, setIsConnecting] = useState(false);

  const {
    setConnected,
    setAgentState,
    setDiagnosis,
    addCitation,
    addHistoricalCase,
    setError,
  } = useSessionStore();

  const handleControlMessage = useCallback(
    (msg: Record<string, unknown>) => {
      if (msg.type === "session_ready") {
        setAgentState("listening");
      } else if (msg.type === "tool_result") {
        const tool = msg.tool as string;
        const data = msg.data as Record<string, unknown>;

        if (tool === "diagnose_frame") {
          setDiagnosis(data as never);
          setAgentState("thinking");
        } else if (tool === "search_manual") {
          const results = (data as Record<string, unknown[]>).results ?? [];
          results.forEach((r) => addCitation(r as never));
        } else if (tool === "lookup_similar_cases") {
          const cases = (data as Record<string, unknown[]>).cases ?? [];
          cases.forEach((c) => addHistoricalCase(c as never));
        }
      }
    },
    [setAgentState, setDiagnosis, addCitation, addHistoricalCase]
  );

  const connect = useCallback(
    (sid: string, industry: string, equipmentModel: string) => {
      // Prevent duplicate connections: skip if already open OR still connecting
      const state = wsRef.current?.readyState;
      if (state === WebSocket.OPEN || state === WebSocket.CONNECTING) return;

      setIsConnecting(true);
      const ws = new WebSocket(`${WS_URL}/ws/${sid}`);
      ws.binaryType = "arraybuffer";
      wsRef.current = ws;

      ws.onopen = () => {
        setIsConnecting(false);
        reconnectAttempts.current = 0;
        setConnected(true);
        ws.send(
          JSON.stringify({
            type: "session_init",
            industry,
            equipment_model: equipmentModel,
            technician_id:
              localStorage.getItem("technician_id") ?? "anonymous",
          })
        );
      };

      let agentWasSpeaking = false;
      ws.onmessage = (event) => {
        if (event.data instanceof ArrayBuffer) {
          playAudioChunk(event.data);
          // Only update React state on the transition, not every chunk,
          // to avoid flooding the render queue.
          if (!agentWasSpeaking) {
            setAgentState("speaking");
            agentWasSpeaking = true;
          }
        } else {
          agentWasSpeaking = false; // text message = turn boundary
          const msg = JSON.parse(event.data as string);
          handleControlMessage(msg);
        }
      };

      ws.onerror = () => setError("Connection error");

      ws.onclose = (event) => {
        setConnected(false);
        // Don't retry on server-side deliberate close (e.g. Gemini auth failure)
        // code 1011 = Internal Error (server crashed), 1008 = Policy Violation
        // Retrying these will just fail again immediately.
        if (event.code === 1011 || event.code === 1008) {
          setError("Session failed — check that the backend is running and GCP credentials are valid.");
          return;
        }
        if (reconnectAttempts.current < MAX_RECONNECT_ATTEMPTS) {
          const delay =
            RECONNECT_BASE_MS *
            Math.pow(2, reconnectAttempts.current);
          reconnectAttempts.current++;
          reconnectTimer.current = setTimeout(
            () => connect(sid, industry, equipmentModel),
            delay
          );
        } else {
          setError("Connection lost. Please refresh.");
        }
      };
    },
    [setConnected, setAgentState, setError, handleControlMessage]
  );

  const sendAudio = useCallback((pcmData: ArrayBuffer) => {
    if (wsRef.current?.readyState === WebSocket.OPEN) {
      wsRef.current.send(pcmData);
    }
  }, []);

  const sendVideoFrame = useCallback((base64jpeg: string) => {
    if (wsRef.current?.readyState === WebSocket.OPEN) {
      wsRef.current.send(
        JSON.stringify({ type: "video_frame", data: base64jpeg })
      );
    }
  }, []);

  const sendBargeIn = useCallback(() => {
    if (wsRef.current?.readyState === WebSocket.OPEN) {
      wsRef.current.send(JSON.stringify({ type: "barge_in" }));
      setAgentState("interrupted");
    }
  }, [setAgentState]);

  const disconnect = useCallback(() => {
    clearTimeout(reconnectTimer.current);
    if (wsRef.current?.readyState === WebSocket.OPEN) {
      wsRef.current.send(JSON.stringify({ type: "end_session" }));
    }
    wsRef.current?.close();
  }, []);

  useEffect(() => () => disconnect(), [disconnect]);

  return {
    connect,
    sendAudio,
    sendVideoFrame,
    sendBargeIn,
    disconnect,
    isConnecting,
  };
}
