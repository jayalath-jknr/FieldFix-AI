import { defineConfig } from "vite";
import tailwindcss from "@tailwindcss/vite";
import react from "@vitejs/plugin-react";
import { VitePWA } from "vite-plugin-pwa";

// https://vite.dev/config/
export default defineConfig({
  plugins: [
    tailwindcss(),
    react(),
    VitePWA({
      registerType: "autoUpdate",
      includeAssets: ["vite.svg", "icons/icon-192.png", "icons/icon-512.png"],
      manifest: {
        name: "FieldFix AI",
        short_name: "FieldFix",
        description:
          "Real-time AI assistant for field technicians — grounded in equipment manuals.",
        theme_color: "#0f172a",
        background_color: "#0f172a",
        display: "standalone",
        start_url: "/",
        icons: [
          {
            src: "/icons/icon-192.png",
            sizes: "192x192",
            type: "image/png",
          },
          {
            src: "/icons/icon-512.png",
            sizes: "512x512",
            type: "image/png",
          },
        ],
      },
    }),
  ],
  server: {
    port: 5173,
    proxy: {
      "/ws": {
        target: "http://localhost:8000",
        ws: true,
      },
      "/health": "http://localhost:8000",
      "/industries": "http://localhost:8000",
    },
  },
});
