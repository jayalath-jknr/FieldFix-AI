/**
 * Canvas frame extraction utilities for camera capture.
 */

/**
 * Capture a JPEG frame from a video element.
 * Returns base64-encoded JPEG string (without data URL prefix).
 */
export function captureFrameAsBase64(
  video: HTMLVideoElement,
  canvas: HTMLCanvasElement,
  quality = 0.75
): string | null {
  if (video.videoWidth === 0 || video.videoHeight === 0) return null;

  canvas.width = video.videoWidth;
  canvas.height = video.videoHeight;

  const ctx = canvas.getContext("2d");
  if (!ctx) return null;

  ctx.drawImage(video, 0, 0);
  const dataUrl = canvas.toDataURL("image/jpeg", quality);
  return dataUrl.split(",")[1];
}

/**
 * Estimate the byte size of a base64 string.
 */
export function estimateBase64Bytes(base64: string): number {
  return Math.ceil(base64.length * 0.75);
}

/**
 * Check if a frame exceeds the maximum allowed size.
 */
export function isFrameWithinSizeLimit(
  base64: string,
  maxBytes = 500_000
): boolean {
  return estimateBase64Bytes(base64) <= maxBytes;
}
