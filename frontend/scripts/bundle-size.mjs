import { appendFileSync, readdirSync, readFileSync } from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";
import { gzipSync } from "node:zlib";

const buildDir = fileURLToPath(new URL("../app/build", import.meta.url));

function* walk(dir) {
  for (const entry of readdirSync(dir, { withFileTypes: true })) {
    const full = path.join(dir, entry.name);
    if (entry.isDirectory()) yield* walk(full);
    else yield full;
  }
}

const files = [...walk(buildDir)]
  .filter((file) => /\.(js|css)$/.test(file))
  .map((file) => ({
    name: path.relative(buildDir, file),
    bytes: gzipSync(readFileSync(file)).length,
  }))
  .sort((a, b) => b.bytes - a.bytes || a.name.localeCompare(b.name));

const kb = (bytes) => (bytes / 1024).toFixed(2);
const total = files.reduce((sum, file) => sum + file.bytes, 0);

const lines = [
  "### Bundle-Größe (gzip, JS und CSS)",
  "",
  "| Datei | KB |",
  "|---|---:|",
  ...files.map((file) => `| \`${file.name}\` | ${kb(file.bytes)} |`),
  `| **Gesamt** | **${kb(total)}** |`,
  "",
];
const output = lines.join("\n");

console.log(output);
if (process.env.GITHUB_STEP_SUMMARY) appendFileSync(process.env.GITHUB_STEP_SUMMARY, output);
