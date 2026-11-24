#!/usr/bin/env python3
"""Frontend-Brücke (S-10): erzeugt TypeScript-Typen aus GET $BASE_URL/api/v1/operations.

Nur Standardbibliothek plus `json-schema-to-typescript` (npx). Von Hand gepflegt wird nichts: je Operation entstehen
`<Name>Params` und `<Name>Result` sowie die Abbildung `Operations` (Operationsname -> {params, result}).
"""
import json
import os
import re
import shutil
import subprocess
import sys
import urllib.request
from pathlib import Path

BASE_URL = os.environ.get("BASE_URL", "http://localhost:8080").rstrip("/")
HERE = Path(__file__).resolve().parent
OUT = HERE / "generated"
JSON2TS = os.environ.get("JSON2TS", "npx --yes -p json-schema-to-typescript@15.0.4 json2ts").split()


def pascal(name: str) -> str:
    return "".join(p.capitalize() for p in re.split(r"[._]", name))


def main() -> int:
    with urllib.request.urlopen(f"{BASE_URL}/api/v1/operations", timeout=30) as r:
        ops = json.load(r)["operations"]
    shutil.rmtree(OUT, ignore_errors=True)
    schemas, types = OUT / "schemas", OUT / "types"
    schemas.mkdir(parents=True)
    names = []
    for op in ops:
        base = pascal(op["name"])
        for kind, key in (("Params", "params_schema"), ("Result", "result_schema")):
            schema = {"title": base + kind, **op[key]}
            (schemas / f"{base}{kind}.json").write_text(json.dumps(schema), encoding="utf-8")
        names.append((op["name"], base))
    subprocess.run([*JSON2TS, "-i", str(schemas), "-o", str(types), "--no-bannerComment"], check=True)
    for f in types.glob("*.d.ts"):
        f.rename(f.with_name(f.name[: -len(".d.ts")] + ".ts"))
    lines = ["// Erzeugt von bridge/generate.py aus /api/v1/operations. Nicht von Hand ändern.", ""]
    for _, base in names:
        lines.append(f'import type {{ {base}Params }} from "./types/{base}Params";')
        lines.append(f'import type {{ {base}Result }} from "./types/{base}Result";')
    lines += ["", "export interface Operations {"]
    for name, base in names:
        lines.append(f'  "{name}": {{ params: {base}Params; result: {base}Result }};')
    lines += ["}", ""]
    (OUT / "operations.ts").write_text("\n".join(lines), encoding="utf-8")
    print(f"{len(names)} Operationen -> {OUT}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
