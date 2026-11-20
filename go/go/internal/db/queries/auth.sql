-- name: InsertAuthFlow :exec
INSERT INTO auth_flows (state, verifier) VALUES ($1, $2);

-- name: TakeAuthFlow :one
DELETE FROM auth_flows WHERE state = $1 AND created_at > now() - interval '10 minutes' RETURNING verifier;

-- name: CreateSession :exec
INSERT INTO sessions (id, person_id) VALUES ($1, $2);

-- name: SessionPerson :one
SELECT p.* FROM sessions s JOIN persons p ON p.id = s.person_id WHERE s.id = $1;

-- name: DeleteSession :exec
DELETE FROM sessions WHERE id = $1;
