-- name: InsertHistory :exec
INSERT INTO history (id, actor, action, object_type, object_id, team_id, before, after, bundle_id, correlation_id, undo_of, event_id)
VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12);

-- name: GetHistory :one
SELECT * FROM history WHERE id = $1;

-- name: SetUndone :exec
UPDATE history SET undone = $2 WHERE id = $1;

-- name: ListHistory :many
WITH RECURSIVE up AS (
    SELECT t.id, t.parent_id FROM teams t JOIN team_members m ON m.team_id = t.id WHERE m.person_id = sqlc.arg(person_id)::text
    UNION
    SELECT p.id, p.parent_id FROM teams p JOIN up ON p.id = up.parent_id
)
SELECT h.* FROM history h
WHERE h.team_id IN (SELECT id FROM up)
  AND (sqlc.narg(object_id)::uuid IS NULL OR h.object_id = sqlc.narg(object_id)::uuid)
ORDER BY h.seq DESC
LIMIT sqlc.arg(max_rows)::int;
