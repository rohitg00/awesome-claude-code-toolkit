import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";
import tailwindcss from "@tailwindcss/vite";

// Built files are served by the Python server under /app/ (the /assets/ route is reserved for the
// proprietary NTXP logo that is mounted at deploy time and never lives in git or the image).
export default defineConfig({
  base: "/app/",
  plugins: [react(), tailwindcss()],
  build: { outDir: "../ntxp_contacts/web/dist", emptyOutDir: true, sourcemap: false },
  server: { proxy: { "/api": "http://127.0.0.1:8099", "/assets": "http://127.0.0.1:8099", "/config.js": "http://127.0.0.1:8099" } },
  test: { environment: "jsdom", setupFiles: ["./src/test-setup.js"], globals: true },
});
