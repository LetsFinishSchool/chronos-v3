-- +goose Up
CREATE TABLE persons (
    id         text PRIMARY KEY,
    name       text NOT NULL,
    email      text NOT NULL,
    channels   text[] NOT NULL DEFAULT '{webpush,email}',
    created_at timestamptz NOT NULL DEFAULT now()
);

CREATE TABLE teams (
    id        uuid PRIMARY KEY,
    name      text NOT NULL,
    parent_id uuid REFERENCES teams (id)
);
CREATE INDEX teams_parent_idx ON teams (parent_id);

CREATE TABLE team_members (
    team_id   uuid NOT NULL REFERENCES teams (id),
    person_id text NOT NULL REFERENCES persons (id),
    PRIMARY KEY (team_id, person_id)
);
CREATE INDEX team_members_person_idx ON team_members (person_id);

CREATE TABLE appointments (
    id        uuid PRIMARY KEY,
    team_id   uuid NOT NULL REFERENCES teams (id),
    title     text NOT NULL,
    starts_at timestamptz NOT NULL,
    ends_at   timestamptz NOT NULL,
    timezone  text NOT NULL,
    status    text NOT NULL
);
CREATE INDEX appointments_team_idx ON appointments (team_id, starts_at, id);

CREATE TABLE series (
    id               uuid PRIMARY KEY,
    team_id          uuid NOT NULL REFERENCES teams (id),
    title            text NOT NULL,
    rrule            text NOT NULL,
    dtstart          text NOT NULL,
    timezone         text NOT NULL,
    duration_minutes integer NOT NULL,
    exdates          text[] NOT NULL DEFAULT '{}'
);

CREATE TABLE events (
    id              uuid PRIMARY KEY,
    type            text NOT NULL,
    actor           text NOT NULL,
    operation       text NOT NULL,
    correlation_id  text NOT NULL,
    forced_channel  text,
    created_at      timestamptz NOT NULL DEFAULT now()
);

CREATE TABLE history (
    id             uuid PRIMARY KEY,
    seq            bigserial NOT NULL,
    at             timestamptz NOT NULL DEFAULT now(),
    actor          text NOT NULL,
    action         text NOT NULL,
    object_type    text NOT NULL,
    object_id      uuid NOT NULL,
    team_id        uuid NOT NULL REFERENCES teams (id),
    before         jsonb,
    after          jsonb,
    bundle_id      uuid NOT NULL,
    correlation_id text NOT NULL,
    undone         boolean NOT NULL DEFAULT false,
    undo_of        uuid REFERENCES history (id),
    event_id       uuid
);
CREATE INDEX history_seq_idx ON history (seq DESC);
CREATE INDEX history_object_idx ON history (object_id, seq DESC);

CREATE TABLE event_recipients (
    event_id      uuid NOT NULL REFERENCES events (id),
    recipient     text NOT NULL,
    state         text NOT NULL DEFAULT 'pending',
    claimed_until timestamptz,
    created_at    timestamptz NOT NULL DEFAULT now(),
    PRIMARY KEY (event_id, recipient)
);
CREATE INDEX event_recipients_pending_idx ON event_recipients (created_at) WHERE state = 'pending';

CREATE TABLE deliveries (
    id              bigserial PRIMARY KEY,
    event_id        uuid NOT NULL REFERENCES events (id),
    recipient       text NOT NULL,
    channel         text NOT NULL,
    attempt         integer NOT NULL,
    result          text NOT NULL,
    error           text,
    at              timestamptz NOT NULL DEFAULT now(),
    idempotency_key text NOT NULL
);
CREATE INDEX deliveries_event_idx ON deliveries (event_id, recipient);

CREATE TABLE push_subscriptions (
    person_id text NOT NULL REFERENCES persons (id),
    endpoint  text NOT NULL,
    p256dh    text NOT NULL,
    auth      text NOT NULL,
    PRIMARY KEY (person_id, endpoint)
);

CREATE TABLE costs (
    id              uuid PRIMARY KEY,
    at              timestamptz NOT NULL DEFAULT now(),
    seq             bigserial NOT NULL,
    person_id       text NOT NULL,
    provider        text NOT NULL,
    trigger_kind    text NOT NULL,
    trigger_name    text NOT NULL,
    correlation_id  text NOT NULL,
    quantity        jsonb NOT NULL,
    amount_micro_eur bigint NOT NULL
);
CREATE INDEX costs_person_idx ON costs (person_id, seq DESC);

CREATE TABLE auth_flows (
    state      text PRIMARY KEY,
    verifier   text NOT NULL,
    created_at timestamptz NOT NULL DEFAULT now()
);

CREATE TABLE sessions (
    id         text PRIMARY KEY,
    person_id  text NOT NULL REFERENCES persons (id),
    created_at timestamptz NOT NULL DEFAULT now()
);

-- +goose Down
DROP TABLE sessions, auth_flows, costs, push_subscriptions, deliveries, event_recipients, history, events, series, appointments, team_members, teams, persons;
