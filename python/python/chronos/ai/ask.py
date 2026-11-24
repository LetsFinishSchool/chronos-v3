"""KI-Anbindung: ai.ask ruft die Anthropic-Messages-API mit den Werkzeugen aus der Operationsbeschreibung."""
from datetime import UTC, datetime
from typing import Any
from uuid import UUID

import anthropic
from pydantic import Field
from sqlalchemy import text

from chronos.config import settings
from chronos.core import access
from chronos.core.context import Ctx
from chronos.core.errors import ProviderError
from chronos.logging import log
from chronos.ops.registry import OPERATIONS, Params, Result, operation, tool_definition

_client: anthropic.AsyncAnthropic | None = None


def _get_client() -> anthropic.AsyncAnthropic:
    global _client
    if _client is None:
        _client = anthropic.AsyncAnthropic(base_url=settings.anthropic_base_url, api_key=settings.anthropic_api_key,
                                           timeout=60.0, max_retries=0)
    return _client


class AskParams(Params):
    prompt: str = Field(min_length=1, max_length=8000)
    team_id: UUID | None = Field(default=None, description="Team, auf das sich die Frage bezieht")


class ProposedCall(Result):
    name: str
    input: dict[str, Any]


class Usage(Result):
    input_tokens: int
    output_tokens: int


class AskResult(Result):
    text: str
    proposed_calls: list[ProposedCall]
    usage: Usage


def _system(ctx: Ctx, team_id: str | None) -> str:
    return (
        "Du bist der Assistent von Chronos, einer Terminverwaltung. Nutze die bereitgestellten Werkzeuge, um "
        "gewünschte Aktionen vorzuschlagen; sie werden nicht automatisch ausgeführt. Zeitangaben für Parameter "
        "wie starts_at und ends_at gibst du in UTC mit Endung Z an (rechne Ortszeiten selbst um). "
        f"Heute ist {datetime.now(UTC):%Y-%m-%d}."
        + (f" Der Nutzer arbeitet im Team mit der ID {team_id}." if team_id else "")
    )


@operation("ai.ask", "Fragt die KI; sie kann Aufrufe beliebiger Operationen vorschlagen, führt sie aber nicht aus. "
           "Erfasst einen Kostenposten.")
async def ai_ask(ctx: Ctx, p: AskParams) -> AskResult:
    team_id = str(p.team_id) if p.team_id else None
    if team_id:
        await access.require_member(ctx, team_id)
    tools = [tool_definition(op) for op in OPERATIONS.values()]
    try:
        msg = await _get_client().messages.create(
            model=settings.anthropic_model, max_tokens=1024, system=_system(ctx, team_id), tools=tools,
            messages=[{"role": "user", "content": p.prompt}])
    except anthropic.APIError as e:
        log.warning("KI-Anbieterfehler: %s", type(e).__name__)
        raise ProviderError(f"KI-Anbieter: {type(e).__name__}") from e
    by_tool = {op.name.replace(".", "_"): op.name for op in OPERATIONS.values()}
    texts = [b.text for b in msg.content if b.type == "text"]
    calls = [ProposedCall(name=by_tool.get(b.name, b.name), input=b.input) for b in msg.content if b.type == "tool_use"]
    tin, tout = msg.usage.input_tokens, msg.usage.output_tokens
    amount = round((tin * settings.ai_price_in + tout * settings.ai_price_out) / 1_000_000)
    await ctx.db.execute(
        text("INSERT INTO cost (person_id, provider, trigger_kind, trigger_name, correlation_id, quantity, "
             "amount_micro_eur) VALUES (:p, 'anthropic', 'operation', :op, :corr, CAST(:q AS jsonb), :amt)"),
        {"p": ctx.person.id, "op": ctx.operation, "corr": ctx.correlation_id,
         "q": f'{{"input_tokens": {tin}, "output_tokens": {tout}}}', "amt": amount})
    return AskResult(text="\n".join(texts), proposed_calls=calls, usage=Usage(input_tokens=tin, output_tokens=tout))
