-- name: CreateAppointment :exec
INSERT INTO appointments (id, team_id, title, starts_at, ends_at, timezone, status)
VALUES ($1, $2, $3, $4, $5, $6, $7);

-- name: GetAppointment :one
SELECT * FROM appointments WHERE id = $1;

-- name: ListAppointments :many
SELECT * FROM appointments WHERE team_id = $1 AND status <> 'gelöscht' ORDER BY starts_at, id;

-- name: RestoreAppointment :exec
UPDATE appointments SET title = $2, starts_at = $3, ends_at = $4, timezone = $5, status = $6 WHERE id = $1;

-- name: CreateSeries :exec
INSERT INTO series (id, team_id, title, rrule, dtstart, timezone, duration_minutes, exdates)
VALUES ($1, $2, $3, $4, $5, $6, $7, $8);

-- name: GetSeries :one
SELECT * FROM series WHERE id = $1;
