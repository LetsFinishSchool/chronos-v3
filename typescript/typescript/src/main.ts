import { rootLog } from "./core/logger.js";

const mode = process.argv[2];
try {
  if (mode === "web") await (await import("./web/server.js")).startWeb();
  else if (mode === "worker") await (await import("./worker/worker.js")).startWorker();
  else { console.error("Aufruf: main.js web|worker"); process.exit(2); }
} catch (e) {
  rootLog.error({ err: e instanceof Error ? (e.stack ?? e.message) : String(e) }, "Start fehlgeschlagen");
  process.exit(1);
}
