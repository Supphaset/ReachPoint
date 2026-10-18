import { defineConfig } from "vitest/config";
import react from "@vitejs/plugin-react";

// V2 reads the API through the local proxy and bundles the static street layer from data/.
export default defineConfig({
  plugins: [react()],
  server: { fs: { allow: [".."] }, proxy: { "/api": "http://127.0.0.1:8093" } },
  test: { environment: "node", setupFiles: ["./test/setup.mjs"] },
});
