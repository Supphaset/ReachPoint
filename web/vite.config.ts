import { defineConfig } from "vitest/config";
import { loadEnv } from "vite";
import react from "@vitejs/plugin-react";

// The app reads the shared fixtures (contract/) and the flood package (data/) straight from the repo,
// so they have one source of truth. Live Firestore views replace the fixtures once the friend's API is up.
export default defineConfig(({ command, mode }) => ({
  plugins: [react()],
  // Built assets are served by the API. Ordinary /desk links must work without a data query parameter.
  // An explicit VITE_DATA=fixtures still builds the offline demo; dev/test defaults stay unchanged.
  define: command === "build" ? {
    "import.meta.env.VITE_DATA": JSON.stringify(loadEnv(mode, ".", "VITE_").VITE_DATA || "api"),
  } : {},
  server: { fs: { allow: [".."] } },
  test: { environment: "node" },
}));
