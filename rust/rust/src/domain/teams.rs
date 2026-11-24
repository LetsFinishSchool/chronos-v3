use crate::core::ctx::Ctx;
use crate::core::ops::Operation;
use crate::error::{ApiError, ApiResult};
use crate::register;
use serde::{Deserialize, Serialize};
use sqlx::PgConnection;
use utoipa::ToSchema;
use uuid::Uuid;

// ---------------------------------------------------------------- Berechtigung (EINE Stelle)

/// Ist `person` effektives Mitglied von `team` (direkt oder in einem Unter-Team)? 404 wenn das Team fehlt, 403 sonst.
pub async fn require_member(conn: &mut PgConnection, team: Uuid, person: &str) -> ApiResult<()> {
    let exists: Option<(Uuid,)> = sqlx::query_as("SELECT id FROM teams WHERE id = $1").bind(team).fetch_optional(&mut *conn).await?;
    if exists.is_none() {
        return Err(ApiError::not_found("Team nicht gefunden"));
    }
    let (member,): (bool,) = sqlx::query_as(
        "WITH RECURSIVE sub AS (
           SELECT id FROM teams WHERE id = $1
           UNION ALL SELECT t.id FROM teams t JOIN sub ON t.parent_id = sub.id)
         SELECT EXISTS (SELECT 1 FROM team_members m JOIN sub ON m.team_id = sub.id WHERE m.person_id = $2)",
    )
    .bind(team)
    .bind(person)
    .fetch_one(&mut *conn)
    .await?;
    if member { Ok(()) } else { Err(ApiError::forbidden("Kein Mitglied des Teams")) }
}

/// Effektive Mitglieder (Person-IDs, sortiert) eines Teams inklusive aller Unter-Teams.
pub async fn effective_member_ids(conn: &mut PgConnection, team: Uuid) -> ApiResult<Vec<String>> {
    let rows: Vec<(String,)> = sqlx::query_as(
        "WITH RECURSIVE sub AS (
           SELECT id FROM teams WHERE id = $1
           UNION ALL SELECT t.id FROM teams t JOIN sub ON t.parent_id = sub.id)
         SELECT DISTINCT m.person_id FROM team_members m JOIN sub ON m.team_id = sub.id ORDER BY 1",
    )
    .bind(team)
    .fetch_all(&mut *conn)
    .await?;
    Ok(rows.into_iter().map(|r| r.0).collect())
}

/// Empfänger eines Ereignisses zu einem Team: alle effektiven Mitglieder außer dem Aufrufer.
pub async fn recipients_except(conn: &mut PgConnection, team: Uuid, caller: &str) -> ApiResult<Vec<String>> {
    Ok(effective_member_ids(conn, team).await?.into_iter().filter(|p| p != caller).collect())
}

// ---------------------------------------------------------------- team.create

#[derive(Deserialize, ToSchema)]
pub struct TeamCreateParams {
    #[schema(min_length = 1, max_length = 100)]
    pub name: String,
    pub parent_id: Option<Uuid>,
}
#[derive(Serialize, ToSchema)]
pub struct TeamCreateResult {
    pub team_id: Uuid,
}
pub struct TeamCreate;
impl Operation for TeamCreate {
    type Params = TeamCreateParams;
    type Result = TeamCreateResult;
    const NAME: &'static str = "team.create";
    const DESCRIPTION: &'static str = "Legt ein Team an (optional unter einem Eltern-Team); der Aufrufer wird direktes Mitglied.";
    const MUTATING: bool = true;
    async fn run(ctx: Ctx, p: Self::Params) -> ApiResult<Self::Result> {
        let mut tx = ctx.begin().await?;
        if let Some(parent) = p.parent_id {
            require_member(&mut tx, parent, &ctx.caller.id).await?;
        }
        let id = Uuid::new_v4();
        sqlx::query("INSERT INTO teams (id, name, parent_id) VALUES ($1,$2,$3)")
            .bind(id).bind(&p.name).bind(p.parent_id).execute(&mut *tx).await?;
        sqlx::query("INSERT INTO team_members (team_id, person_id) VALUES ($1,$2)")
            .bind(id).bind(&ctx.caller.id).execute(&mut *tx).await?;
        tx.commit().await?;
        Ok(TeamCreateResult { team_id: id })
    }
}
register!(TeamCreate);

// ---------------------------------------------------------------- team.add_member

