-- name: InsertEvent :exec
INSERT INTO events (id, type, actor, operation, correlation_id, forced_channel) VALUES ($1, $2, $3, $4, $5, $6);

-- name: InsertRecipients :exec
INSERT INTO event_recipients (event_id, recipient) SELECT sqlc.arg(event_id)::uuid, unnest(sqlc.arg(recipients)::text[]);

-- name: GetEvent :one
SELECT * FROM events WHERE id = $1;

-- name: EventRecipients :many
SELECT recipient FROM event_recipients WHERE event_id = $1 ORDER BY recipient;

-- name: ResetClaims :exec
UPDATE event_recipients SET claimed_until = NULL WHERE state = 'pending';

-- name: ClaimRecipients :many
UPDATE event_recipients er SET claimed_until = now() + make_interval(secs => sqlc.arg(lease_secs)::int)
WHERE (er.event_id, er.recipient) IN (
    SELECT q.event_id, q.recipient FROM event_recipients q
    WHERE q.state = 'pending' AND (q.claimed_until IS NULL OR q.claimed_until < now())
    ORDER BY q.created_at, q.event_id, q.recipient
    LIMIT sqlc.arg(max_rows)::int
    FOR UPDATE SKIP LOCKED
)
RETURNING er.event_id, er.recipient;

-- name: FinishRecipient :exec
UPDATE event_recipients SET state = 'done', claimed_until = NULL WHERE event_id = $1 AND recipient = $2;

-- name: InsertDelivery :exec
INSERT INTO deliveries (event_id, recipient, channel, attempt, result, error, idempotency_key)
VALUES ($1, $2, $3, $4, $5, $6, $7);

-- name: DeliveriesFor :many
SELECT * FROM deliveries WHERE event_id = $1 AND recipient = $2 ORDER BY id;

-- name: ListDeliveries :many
SELECT d.id, d.event_id, e.type AS event_type, e.correlation_id, e.actor, d.recipient, d.channel, d.attempt,
       d.result, d.error, d.at, d.idempotency_key
FROM deliveries d JOIN events e ON e.id = d.event_id
WHERE (e.actor = sqlc.arg(person_id)::text OR d.recipient = sqlc.arg(person_id)::text)
  AND (sqlc.narg(event_id)::uuid IS NULL OR d.event_id = sqlc.narg(event_id)::uuid)
  AND (sqlc.narg(correlation_id)::text IS NULL OR e.correlation_id = sqlc.narg(correlation_id)::text)
ORDER BY d.id
LIMIT sqlc.arg(max_rows)::int;

-- name: InsertCost :exec
INSERT INTO costs (id, person_id, provider, trigger_kind, trigger_name, correlation_id, quantity, amount_micro_eur)
VALUES ($1, $2, $3, $4, $5, $6, $7, $8);

-- name: ListCosts :many
SELECT * FROM costs WHERE person_id = $1 ORDER BY seq DESC LIMIT $2;
