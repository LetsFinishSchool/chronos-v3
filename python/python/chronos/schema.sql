-- Chronos-Spike: Schema (idempotent, wird beim Start des Web unter Advisory-Lock ausgeführt)
CREATE TABLE IF NOT EXISTS person (
    id          text PRIMARY KEY,
    name        text NOT NULL,
    email       text NOT NULL,
    channels    jsonb NOT NULL DEFAULT '["webpush","email"]',
    created_at  timestamptz NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS push_subscription (
    id          bigserial PRIMARY KEY,
    person_id   text NOT NULL REFERENCES person(id),
    endpoint    text NOT NULL,
    p256dh      text NOT NULL,
    auth        text NOT NULL,
    UNIQUE (person_id, endpoint)
);

CREATE TABLE IF NOT EXISTS team (
    id          uuid PRIMARY KEY,
    name        text NOT NULL,
    parent_id   uuid REFERENCES team(id)
);
CREATE INDEX IF NOT EXISTS team_parent_idx ON team(parent_id);

CREATE TABLE IF NOT EXISTS team_member (
    team_id     uuid NOT NULL REFERENCES team(id),
    person_id   text NOT NULL REFERENCES person(id),
    PRIMARY KEY (team_id, person_id)
);
CREATE INDEX IF NOT EXISTS team_member_person_idx ON team_member(person_id);

CREATE TABLE IF NOT EXISTS appointment (
    id          uuid PRIMARY KEY,
    team_id     uuid NOT NULL REFERENCES team(id),
    title       text NOT NULL,
    starts_at   timestamptz NOT NULL,
    ends_at     timestamptz NOT NULL,
    timezone    text NOT NULL,
    status      text NOT NULL
);
CREATE INDEX IF NOT EXISTS appointment_team_idx ON appointment(team_id, starts_at);

CREATE TABLE IF NOT EXISTS series (
    id               uuid PRIMARY KEY,
    team_id          uuid NOT NULL REFERENCES team(id),
    title            text NOT NULL,
    rrule            text NOT NULL,
    dtstart          timestamp NOT NULL,
    timezone         text NOT NULL,
    duration_minutes integer NOT NULL,
    exdates          jsonb NOT NULL DEFAULT '[]',
    status           text NOT NULL DEFAULT 'aktiv'
);

CREATE TABLE IF NOT EXISTS event (
    id              uuid PRIMARY KEY,
    seq             bigserial,
    type            text NOT NULL,
    trigger_kind    text NOT NULL,
    actor           text NOT NULL,
    operation       text NOT NULL,
    correlation_id  text NOT NULL,
    recipients      jsonb NOT NULL,
    payload         jsonb NOT NULL DEFAULT '{}',
    created_at      timestamptz NOT NULL DEFAULT now()
);
CREATE INDEX IF NOT EXISTS event_corr_idx ON event(correlation_id);
CREATE INDEX IF NOT EXISTS event_actor_idx ON event(actor);

-- Arbeitsliste des Workers: je (Ereignis, Empfänger) eine Zeile mit Fortschritt (Kanalindex, Versuch).
CREATE TABLE IF NOT EXISTS delivery_task (
    event_id        uuid NOT NULL REFERENCES event(id),
    recipient       text NOT NULL,
    status          text NOT NULL DEFAULT 'pending',
    channel_idx     integer NOT NULL DEFAULT 0,
    attempt         integer NOT NULL DEFAULT 0,
    next_at         timestamptz NOT NULL DEFAULT now(),
    lease_until     timestamptz,
    PRIMARY KEY (event_id, recipient)
);
CREATE INDEX IF NOT EXISTS delivery_task_due_idx ON delivery_task(next_at) WHERE status = 'pending';

CREATE TABLE IF NOT EXISTS delivery (
    id               bigserial PRIMARY KEY,
    event_id         uuid NOT NULL REFERENCES event(id),
    recipient        text NOT NULL,
    channel          text NOT NULL,
    attempt          integer NOT NULL,
    result           text NOT NULL,
    error            text,
    at               timestamptz NOT NULL DEFAULT now(),
    idempotency_key  text NOT NULL,
    correlation_id   text NOT NULL
);
CREATE INDEX IF NOT EXISTS delivery_event_idx ON delivery(event_id);
CREATE INDEX IF NOT EXISTS delivery_recipient_idx ON delivery(recipient);
CREATE INDEX IF NOT EXISTS delivery_corr_idx ON delivery(correlation_id);

CREATE TABLE IF NOT EXISTS history (
    id              uuid PRIMARY KEY,
    seq             bigserial,
    at              timestamptz NOT NULL DEFAULT now(),
    actor           text NOT NULL,
    action          text NOT NULL,
    object_type     text NOT NULL,
    object_id       uuid NOT NULL,
    team_id         uuid NOT NULL,
    before          jsonb,
    after           jsonb,
    bundle_id       uuid NOT NULL,
    correlation_id  text NOT NULL,
    undone          boolean NOT NULL DEFAULT false,
    undo_of         uuid,
    event_id        uuid
);
CREATE INDEX IF NOT EXISTS history_object_idx ON history(object_id, seq DESC);
CREATE INDEX IF NOT EXISTS history_team_idx ON history(team_id, seq DESC);

CREATE TABLE IF NOT EXISTS cost (
    id              bigserial PRIMARY KEY,
    at              timestamptz NOT NULL DEFAULT now(),
    person_id       text NOT NULL,
    provider        text NOT NULL,
    trigger_kind    text NOT NULL,
    trigger_name    text NOT NULL,
    correlation_id  text NOT NULL,
    quantity        jsonb NOT NULL,
    amount_micro_eur bigint NOT NULL
);
CREATE INDEX IF NOT EXISTS cost_person_idx ON cost(person_id, id DESC);

CREATE TABLE IF NOT EXISTS session (
    id          text PRIMARY KEY,
    person_id   text NOT NULL,
    name        text NOT NULL,
    email       text NOT NULL,
    created_at  timestamptz NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS oidc_login (
    state       text PRIMARY KEY,
    verifier    text NOT NULL,
    created_at  timestamptz NOT NULL DEFAULT now()
);
