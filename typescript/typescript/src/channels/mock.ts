import { config } from "../core/config.js";
import type { Channel } from "./types.js";

export const mockChannel: Channel = {
  name: "mock",
  async deliver(req) {
    const res = await fetch(`${config.mockChannelUrl}/deliver`, {
      method: "POST",
      headers: { "Content-Type": "application/json", "Idempotency-Key": req.idempotencyKey },
      body: JSON.stringify({ recipient: req.recipient.id, event_type: req.eventType, event_id: req.eventId, correlation_id: req.correlationId }),
      signal: AbortSignal.timeout(5000),
    });
    if (!res.ok) throw new Error(`Mock-Kanal antwortete ${res.status}`);
    return "sent";
  },
};
