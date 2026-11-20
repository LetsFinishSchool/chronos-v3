import { readdirSync } from "node:fs";
import { fileURLToPath } from "node:url";
import { z } from "zod";
import type { Kysely } from "kysely";
import type { Database } from "./db.js";
import type { Log } from "./logger.js";
import { AppError } from "./errors.js";

export interface Person { id: string; name: string; email: string | null }
export interface Affected { type: string; id: string; change: string }

/** Aufrufkontext einer Operation. Schreibende Operationen laufen in einer Transaktion (`db`). */
export interface Ctx {
  db: Kysely<Database>;
  caller: Person;
  correlationId: string;
  operation: string;
  bundleId: string;
  log: Log;
  /** Fehlerinjektion `after_history` (nur mit SPIKE_FAULTS=1 und Header). */
  faultAfterHistory: boolean;
  affected: Affected[];
}

export interface OperationDef<P extends z.ZodObject = z.ZodObject, R extends z.ZodObject = z.ZodObject> {
  /** Name, z. B. `appointment.create`. */
  name: string;
  description: string;
  mutating: boolean;
  params: P;
  result: R;
  run: (ctx: Ctx, params: z.output<P>) => Promise<z.input<R>>;
}

/** EINE Beschreibung je Operation: aus ihr entstehen Validierung, Endpunkt, Operationsliste, KI-Werkzeuge und Brückentypen. */
export function defineOperation<P extends z.ZodObject, R extends z.ZodObject>(def: OperationDef<P, R>): OperationDef<P, R> {
  registry.set(def.name, def as unknown as OperationDef);
  return def;
}

const registry = new Map<string, OperationDef>();

/** Lädt alle Dateien in `domain/ops/` (Eintragen = neue Datei anlegen, keine Liste pflegen). */
export async function loadOperations(): Promise<void> {
  const dir = new URL("../domain/ops/", import.meta.url);
  for (const f of readdirSync(fileURLToPath(dir)).sort()) {
    if (/\.(ts|js)$/.test(f) && !/\.d\.ts$/.test(f) && !/\.test\./.test(f)) await import(new URL(f, dir).href);
  }
}

export const getOperation = (name: string) => registry.get(name);
export const allOperations = (): OperationDef[] => [...registry.values()].sort((a, b) => a.name.localeCompare(b.name));

type Json = Record<string, unknown>;
function schemaOf(s: z.ZodType, io: "input" | "output"): Json {
  const j = z.toJSONSchema(s, { target: "draft-2020-12", io, unrepresentable: "any" }) as Json;
  delete j["$schema"];
  return j;
}

export function describe(op: OperationDef) {
  return {
    name: op.name,
    description: op.description,
    mutating: op.mutating,
    preview_supported: op.mutating,
    params_schema: schemaOf(op.params, "input"),
    result_schema: schemaOf(op.result, "output"),
  };
}

/** Werkzeugdefinitionen im Anthropic-Format, abgeleitet aus den Operationen. */
export function aiTools() {
  return allOperations().map((op) => ({
    name: op.name.replaceAll(".", "_"),
    description: op.description,
    input_schema: schemaOf(op.params, "input"),
  }));
}

export function operationByToolName(tool: string): OperationDef | undefined {
  return allOperations().find((o) => o.name.replaceAll(".", "_") === tool);
}

class Rollback extends Error {}

export type Outcome = { result: unknown } | { preview: { count: number; affected: Affected[] } };

export interface Invocation {
  db: Kysely<Database>;
  caller: Person;
  correlationId: string;
  log: Log;
  faultAfterHistory: boolean;
}

/** Führt eine Operation aus: Validierung, Transaktion (bei schreibend), Vorschau = Ausführung mit Rücknahme. */
export async function invoke(name: string, rawParams: unknown, preview: boolean, inv: Invocation): Promise<Outcome> {
  const op = registry.get(name);
  if (!op) throw new AppError("not_found", `Operation ${name} unbekannt`);
  const parsed = op.params.safeParse(rawParams ?? {});
  if (!parsed.success) {
    const msg = parsed.error.issues.map((i) => `${i.path.join(".") || "params"}: ${i.message}`).join("; ");
    throw new AppError("validation_error", msg);
  }
  const base = { ...inv, operation: name, bundleId: crypto.randomUUID(), affected: [] as Affected[] };
  if (!op.mutating) {
    const result = await op.run({ ...base }, parsed.data);
    return { result: op.result.parse(result) };
  }
  let result: unknown;
  try {
    await inv.db.transaction().execute(async (trx) => {
      result = await op.run({ ...base, db: trx }, parsed.data);
      if (preview) throw new Rollback();
    });
  } catch (e) {
    if (!(e instanceof Rollback)) throw e;
    return { preview: { count: base.affected.length, affected: base.affected } };
  }
  return { result: op.result.parse(result) };
}
