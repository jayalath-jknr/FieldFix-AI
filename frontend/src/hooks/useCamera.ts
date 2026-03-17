/**
 * Camera hook — manages getUserMedia stream + periodic frame capture.
 * Sends JPEG frames to the WebSocket every `intervalMs` milliseconds.
 * Respects battery by pausing frame capture when tab is hidden.
 */

import { useCallback, useEffect, useRef } from "react";

interface UseCameraOptions {
  intervalMs?: number;
  quality?: number;
  onFrame: (base64jpeg: string) => void;
  onError: (error: string) => void;
}

export function useCamera({
  intervalMs = 2500,
  quality = 0.75,
  onFrame,
  onError,
}: UseCameraOptions) {
  const streamRef = useRef<MediaStream | null>(null);
  const videoRef = useRef<HTMLVideoElement | null>(null);
  const canvasRef = useRef<HTMLCanvasElement | null>(null);
  const intervalRef = useRef<ReturnType<typeof setInterval>>(undefined);
  const isCapturing = useRef(false);

  const startCamera = useCallback(async () => {
    try {
      const stream = await navigator.mediaDevices.getUserMedia({
        video: {
          facingMode: { ideal: "environment" },
          width: { ideal: 1280 },
          height: { ideal: 720 },
        },
        audio: false,
      });
      streamRef.current = stream;
      return stream;
    } catch (err) {
      onError(`Camera access denied: ${(err as Error).message}`);
      throw err;
    }
  }, [onError]);

  const captureFrame = useCallback(() => {
    if (!videoRef.current || !canvasRef.current || !isCapturing.current) return;
    if (document.hidden) return;

    const video = videoRef.current;
    const canvas = canvasRef.current;

    if (video.videoWidth === 0) return;

    // Cap to 640×480 to keep frame payloads small.
    // Full 1280×720 JPEG frames add unnecessary bandwidth and serialisation
    // overhead without improving AI analysis quality meaningfully.
    const MAX_W = 640;
    const MAX_H = 480;
    const scale = Math.min(1, MAX_W / video.videoWidth, MAX_H / video.videoHeight);
    canvas.width = Math.round(video.videoWidth * scale);
    canvas.height = Math.round(video.videoHeight * scale);

    const ctx = canvas.getContext("2d");
    if (!ctx) return;

    ctx.drawImage(video, 0, 0, canvas.width, canvas.height);
    const dataUrl = canvas.toDataURL("image/jpeg", quality);
    const base64 = dataUrl.split(",")[1];
    onFrame(base64);
  }, [onFrame, quality]);

  const startCapture = useCallback(() => {
    isCapturing.current = true;
    intervalRef.current = setInterval(captureFrame, intervalMs);
  }, [captureFrame, intervalMs]);

  const stopCapture = useCallback(() => {
    isCapturing.current = false;
    clearInterval(intervalRef.current);
  }, []);

  const stopCamera = useCallback(() => {
    stopCapture();
    streamRef.current?.getTracks().forEach((t) => t.stop());
    streamRef.current = null;
  }, [stopCapture]);

  useEffect(() => () => stopCamera(), [stopCamera]);

  return {
    videoRef,
    canvasRef,
    startCamera,
    startCapture,
    stopCapture,
    stopCamera,
    stream: streamRef.current,
  };
}
