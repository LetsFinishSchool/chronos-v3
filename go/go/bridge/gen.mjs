// Erzeugt bridge/generated/operations.ts aus GET $BASE_URL/api/v1/operations (einzige Quelle).
// Die Typen je Operation übernimmt json-schema-to-typescript; hier wird nur die Zuordnung Name → Typen ausgegeben.
import { compile } from "json-schema-to-typescript";
import { mkdirSync, writeFileSync } from "node:fs";

const base = process.env.BASE_URL ?? "http://localhost:9080";
const res = await fetch(`${base}/api/v1/operations`);
if (!res.ok) throw new Error(`GET /api/v1/operations: ${res.status}`);
const { operations } = await res.json();

const pascal = (n) => n.split(/[._]/).map((s) => s[0].toUpperCase() + s.slice(1)).join("");
let out = "// GENERIERT aus /api/v1/operations (make bridge). Nicht von Hand ändern.\n\n";
const map = [];
for (const op of operations) {
  const p = pascal(op.name) + "Params";
  const r = pascal(op.name) + "Result";
  const opts = { bannerComment: "", additionalProperties: false, format: true };
  out += await compile({ ...op.params_schema, title: p }, p, opts);
  out += await compile({ ...op.result_schema, title: r }, r, opts);
  map.push(`  ${JSON.stringify(op.name)}: { params: ${p}; result: ${r} };`);
}
out += `export interface OperationMap {\n${map.join("\n")}\n}\n`;
mkdirSync("generated", { recursive: true });
writeFileSync("generated/operations.ts", out);
console.log(`bridge: ${operations.length} Operationen erzeugt`);
