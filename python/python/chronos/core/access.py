"""Berechtigung an EINER Stelle: effektive Mitgliedschaft (direkt oder über Unter-Teams)."""
from sqlalchemy import text

from chronos.core.context import Ctx
from chronos.core.errors import Forbidden, NotFound

_SUBTREE = """
WITH RECURSIVE sub(id) AS (
    SELECT id FROM team WHERE id = :team_id
    UNION
    SELECT c.id FROM team c JOIN sub ON c.parent_id = sub.id
)
"""

# Alle Teams, in denen eine Person effektiv Mitglied ist: direkte Teams und alle übergeordneten.
EFFECTIVE_TEAMS_CTE = """
WITH RECURSIVE eff(id, name, parent_id) AS (
    SELECT t.id, t.name, t.parent_id FROM team t JOIN team_member m ON m.team_id = t.id WHERE m.person_id = :person_id
    UNION
    SELECT p.id, p.name, p.parent_id FROM team p JOIN eff ON eff.parent_id = p.id
)
"""


async def team_exists(ctx: Ctx, team_id: str) -> bool:
    r = await ctx.db.execute(text("SELECT 1 FROM team WHERE id = :t"), {"t": team_id})
    return r.first() is not None


async def is_effective_member(ctx: Ctx, team_id: str, person_id: str) -> bool:
    r = await ctx.db.execute(
        text(_SUBTREE + "SELECT EXISTS(SELECT 1 FROM team_member m JOIN sub ON m.team_id = sub.id "
                        "WHERE m.person_id = :p)"),
        {"team_id": team_id, "p": person_id},
    )
    return bool(r.scalar_one())


async def require_member(ctx: Ctx, team_id: str) -> None:
    """404, wenn das Team fehlt; 403, wenn der Aufrufer kein effektives Mitglied ist."""
    if not await team_exists(ctx, team_id):
        raise NotFound("Team nicht gefunden")
    if not await is_effective_member(ctx, team_id, ctx.person.id):
        raise Forbidden("kein Mitglied des Teams")


async def effective_members(ctx: Ctx, team_id: str) -> list[tuple[str, str]]:
    r = await ctx.db.execute(
        text(_SUBTREE + "SELECT DISTINCT p.id, p.name FROM team_member m JOIN sub ON m.team_id = sub.id "
                        "JOIN person p ON p.id = m.person_id ORDER BY p.id"),
        {"team_id": team_id},
    )
    return [(row.id, row.name) for row in r]


async def recipients_except_actor(ctx: Ctx, team_id: str) -> list[str]:
    return [pid for pid, _ in await effective_members(ctx, team_id) if pid != ctx.person.id]
