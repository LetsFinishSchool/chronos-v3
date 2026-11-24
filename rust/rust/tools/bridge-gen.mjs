// S-10: erzeugt bridge/generated/operations.ts aus GET $BASE_URL/api/v1/operations.
// Typen entstehen mit der Bibliothek json-schema-to-typescript; hier steht nur der Leim.
import { compile } from "json-schema-to-typescript";
import http from "node:http";
import { mkdir, writeFile } from "node:fs/promises";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";

const baseUrl = process.env.BASE_URL ?? "http://localhost:10080";
const root = join(dirname(fileURLToPath(import.meta.url)), "..", "bridge", "generated");

// node:http statt fetch: undici sperrt einige Ports (u. a. 10080)
const { operations } = await new Promise((resolve, reject) => {
  http.get(`${baseUrl}/api/v1/operations`, (res) => {
    let body = "";
    res.on("data", (c) => (body += c));
    res.on("end", () => (res.statusCode === 200 ? resolve(JSON.parse(body)) : reject(new Error(`GET /api/v1/operations: ${res.statusCode}`))));
  }).on("error", reject);
});

const pascal = (n) => n.split(/[._]/).map((p) => p[0].toUpperCase() + p.slice(1)).join("");
const opts = { bannerComment: "", additionalProperties: false, format: false, strictIndexSignatures: true };

let out = "// GENERIERT aus GET /api/v1/operations (make bridge); nicht von Hand ändern.\n\n";
const map = [];
for (const op of operations) {
  const base = pascal(op.name);
  const strip = (s) => { const { $schema, title, ...rest } = s; return rest; };
  out += await compile({ ...strip(op.params_schema), title: `${base}Params` }, `${base}Params`, opts);
  out += await compile({ ...strip(op.result_schema), title: `${base}Result` }, `${base}Result`, opts);
  map.push(`  ${JSON.stringify(op.name)}: { params: ${base}Params; result: ${base}Result; mutating: ${op.mutating}; preview: ${op.preview_supported} };`);
}
out += `export interface OperationMap {\n${map.join("\n")}\n}\n\nexport type OperationName = keyof OperationMap;\n`;

await mkdir(root, { recursive: true });
await writeFile(join(root, "operations.ts"), out);
console.log(`bridge/generated/operations.ts: ${operations.length} Operationen`);
