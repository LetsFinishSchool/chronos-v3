-- Minimalstand des Operationsrahmens (ADR-005, K-003, K-004).

-- Kennung und Art jedes Akteurs; Keycloak-Anbindung und Profil erweitern die Tabelle später.
CREATE TABLE person (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    kind text NOT NULL CHECK (kind IN ('person', 'guest')),
    created_at timestamptz NOT NULL DEFAULT now()
);

-- Ein Eintrag je geänderter Objektzustand. `before` hält den Zustand vor der Änderung,
-- damit der volle Verlaufsmechanismus (#34) darauf aufbauen kann.
CREATE TABLE history (
    id bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    actor_id uuid NOT NULL REFERENCES person (id),
    occurred_at timestamptz NOT NULL DEFAULT now(),
    action text NOT NULL,
    object_kind text NOT NULL,
    object_id uuid NOT NULL,
    before jsonb,
    correlation_id uuid NOT NULL,
    bundle_id uuid
);

-- Ereignisse entstehen in derselben Transaktion wie die Fachänderung; der Worker
-- arbeitet sie später ab (K-003).
CREATE TABLE outbox (
    id bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    event text NOT NULL,
    payload jsonb NOT NULL,
    actor_id uuid NOT NULL REFERENCES person (id),
    correlation_id uuid NOT NULL,
    created_at timestamptz NOT NULL DEFAULT now(),
    processed_at timestamptz
);

CREATE INDEX outbox_pending ON outbox (id) WHERE processed_at IS NULL;
