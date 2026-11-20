#!/usr/bin/env python3
"""Erzeugt TypeScript-Typen aus GET /api/v1/operations (nur für die Referenzattrappe; die Kandidaten bringen ihre eigene Brücke mit)."""
import json, os, sys, urllib.request

base = os.environ.get("BASE_URL", "http://localhost:8080")
ops = json.load(urllib.request.urlopen(base + "/api/v1/operations"))["operations"]

def ts(s):
    t = s.get("type")
    if "enum" in s:
        return " | ".join(json.dumps(x) for x in s["enum"])
    if t == "string": return "string"
    if t in ("integer", "number"): return "number"
    if t == "boolean": return "boolean"
    if t == "array": return f"Array<{ts(s['items'])}>"
    if t == "object":
        props = s.get("properties")
        if not props: return "Record<string, unknown>"
        req = set(s.get("required", []))
        return "{ " + "; ".join(f"{k}{'' if k in req else '?'}: {ts(v)}" for k, v in props.items()) + " }"
    return "unknown"

out = ["// GENERIERT aus /api/v1/operations. Nicht von Hand ändern.", "export interface OperationMap {"]
for o in ops:
    out.append(f"  {json.dumps(o['name'])}: {{ params: {ts(o['params_schema'])}; result: {ts(o['result_schema'])} }};")
out.append("}")
os.makedirs("bridge/generated", exist_ok=True)
open("bridge/generated/operations.ts", "w").write("\n".join(out) + "\n")