#[derive(Deserialize, ToSchema)]
pub struct AddMemberParams {
    pub team_id: Uuid,
    #[schema(min_length = 1)]
    pub person_id: String,
}
#[derive(Serialize, ToSchema)]
pub struct Empty {}
pub struct TeamAddMember;
impl Operation for TeamAddMember {
    type Params = AddMemberParams;
    type Result = Empty;
    const NAME: &'static str = "team.add_member";
    const DESCRIPTION: &'static str = "Fügt eine bekannte Person (Keycloak-sub) einem Team hinzu; doppeltes Hinzufügen bleibt ohne Wirkung.";
    const MUTATING: bool = true;
    async fn run(ctx: Ctx, p: Self::Params) -> ApiResult<Empty> {
        let mut c = ctx.pool.acquire().await?;
        require_member(&mut c, p.team_id, &ctx.caller.id).await?;
        let known: Option<(String,)> = sqlx::query_as("SELECT id FROM persons WHERE id = $1").bind(&p.person_id).fetch_optional(&mut *c).await?;
        if known.is_none() {
            return Err(ApiError::not_found("Person unbekannt"));
        }
        sqlx::query("INSERT INTO team_members (team_id, person_id) VALUES ($1,$2) ON CONFLICT DO NOTHING")
            .bind(p.team_id).bind(&p.person_id).execute(&mut *c).await?;
        Ok(Empty {})
    }
}
register!(TeamAddMember);

// ---------------------------------------------------------------- team.effective_members

#[derive(Deserialize, ToSchema)]
pub struct TeamIdParams {
    pub team_id: Uuid,
}
#[derive(Serialize, ToSchema)]
pub struct Member {
    pub person_id: String,
    pub name: String,
}
#[derive(Serialize, ToSchema)]
pub struct MembersResult {
    pub members: Vec<Member>,
}
pub struct TeamEffectiveMembers;
impl Operation for TeamEffectiveMembers {
    type Params = TeamIdParams;
    type Result = MembersResult;
    const NAME: &'static str = "team.effective_members";
    const DESCRIPTION: &'static str = "Liefert die direkten Mitglieder eines Teams und aller Unter-Teams ohne Duplikate, nach person_id sortiert.";
    const MUTATING: bool = false;
    async fn run(ctx: Ctx, p: Self::Params) -> ApiResult<MembersResult> {
        let mut c = ctx.pool.acquire().await?;
        require_member(&mut c, p.team_id, &ctx.caller.id).await?;
        let ids = effective_member_ids(&mut c, p.team_id).await?;
        let rows: Vec<(String, String)> = sqlx::query_as("SELECT id, name FROM persons WHERE id = ANY($1) ORDER BY id")
            .bind(&ids).fetch_all(&mut *c).await?;
        Ok(MembersResult { members: rows.into_iter().map(|(person_id, name)| Member { person_id, name }).collect() })
    }
}
register!(TeamEffectiveMembers);

// ---------------------------------------------------------------- team.effective_teams

#[derive(Deserialize, ToSchema)]
pub struct EffectiveTeamsParams {
    pub person_id: Option<String>,
}
#[derive(Serialize, ToSchema)]
pub struct TeamInfo {
    pub team_id: Uuid,
    pub name: String,
    pub parent_id: Option<Uuid>,
}
#[derive(Serialize, ToSchema)]
pub struct EffectiveTeamsResult {
    pub teams: Vec<TeamInfo>,
}
pub struct TeamEffectiveTeams;
impl Operation for TeamEffectiveTeams {
    type Params = EffectiveTeamsParams;
    type Result = EffectiveTeamsResult;
    const NAME: &'static str = "team.effective_teams";
    const DESCRIPTION: &'static str = "Liefert alle Teams mit direkter Mitgliedschaft der Person und alle übergeordneten Teams (Standard: Aufrufer).";
    const MUTATING: bool = false;
    async fn run(ctx: Ctx, p: Self::Params) -> ApiResult<EffectiveTeamsResult> {
        if let Some(other) = &p.person_id {
            if *other != ctx.caller.id {
                return Err(ApiError::forbidden("Nur die eigenen Teams sind abrufbar"));
            }
        }
        let mut c = ctx.pool.acquire().await?;
        let rows = effective_teams(&mut c, &ctx.caller.id).await?;
        Ok(EffectiveTeamsResult { teams: rows.into_iter().map(|(team_id, name, parent_id)| TeamInfo { team_id, name, parent_id }).collect() })
    }
}
register!(TeamEffectiveTeams);

pub async fn effective_teams(conn: &mut PgConnection, person: &str) -> ApiResult<Vec<(Uuid, String, Option<Uuid>)>> {
    Ok(sqlx::query_as(
        "WITH RECURSIVE up AS (
           SELECT t.id, t.name, t.parent_id FROM teams t JOIN team_members m ON m.team_id = t.id WHERE m.person_id = $1
           UNION SELECT t.id, t.name, t.parent_id FROM teams t JOIN up ON up.parent_id = t.id)
         SELECT id, name, parent_id FROM up ORDER BY name, id",
    )
    .bind(person)
    .fetch_all(&mut *conn)
    .await?)
}
