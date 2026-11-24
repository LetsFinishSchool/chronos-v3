CREATE TABLE persons (
  id text PRIMARY KEY,
  name text NOT NULL DEFAULT '',
  email text NOT NULL DEFAULT '',
  channels text[] NOT NULL DEFAULT ARRAY['webpush','email'],
  created_at timestamptz NOT NULL DEFAULT now()
);

CREATE TABLE teams (
  id uuid PRIMARY KEY,
  name text NOT NULL,
  parent_id uuid REFERENCES teams(id)
);
CREATE INDEX teams_parent ON teams(parent_id);

CREATE TABLE team_members (
  team_id uuid NOT NULL REFERENCES teams(id),
  person_id text NOT NULL REFERENCES persons(id),
  PRIMARY KEY (team_id, person_id)
);
CREATE INDEX team_members_person ON team_members(person_id);

CREATE TABLE appointments (
  id uuid PRIMARY KEY,
  team_id uuid NOT NULL REFERENCES teams(id),
  title text NOT NULL,
  starts_at timestamptz NOT NULL,
  ends_at timestamptz NOT NULL,
  timezone text NOT NULL,
  status text NOT NULL
);
CREATE INDEX appointments_team ON appointments(team_id, starts_at, id);

CREATE TABLE series (
  id uuid PRIMARY KEY,
  team_id uuid NOT NULL REFERENCES teams(id),
  title text NOT NULL,
  rrule text NOT NULL,
  dtstart text NOT NULL,
  timezone text NOT NULL,
  duration_minutes int NOT NULL,
  exdates text[] NOT NULL DEFAULT '{}',
  status text NOT NULL DEFAULT 'aktiv'
);

CREATE TABLE events (
  id uuid PRIMARY KEY,
  seq bigserial,
  event_type text NOT NULL,
  trigger_kind text NOT NULL DEFAULT 'person',
  trigger_actor text NOT NULL,
  trigger_op text NOT NULL,
  correlation_id text NOT NULL,
  payload jsonb NOT NULL DEFAULT '{}',
  recipients text[] NOT NULL,
  only_channel text,
  created_at timestamptz NOT NULL DEFAULT now()
);
CREATE INDEX events_corr ON events(correlation_id);
CREATE INDEX events_actor ON events(trigger_actor);

CREATE TABLE history (
  id uuid PRIMARY KEY,
  seq bigserial,
  at timestamptz NOT NULL DEFAULT now(),
  actor text NOT NULL,
  action text NOT NULL,
  object_type text NOT NULL,
  object_id uuid NOT NULL,
  team_id uuid NOT NULL REFERENCES teams(id),
  before jsonb,
  after jsonb,
  bundle_id uuid NOT NULL,
  correlation_id text NOT NULL,
  undone boolean NOT NULL DEFAULT false,
  undo_of uuid,
  event_id uuid
);
CREATE INDEX history_object ON history(object_id, seq DESC);
CREATE INDEX history_team ON history(team_id, seq DESC);

-- Arbeitsliste des Workers: je (Ereignis, Empfänger) eine Zeile, in derselben Transaktion wie das Ereignis angelegt.
CREATE TABLE delivery_tasks (
  id bigserial PRIMARY KEY,
  event_id uuid NOT NULL REFERENCES events(id),
  recipient text NOT NULL,
  channel_idx int NOT NULL DEFAULT 0,
  attempt int NOT NULL DEFAULT 1,
  state text NOT NULL DEFAULT 'pending',
  next_at timestamptz NOT NULL DEFAULT now(),
  locked_until timestamptz
);
CREATE INDEX delivery_tasks_pending ON delivery_tasks(next_at) WHERE state = 'pending';

-- Zustellprotokoll: je Versuch eine Zeile.
CREATE TABLE deliveries (
  id bigserial PRIMARY KEY,
  event_id uuid NOT NULL REFERENCES events(id),
  recipient text NOT NULL,
  channel text NOT NULL,
  attempt int NOT NULL,
  result text NOT NULL,
  error text,
  at timestamptz NOT NULL DEFAULT now(),
  idempotency_key text NOT NULL
);
CREATE INDEX deliveries_event ON deliveries(event_id, id);

CREATE TABLE cost_entries (
  id uuid PRIMARY KEY,
  seq bigserial,
  at timestamptz NOT NULL DEFAULT now(),
  person_id text NOT NULL,
  provider text NOT NULL,
  trigger_kind text NOT NULL,
  trigger_name text NOT NULL,
  correlation_id text NOT NULL,
  quantity jsonb NOT NULL,
  amount_micro_eur bigint NOT NULL
);
CREATE INDEX cost_person ON cost_entries(person_id, seq DESC);

CREATE TABLE push_subscriptions (
  person_id text NOT NULL REFERENCES persons(id),
  endpoint text NOT NULL,
  p256dh text NOT NULL,
  auth text NOT NULL,
  PRIMARY KEY (person_id, endpoint)
);

CREATE TABLE oidc_states (
  state text PRIMARY KEY,
  pkce_verifier text NOT NULL,
  nonce text NOT NULL,
  created_at timestamptz NOT NULL DEFAULT now()
);

CREATE TABLE sessions (
  token text PRIMARY KEY,
  person_id text NOT NULL REFERENCES persons(id),
  created_at timestamptz NOT NULL DEFAULT now()
);
