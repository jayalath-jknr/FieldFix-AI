/**
 * CameraFeed — Live camera with frame capture overlay.
 * Shows the camera stream, scan line animation, and status badges.
 */

import { useEffect } from "react";
import { CameraOff } from "lucide-react";
import { motion, AnimatePresence } from "framer-motion";
import { useSessionStore } from "../store/sessionStore";

interface Props {
  stream: MediaStream | null;
  videoRef: React.RefObject<HTMLVideoElement | null>;
}

export function CameraFeed({ stream, videoRef }: Props) {
  const { currentDiagnosis, agentState, isConnected } = useSessionStore();

  useEffect(() => {
    if (videoRef.current && stream) {
      videoRef.current.srcObject = stream;
    }
  }, [stream, videoRef]);

  const severityColor: Record<string, string> = {
    low: "bg-green-500",
    medium: "bg-yellow-500",
    high: "bg-orange-500",
    critical: "bg-red-500",
    unknown: "bg-gray-500",
  };

  return (
    <div className="relative w-full h-full overflow-hidden rounded-2xl bg-black">
      {/* Video Feed */}
      <video
        ref={videoRef}
        autoPlay
        playsInline
        muted
        className="w-full h-full object-cover"
      />

      {/* Scan Line Animation */}
      {isConnected && agentState !== "idle" && (
        <motion.div
          className="absolute left-0 right-0 h-0.5 bg-gradient-to-r from-transparent via-cyan-400 to-transparent opacity-60"
          animate={{ top: ["0%", "100%", "0%"] }}
          transition={{ duration: 4, repeat: Infinity, ease: "linear" }}
        />
      )}

      {/* Connection Badge */}
      <div className="absolute top-3 left-3 flex items-center gap-2">
        <div
          className={`w-2.5 h-2.5 rounded-full ${
            isConnected ? "bg-green-400 animate-pulse" : "bg-red-400"
          }`}
        />
        <span className="text-xs font-medium text-white/80 glass px-2 py-1 rounded-full">
          {isConnected ? "LIVE" : "OFFLINE"}
        </span>
      </div>

      {/* No Camera Fallback */}
      {!stream && (
        <div className="absolute inset-0 flex flex-col items-center justify-center bg-surface/90">
          <CameraOff className="w-16 h-16 text-text-muted mb-4" />
          <p className="text-text-secondary text-sm">Camera not started</p>
        </div>
      )}

      {/* Diagnosis Overlay */}
      <AnimatePresence>
        {currentDiagnosis && (
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: 20 }}
            className="absolute bottom-0 left-0 right-0 glass p-4"
          >
            <div className="flex items-start gap-3">
              <div
                className={`w-3 h-3 rounded-full mt-1 flex-shrink-0 ${
                  severityColor[currentDiagnosis.severity] || "bg-gray-500"
                }`}
              />
              <div className="flex-1 min-w-0">
                <p className="text-sm font-semibold text-white truncate">
                  {currentDiagnosis.likely_fault}
                </p>
                {currentDiagnosis.draw_attention_to && (
                  <p className="text-xs text-cyan-300 mt-1">
                    👁 {currentDiagnosis.draw_attention_to}
                  </p>
                )}
                {currentDiagnosis.immediate_action && (
                  <p className="text-xs text-amber-300 mt-1">
                    ⚡ {currentDiagnosis.immediate_action}
                  </p>
                )}
                <div className="flex items-center gap-3 mt-2">
                  <span className="text-xs text-text-muted">
                    Confidence: {Math.round(currentDiagnosis.confidence * 100)}%
                  </span>
                  {!currentDiagnosis.safe_to_operate && (
                    <span className="text-xs text-red-400 font-semibold">
                      ⚠ NOT SAFE TO OPERATE
                    </span>
                  )}
                </div>
              </div>
            </div>
          </motion.div>
        )}
      </AnimatePresence>

      {/* Hidden canvas for frame capture */}
      <canvas className="hidden" />
    </div>
  );
}
