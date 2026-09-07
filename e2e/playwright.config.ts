import { defineConfig } from "@playwright/test";

// The deployed self-hosted stack (see config/images.yaml in the repo root
// and ~/work/services/kroki/docker-compose.yml).
const BASE_URL = process.env.EXCALIDRAW_URL ?? "http://localhost:44186";

export default defineConfig({
  testDir: "./tests",
  timeout: 90_000,
  expect: { timeout: 10_000 },
  // Collaboration tests share two tabs in one room — keep them serial.
  fullyParallel: false,
  workers: 1,
  reporter: [["list"]],
  use: {
    baseURL: BASE_URL,
    headless: true,
    viewport: { width: 1440, height: 900 },
    screenshot: "only-on-failure",
    trace: "retain-on-failure",
    // Unset = bundled Chromium (reproducible). Set to "chrome" to use the
    // system Google Chrome instead: EXCALIDRAW_BROWSER_CHANNEL=chrome.
    channel: process.env.EXCALIDRAW_BROWSER_CHANNEL as "chrome" | undefined,
  },
});
