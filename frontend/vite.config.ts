import react from "@vitejs/plugin-react";
import { fileURLToPath, URL } from "node:url";
import { defineConfig } from "vitest/config";

export default defineConfig({
  plugins: [react()],
  resolve: {
    // `@` apunta a src/ para que los imports no degeneren en ../../../.
    alias: {
      "@": fileURLToPath(new URL("./src", import.meta.url)),
    },
  },
  server: {
    port: 5173,
    // El backend se consume a traves del proxy para evitar CORS en desarrollo.
    proxy: {
      "/api": {
        target: process.env.VITE_API_TARGET ?? "http://localhost:8000",
        changeOrigin: true,
      },
      // Swagger bajo el mismo origen, igual que en produccion.
      "/docs": {
        target: process.env.VITE_API_TARGET ?? "http://localhost:8000",
        changeOrigin: true,
      },
      "/openapi.json": {
        target: process.env.VITE_API_TARGET ?? "http://localhost:8000",
        changeOrigin: true,
      },
    },
  },
  test: {
    environment: "jsdom",
    globals: true,
    setupFiles: ["./src/setupTests.ts"],
    coverage: {
      provider: "v8",
      include: ["src/**/*.{ts,tsx}"],
      exclude: ["src/main.tsx", "src/setupTests.ts", "src/**/*.test.{ts,tsx}"],
    },
  },
});
