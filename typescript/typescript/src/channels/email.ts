import nodemailer from "nodemailer";
import { config } from "../core/config.js";
import type { Channel } from "./types.js";

const transport = nodemailer.createTransport({
  host: config.smtp.host, port: config.smtp.port, secure: false, ignoreTLS: true,
  connectionTimeout: 5000, greetingTimeout: 5000, socketTimeout: 10000,
});

export const emailChannel: Channel = {
  name: "email",
  async deliver(req) {
    if (!req.recipient.email) return "skipped";
    await transport.sendMail({
      from: "chronos-spike@example.test",
      to: req.recipient.email,
      subject: `Chronos: ${req.eventType}`,
      text: `Ereignis ${req.eventType} (${req.eventId})`,
      headers: { "X-Chronos-Idempotency-Key": req.idempotencyKey, "X-Chronos-Correlation-Id": req.correlationId },
    });
    return "sent";
  },
};
