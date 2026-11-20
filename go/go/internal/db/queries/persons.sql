-- name: UpsertPerson :exec
INSERT INTO persons (id, name, email) VALUES ($1, $2, $3)
ON CONFLICT (id) DO UPDATE SET name = EXCLUDED.name, email = EXCLUDED.email
WHERE persons.name IS DISTINCT FROM EXCLUDED.name OR persons.email IS DISTINCT FROM EXCLUDED.email;

-- name: GetPerson :one
SELECT * FROM persons WHERE id = $1;

-- name: PersonExists :one
SELECT EXISTS (SELECT 1 FROM persons WHERE id = $1);

-- name: SetChannels :exec
UPDATE persons SET channels = $2 WHERE id = $1;

-- name: AddPushSubscription :exec
INSERT INTO push_subscriptions (person_id, endpoint, p256dh, auth) VALUES ($1, $2, $3, $4)
ON CONFLICT (person_id, endpoint) DO UPDATE SET p256dh = EXCLUDED.p256dh, auth = EXCLUDED.auth;

-- name: ListPushSubscriptions :many
SELECT * FROM push_subscriptions WHERE person_id = $1 ORDER BY endpoint;
