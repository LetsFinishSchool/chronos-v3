import { pino, type Logger } from "pino";

export type Log = Logger;

/** JSON-Zeilen auf stdout mit ts, level, msg (correlation_id und event_id kommen über child()). */
export const rootLog: Log = pino({
  messageKey: "msg",
  base: undefined,
  timestamp: () => `,"ts":"${new Date().toISOString()}"`,
  formatters: { level: (label) => ({ level: label }) },
});
