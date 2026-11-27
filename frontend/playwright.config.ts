import path from "node:path";
import { defineConfig, devices } from "@playwright/test";

const port = 4318;
const repoRoot = path.resolve(__dirname, "..");
const buildDir = path.join(__dirname, "app", "build");

export default defineConfig({
  testDir: "./e2e",
  fullyParallel: true,
  forbidOnly: !!process.env.CI,
  retries: 0,
  reporter: process.env.CI ? [["list"], ["html", { open: "never" }]] : "list",
  use: {
    baseURL: `http://127.0.0.1:${port}`,
    locale: "de-DE",
  },
  projects: [{ name: "chromium", use: { ...devices["Desktop Chrome"] } }],
  // Das Binary braucht migrierte Datenbank und DATABASE_URL_APP aus der Umgebung des Aufrufers.
  webServer: {
    command: "cargo run --locked -p chronos -- serve",
    cwd: repoRoot,
    url: `http://127.0.0.1:${port}/healthz`,
    reuseExistingServer: !process.env.CI,
    timeout: 300_000,
    env: {
      CHRONOS_LISTEN: `127.0.0.1:${port}`,
      CHRONOS_FRONTEND_DIR: buildDir,
    },
  },
});
