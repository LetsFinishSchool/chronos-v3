import * as webpush from "web-push";
import { config } from "../core/config.js";
import type { Channel } from "./types.js";

// VAPID-Signatur und Nutzlastverschlüsselung übernimmt die Bibliothek `web-push`.
let ready = false;
function init() {
  if (ready) return;
  webpush.setVapidDetails(config.vapid.subject, config.vapid.publicKey, config.vapid.privateKey);
  ready = true;
}

export const webpushChannel: Channel = {
  name: "webpush",
  async deliver(req) {
    const subs = req.recipient.pushSubscriptions;
    if (subs.length === 0) return "skipped";
    init();
    const payload = JSON.stringify({ event_type: req.eventType, event_id: req.eventId });
    const results = await Promise.allSettled(subs.map((s) =>
      webpush.sendNotification({ endpoint: s.endpoint, keys: { p256dh: s.p256dh, auth: s.auth } }, payload, { TTL: 60, timeout: 10_000, headers: { Urgency: "high" } })));
    const failed = results.filter((r) => r.status === "rejected");
    if (failed.length === results.length) throw new Error(String((failed[0] as PromiseRejectedResult).reason));
    return "sent";
  },
};
