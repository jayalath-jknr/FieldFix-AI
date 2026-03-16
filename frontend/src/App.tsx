/**
 * FieldFix AI — Main Application
 *
 * Orchestrates the full technician experience:
 * 1. Industry/equipment selection
 * 2. Live camera + microphone session
 * 3. AI-guided real-time repair assistance
 */

import { useCallback, useRef, useState } from "react";
import { AnimatePresence, motion } from "framer-motion";
import { LogOut, Settings, Zap } from "lucide-react";

import { useSessionStore } from "./store/sessionStore";
import { useWebSocket } from "./hooks/useWebSocket";
import { useCamera } from "./hooks/useCamera";
import { useMicrophone } from "./hooks/useMicrophone";

import { IndustrySelector } from "./components/IndustrySelector";
import { CameraFeed } from "./components/CameraFeed";
import { VoiceIndicator } from "./components/VoiceIndicator";
import { CitationCard } from "./components/CitationCard";
import { CaseHistoryPanel } from "./components/CaseHistoryPanel";
import { StepTracker } from "./components/StepTracker";
import type { Industry } from "./types";

function App() {
  const {
    sessionId,
    industry,
    equipmentModel,
    agentState,
    citations,
    repairSteps,
    historicalCases,
    error,
    setSessionId,
    setIndustry,
    setEquipmentModel,
    setError,
    resetSession,
  } = useSessionStore();

  const [caseHistoryOpen, setCaseHistoryOpen] = useState(false);
  const canvasRef = useRef<HTMLCanvasElement>(null);

  const { connect, sendAudio, sendVideoFrame, sendBargeIn, disconnect } =
    useWebSocket();

  const {
    videoRef,
    startCamera,
    startCapture,
    stopCamera,
  } = useCamera({
    intervalMs: 2500,
    quality: 0.75,
    onFrame: sendVideoFrame,
    onError: (err) => setError(err),
  });

  const { startRecording, stopRecording } = useMicrophone({
    onAudioChunk: sendAudio,
    onSpeechStart: sendBargeIn,
  });

  const handleSelect = useCallback(
    async (selectedIndustry: Industry, selectedModel: string) => {
      const sid = crypto.randomUUID();
      setSessionId(sid);
      setIndustry(selectedIndustry);
      setEquipmentModel(selectedModel);

      try {
        // Start camera
        const stream = await startCamera();
        if (videoRef.current) {
          videoRef.current.srcObject = stream;
        }
        startCapture();

        // Start microphone
        await startRecording();

        // Connect WebSocket
        connect(sid, selectedIndustry, selectedModel);
      } catch (err) {
        setError(`Failed to start session: ${(err as Error).message}`);
      }
    },
    [
      connect,
      setSessionId,
      setIndustry,
      setEquipmentModel,
      setError,
      startCamera,
      startCapture,
      startRecording,
      videoRef,
    ]
  );

  const handleEndSession = useCallback(() => {
    disconnect();
    stopRecording();
    stopCamera();
    resetSession();
  }, [disconnect, stopRecording, stopCamera, resetSession]);

  // Show industry selector if no session
  if (!sessionId) {
    return <IndustrySelector onSelect={handleSelect} />;
  }

  return (
    <div className="h-full flex flex-col lg:flex-row overflow-hidden bg-surface">
      {/* Left: Camera + Diagnosis */}
      <div className="flex-1 flex flex-col min-h-0">
        {/* Top Bar */}
        <div className="flex items-center justify-between px-4 py-3 glass border-b border-white/5">
          <div className="flex items-center gap-3">
            <div className="w-8 h-8 rounded-lg gradient-primary flex items-center justify-center">
              <Zap className="w-4 h-4 text-white" />
            </div>
            <div>
              <h1 className="text-sm font-bold text-gradient">FieldFix AI</h1>
              <p className="text-[11px] text-text-muted">
                {equipmentModel} · {industry?.toUpperCase()}
              </p>
            </div>
          </div>
          <div className="flex items-center gap-2">
            <VoiceIndicator state={agentState} />
            <button
              id="end-session-btn"
              onClick={handleEndSession}
              className="ml-3 p-2 rounded-lg hover:bg-surface-lighter transition-colors text-text-muted hover:text-danger"
              title="End Session"
            >
              <LogOut className="w-4 h-4" />
            </button>
          </div>
        </div>

        {/* Camera Feed */}
        <div className="flex-1 min-h-0 p-3">
          <CameraFeed stream={videoRef.current?.srcObject as MediaStream | null} videoRef={videoRef} />
        </div>

        {/* Hidden canvas for frame capture */}
        <canvas ref={canvasRef} className="hidden" />
      </div>

      {/* Right: Citations + Steps */}
      <div className="w-full lg:w-96 flex flex-col glass border-t lg:border-t-0 lg:border-l border-white/5 max-h-[40vh] lg:max-h-full overflow-y-auto">
        <div className="p-4 space-y-4">
          {/* Repair Steps */}
          <StepTracker steps={repairSteps} />

          {/* Citations */}
          {citations.length > 0 && (
            <div>
              <h3 className="text-xs font-semibold text-text-secondary uppercase tracking-wider mb-2 flex items-center gap-1.5">
                📖 Manual Citations
              </h3>
              <div className="space-y-1">
                {citations.map((c, i) => (
                  <CitationCard
                    key={`${c.citation}-${i}`}
                    citation={c}
                    isLatest={i === citations.length - 1}
                  />
                ))}
              </div>
            </div>
          )}

          {/* Error */}
          <AnimatePresence>
            {error && (
              <motion.div
                initial={{ opacity: 0, y: 10 }}
                animate={{ opacity: 1, y: 0 }}
                exit={{ opacity: 0 }}
                className="rounded-xl p-3 bg-danger/10 border border-danger/20"
              >
                <p className="text-sm text-danger-light">{error}</p>
              </motion.div>
            )}
          </AnimatePresence>

          {/* Empty State */}
          {citations.length === 0 && repairSteps.length === 0 && !error && (
            <div className="text-center py-12">
              <div className="w-16 h-16 rounded-2xl bg-surface-lighter flex items-center justify-center mx-auto mb-4">
                <Settings className="w-8 h-8 text-text-muted animate-spin" style={{ animationDuration: "3s" }} />
              </div>
              <p className="text-sm text-text-secondary">
                Point your camera at the equipment and describe the issue.
              </p>
              <p className="text-xs text-text-muted mt-2">
                AI diagnosis and manual citations will appear here.
              </p>
            </div>
          )}
        </div>
      </div>

      {/* Case History Panel */}
      <CaseHistoryPanel
        cases={historicalCases}
        isOpen={caseHistoryOpen}
        onToggle={() => setCaseHistoryOpen(!caseHistoryOpen)}
      />
    </div>
  );
}

export default App;
