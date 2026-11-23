"""EINE Beschreibung je Operation (S-1).

Eine Operation ist eine asynchrone Funktion `handler(ctx, params: P) -> R` mit Pydantic-Modellen P und R, dekoriert
mit `@operation(...)`. Aus Name, Beschreibung, Art und den Typen P/R entstehen automatisch: Validierung, Endpunkt,
`/api/v1/operations`, das KI-Werkzeugschema und (über das Schema) die Typen der Frontend-Brücke.
"""
import copy
import typing
from collections.abc import Awaitable, Callable
from dataclasses import dataclass
from typing import Any

from pydantic import BaseModel, ConfigDict

from chronos.core.context import Ctx


class Params(BaseModel):
    """Basis aller Parametermodelle: unbekannte Felder sind Fehler (additionalProperties: false)."""
    model_config = ConfigDict(extra="forbid")


class Result(BaseModel):
    pass


class Empty(Result):
    """Leeres Ergebnis `{}`."""


@dataclass(frozen=True)
class Operation:
    name: str
    description: str
    mutating: bool
    preview_supported: bool
    params: type[Params]
    result: type[Result]
    handler: Callable[[Ctx, Any], Awaitable[Any]]


OPERATIONS: dict[str, Operation] = {}


def operation(name: str, description: str, *, mutating: bool = False, preview: bool = False):
    def deco(fn):
        hints = typing.get_type_hints(fn)
        params, result = hints["p"], hints["return"]
        if name in OPERATIONS:
            raise RuntimeError(f"Operation doppelt beschrieben: {name}")
        OPERATIONS[name] = Operation(name, description, mutating, preview and mutating, params, result, fn)
        return fn
    return deco


# EIGENBAU:BEGIN JSON-Schema-Nachbearbeitung (Referenzen auflösen, title entfernen, optionale Parameter vereinfachen)
def _inline(node: Any, defs: dict[str, Any]) -> Any:
    """Löst $ref/$defs auf und entfernt das Schlüsselwort `title` (Lärm); Ergebnis ist in sich geschlossen."""
    if isinstance(node, dict):
        if "$ref" in node:
            return _inline(copy.deepcopy(defs[node["$ref"].split("/")[-1]]), defs)
        out = {}
        for k, v in node.items():
            if k in ("title", "$defs") and not isinstance(v, dict):
                continue  # Schlüsselwort title (Zeichenkette); ein Feld namens title wäre ein Objekt
            if k == "properties" and isinstance(v, dict):
                out[k] = {name: _inline(sub, defs) for name, sub in v.items()}  # Feldnamen bleiben unangetastet
            elif k != "$defs":
                out[k] = _inline(v, defs)
        return out
    if isinstance(node, list):
        return [_inline(v, defs) for v in node]
    return node


def _drop_null_options(schema: dict) -> dict:
    """Optionale Parameter: `X | None = None` wird zu `X` (nicht Pflicht), das Weglassen genügt."""
    for k, v in schema.get("properties", {}).items():
        opts = v.get("anyOf")
        if opts and len(opts) == 2 and {"type": "null"} in opts and k not in schema.get("required", []):
            inner = next(o for o in opts if o != {"type": "null"})
            v.pop("anyOf")
            v.update(inner)
            v.pop("default", None)
    return schema
# EIGENBAU:END


def params_schema(op: Operation) -> dict:
    s = op.params.model_json_schema(mode="validation")
    s = _drop_null_options(_inline(s, s.get("$defs", {})))
    s.setdefault("required", [])
    return s


def result_schema(op: Operation) -> dict:
    s = op.result.model_json_schema(mode="serialization")
    s = _inline(s, s.get("$defs", {}))
    s.setdefault("required", [])
    return s


def describe(op: Operation) -> dict:
    return {"name": op.name, "description": op.description, "mutating": op.mutating,
            "preview_supported": op.preview_supported, "params_schema": params_schema(op),
            "result_schema": result_schema(op)}


def tool_definition(op: Operation) -> dict:
    """Anthropic-Werkzeugdefinition: Name mit `_` statt `.`, input_schema = params_schema."""
    return {"name": op.name.replace(".", "_"), "description": op.description, "input_schema": params_schema(op)}
