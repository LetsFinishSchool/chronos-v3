-- name: CreateTeam :exec
INSERT INTO teams (id, name, parent_id) VALUES ($1, $2, $3);

-- name: GetTeam :one
SELECT * FROM teams WHERE id = $1;

-- name: AddTeamMember :exec
INSERT INTO team_members (team_id, person_id) VALUES ($1, $2) ON CONFLICT DO NOTHING;

-- name: IsEffectiveMember :one
WITH RECURSIVE sub AS (
    SELECT t.id FROM teams t WHERE t.id = $1
    UNION ALL
    SELECT c.id FROM teams c JOIN sub ON c.parent_id = sub.id
)
SELECT EXISTS (SELECT 1 FROM team_members m JOIN sub ON m.team_id = sub.id WHERE m.person_id = $2);

-- name: EffectiveMembers :many
WITH RECURSIVE sub AS (
    SELECT t.id FROM teams t WHERE t.id = $1
    UNION ALL
    SELECT c.id FROM teams c JOIN sub ON c.parent_id = sub.id
)
SELECT DISTINCT p.id AS person_id, p.name FROM team_members m
JOIN sub ON m.team_id = sub.id JOIN persons p ON p.id = m.person_id
ORDER BY p.id;

-- name: EffectiveTeams :many
WITH RECURSIVE up AS (
    SELECT t.id, t.name, t.parent_id FROM teams t JOIN team_members m ON m.team_id = t.id WHERE m.person_id = $1
    UNION
    SELECT p.id, p.name, p.parent_id FROM teams p JOIN up ON p.id = up.parent_id
)
SELECT id, name, parent_id FROM up ORDER BY name, id;
