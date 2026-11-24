// Erzeugt die Typen der Frontend-Brücke aus GET $BASE_URL/api/v1/operations (Dienst muss laufen).
import { mkdirSync, writeFileSync } from "node:fs";
import { compile, type JSONSchema } from "json-schema-to-typescript";

interface Op { name: string; params_schema: JSONSchema; result_schema: JSONSchema }

const baseUrl = process.env.BASE_URL ?? "http://localhost:8080";
const res = await fetch(`${baseUrl}/api/v1/operations`);
if (!res.ok) throw new Error(`Operationsliste nicht abrufbar: ${res.status}`);
const { operations } = (await res.json()) as { operations: Op[] };

const pascal = (n: string) => n.split(/[._]/).map((s) => s[0]!.toUpperCase() + s.slice(1)).join("");
const opts = { bannerComment: "", additionalProperties: false, format: false as const, style: { singleQuote: false } };

let out = "// GENERIERT von scripts/bridge.ts aus /api/v1/operations. Nicht von Hand ändern.\n\n";
for (const op of operations) {
  out += await compile(op.params_schema, `${pascal(op.name)}Params`, opts);
  out += await compile(op.result_schema, `${pascal(op.name)}Result`, opts);
}
out += "export interface Operations {\n";
for (const op of operations) out += `  ${JSON.stringify(op.name)}: { params: ${pascal(op.name)}Params; result: ${pascal(op.name)}Result };\n`;
out += "}\n";

mkdirSync("bridge/generated", { recursive: true });
writeFileSync("bridge/generated/operations.ts", out);
console.log(`bridge/generated/operations.ts: ${operations.length} Operationen`);
