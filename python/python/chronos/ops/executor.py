"""Führt eine Operation aus: Validierung, EINE Transaktion, Vorschau (Rollback), Ergebnis."""
from pydantic import ValidationError

from chronos import db
from chronos.core.context import Ctx, Person
from chronos.core.errors import ValidationFailed
from chronos.ops.registry import Operation


def _summarize(e: ValidationError) -> str:
    return "; ".join(f"{'.'.join(str(x) for x in err['loc']) or 'params'}: {err['msg']}" for err in e.errors()[:5])


async def execute(op: Operation, raw_params: dict, *, preview: bool, person: Person, correlation_id: str,
                  fault: str | None) -> dict:
    try:
        params = op.params.model_validate(raw_params)
    except ValidationError as e:
        raise ValidationFailed(_summarize(e)) from e
    if preview and op.mutating and not op.preview_supported:
        raise ValidationFailed(f"Operation {op.name} unterstützt keine Vorschau")
    dry_run = preview and op.mutating
    async with db.session() as s:
        ctx = Ctx(db=s, person=person, correlation_id=correlation_id, operation=op.name, preview=dry_run, fault=fault)
        async with s.begin() as tx:
            result = await op.handler(ctx, params)
            if dry_run:
                # Vorschau: dieselbe Logik, aber die Transaktion wird verworfen -> keine Schreibwirkung.
                await tx.rollback()
                return {"preview": {"count": len(ctx.affected), "affected": ctx.affected}}
    return {"result": result.model_dump(mode="json")}
