import path from "node:path";
import { defineConfig } from "vitest/config";

export default defineConfig({
  resolve: {
    alias: {
      "@": path.resolve(__dirname, "."),
    },
  },
  test: {
    environment: "jsdom",
    include: ["**/*.spec.{ts,tsx}"],
    exclude: ["**/node_modules/**", "**/.next/**"],
    setupFiles: ["./vitest-setup.ts"],
  },
});
