import Anthropic from "@anthropic-ai/sdk";
import { z } from "zod";
import { aiTools, defineOperation, operationByToolName } from "../../core/operation.js";
import { AppError } from "../../core/errors.js";
import { config } from "../../core/config.js";
import { uuid } from "../schemas.js";

const client = new Anthropic({ baseURL: config.ai.baseUrl, apiKey: config.ai.apiKey || "unset", maxRetries: 0, timeout: 60_000 });

const ceilDiv = (n: bigint, d: bigint) => (n + d - 1n) / d;

defineOperation({
  name: "ai.ask",
  description: "Fragt die KI (Anthropic Messages API) mit den Chronos-Operationen als Werkzeugen. Vorgeschlagene Aufrufe werden NICHT ausgeführt.",
  mutating: false,
  params: z.strictObject({ prompt: z.string().min(1).max(8000), team_id: uuid.optional() }),
  result: z.object({
    text: z.string(),
    proposed_calls: z.array(z.object({ name: z.string(), input: z.record(z.string(), z.unknown()) })),
    usage: z.object({ input_tokens: z.number().int(), output_tokens: z.number().int() }),
  }),
  async run(ctx, p) {
    const system = `Du bist der Assistent von Chronos, einer Terminverwaltung. Schlage Aufrufe der bereitgestellten Werkzeuge vor, statt Text zu raten. Zeitpunkte sind UTC (…Z).`
      + (p.team_id ? ` Aktives Team: ${p.team_id}.` : "");
    let msg: Anthropic.Message;
    try {
      msg = await client.messages.create({
        model: config.ai.model, max_tokens: 1024, system,
        tools: aiTools() as Anthropic.Tool[], messages: [{ role: "user", content: p.prompt }],
      });
    } catch (e) {
      ctx.log.warn({ err: String(e) }, "KI-Aufruf fehlgeschlagen");
      throw new AppError("provider_error", "KI-Anbieter nicht erreichbar oder lehnt ab");
    }
    const text = msg.content.flatMap((b) => (b.type === "text" ? [b.text] : [])).join("\n");
    const proposed_calls = msg.content.flatMap((b) =>
      b.type === "tool_use" ? [{ name: operationByToolName(b.name)?.name ?? b.name, input: b.input as Record<string, unknown> }] : []);
    const usage = { input_tokens: msg.usage.input_tokens, output_tokens: msg.usage.output_tokens };
    const amount = ceilDiv(BigInt(usage.input_tokens) * BigInt(config.ai.priceInMicroEurPerMtok) + BigInt(usage.output_tokens) * BigInt(config.ai.priceOutMicroEurPerMtok), 1_000_000n);
    await ctx.db.insertInto("cost_entry").values({
      person_id: ctx.caller.id, provider: "anthropic", trigger_kind: "operation", trigger_name: ctx.operation, correlation_id: ctx.correlationId,
      quantity: JSON.stringify(usage), amount_micro_eur: amount.toString(),
    }).execute();
    return { text, proposed_calls, usage };
  },
});
