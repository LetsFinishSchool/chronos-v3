import type { ChannelName } from "../core/channels.js";

export interface PushSubscriptionRow { endpoint: string; p256dh: string; auth: string }

export interface DeliveryRequest {
  eventId: string;
  eventType: string;
  correlationId: string;
  idempotencyKey: string;
  recipient: { id: string; email: string | null; pushSubscriptions: PushSubscriptionRow[] };
}

/** `"skipped"`: Voraussetzung fehlt (z. B. kein Push-Abo). Fehler = Exception. */
export interface Channel {
  readonly name: ChannelName;
  deliver(req: DeliveryRequest): Promise<"sent" | "skipped">;
}
