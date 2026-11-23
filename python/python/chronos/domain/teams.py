"""Fachbereich Teams: Team-Baum, Mitglieder, effektive Mitgliedschaft."""
import uuid
from uuid import UUID

from pydantic import Field
from sqlalchemy import text

from chronos.core import access
from chronos.core.context import Ctx
from chronos.core.errors import NotFound, Forbidden
from chronos.ops.registry import Empty, Params, Result, operation


class TeamCreateParams(Params):
    name: str = Field(min_length=1, max_length=100)
    parent_id: UUID | None = None


class TeamCreateResult(Result):
    team_id: str


@operation("team.create", "Legt ein Team an; der Aufrufer wird direktes Mitglied. Mit parent_id entsteht ein "
           "Unter-Team (der Aufrufer muss Mitglied des Eltern-Teams sein).", mutating=True)
async def team_create(ctx: Ctx, p: TeamCreateParams) -> TeamCreateResult:
    if p.parent_id is not None:
        await access.require_member(ctx, str(p.parent_id))
    team_id = str(uuid.uuid4())
    await ctx.db.execute(text("INSERT INTO team (id, name, parent_id) VALUES (:id, :name, :parent)"),
                         {"id": team_id, "name": p.name, "parent": str(p.parent_id) if p.parent_id else None})
    await ctx.db.execute(text("INSERT INTO team_member (team_id, person_id) VALUES (:t, :p)"),
                         {"t": team_id, "p": ctx.person.id})
    ctx.affected.append({"type": "team", "id": team_id, "change": "team.create"})
    return TeamCreateResult(team_id=team_id)


class TeamAddMemberParams(Params):
    team_id: UUID
    person_id: str = Field(min_length=1, description="Keycloak-sub der Person")


@operation("team.add_member", "Fügt eine bereits angemeldete Person als direktes Mitglied zu einem Team hinzu "
           "(doppeltes Hinzufügen ohne Wirkung).", mutating=True)
async def team_add_member(ctx: Ctx, p: TeamAddMemberParams) -> Empty:
    await access.require_member(ctx, str(p.team_id))
    known = (await ctx.db.execute(text("SELECT 1 FROM person WHERE id = :p"), {"p": p.person_id})).first()
    if known is None:
        raise NotFound("Person unbekannt")
    await ctx.db.execute(text("INSERT INTO team_member (team_id, person_id) VALUES (:t, :p) ON CONFLICT DO NOTHING"),
                         {"t": str(p.team_id), "p": p.person_id})
    ctx.affected.append({"type": "team", "id": str(p.team_id), "change": "team.add_member"})
    return Empty()


class Member(Result):
    person_id: str
    name: str


class EffectiveMembersParams(Params):
    team_id: UUID


class EffectiveMembersResult(Result):
    members: list[Member]


@operation("team.effective_members", "Liefert die direkten Mitglieder eines Teams und aller Unter-Teams "
           "(beliebig tief), ohne Duplikate, nach person_id sortiert.")
async def team_effective_members(ctx: Ctx, p: EffectiveMembersParams) -> EffectiveMembersResult:
    await access.require_member(ctx, str(p.team_id))
    return EffectiveMembersResult(
        members=[Member(person_id=i, name=n) for i, n in await access.effective_members(ctx, str(p.team_id))])


class EffectiveTeamsParams(Params):
    person_id: str | None = None


class TeamRef(Result):
    team_id: str
    name: str
    parent_id: str | None


class EffectiveTeamsResult(Result):
    teams: list[TeamRef]


@operation("team.effective_teams", "Liefert alle Teams mit direkter Mitgliedschaft der Person und alle "
           "übergeordneten Teams (Standard: der Aufrufer; andere Personen nicht erlaubt).")
async def team_effective_teams(ctx: Ctx, p: EffectiveTeamsParams) -> EffectiveTeamsResult:
    person_id = p.person_id or ctx.person.id
    if person_id != ctx.person.id:
        raise Forbidden("nur die eigenen Teams abrufbar")
    r = await ctx.db.execute(
        text(access.EFFECTIVE_TEAMS_CTE + "SELECT id::text AS id, name, parent_id::text AS parent_id FROM eff "
                                          "ORDER BY name COLLATE \"C\", id::text"), {"person_id": person_id})
    return EffectiveTeamsResult(teams=[TeamRef(team_id=x.id, name=x.name, parent_id=x.parent_id) for x in r])
