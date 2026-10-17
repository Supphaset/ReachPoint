import { defineConfig } from "vitest/config";
import react from "@vitejs/plugin-react";

// The app reads the shared fixtures (contract/) and the flood package (data/) straight from the repo,
// so they have one source of truth. Live Firestore views replace the fixtures once the friend's API is up.
export default defineConfig({
  plugins: [react()],
  server: { fs: { allow: [".."] }, proxy: { "/api": "http://127.0.0.1:8093" } },
  test: { environment: "node", setupFiles: ["./test/setup.mjs"] },
});
