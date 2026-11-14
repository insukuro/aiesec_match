import { defineConfig } from "vitest/config";
import react from "@vitejs/plugin-react-swc";
import { fileURLToPath, URL } from "node:url";

export default defineConfig({
  plugins: [react()],
  resolve: {
    alias: { "@": fileURLToPath(new URL("./src", import.meta.url)) },
  },
  test: {
    environment: "jsdom",
    globals: true,
    setupFiles: ["./src/test/setup.ts"],
    env: { TZ: "UTC" },
    // msw v2 и jsdom: нужно, чтобы `Response`/`Request`/`Headers` были
    // доступны как глобалы (в Node 20 они есть, но jsdom их перетирает)
    environmentOptions: { jsdom: { url: "http://localhost/" } },
    coverage: {
      provider: "v8",
      reporter: ["text", "html", "lcov"],
      reportsDirectory: "./coverage",
      exclude: [
        "**/node_modules/**",
        "**/*.config.{ts,js}",
        "**/main.tsx",
        "**/app/providers.tsx",
        "**/app/router.tsx",
        "**/*.d.ts",
        "**/shared/api/schema.ts",
        "**/test/**",
        "**/*.stories.{ts,tsx}",
      ],
      thresholds: { lines: 60, functions: 60, branches: 50, statements: 60 },
    },
  },
});