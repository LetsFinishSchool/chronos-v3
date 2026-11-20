import { Kysely, PostgresDialect, sql, type ColumnType, type Generated } from "kysely";
import { Migrator, type Migration, type MigrationProvider } from "kysely/migration";
import pg from "pg";
import { config } from "./config.js";

type Ts = ColumnType<Date, Date | string, Date | string>;
type TsDef = ColumnType<Date, Date | string | undefined, Date | string>;
type Json = ColumnType<unknown, string | null, string | null>; // jsonb: als JSON-Text schreiben

export interface Database {
  person: { id: string; name: string; email: string | null; channels: ColumnType<string[], string[] | undefined, string[]>; created_at: TsDef };
  push_subscription: { id: Generated<string>; person_id: string; endpoint: string; p256dh: string; auth: string };
  team: { id: string; name: string; parent_id: string | null };
  team_member: { team_id: string; person_id: string };
  appointment: { id: string; team_id: string; title: string; starts_at: Ts; ends_at: Ts; timezone: string; status: string };
  series: { id: string; team_id: string; title: string; rrule: string; dtstart: string; timezone: string; duration_minutes: number; exdates: ColumnType<string[], string[], string[]>; status: string };
  history: {
    id: string; seq: Generated<string>; at: TsDef; actor: string; action: string; object_type: string; object_id: string; team_id: string;
    before: Json; after: Json; bundle_id: string; correlation_id: string; undone: Generated<boolean>; undo_of: string | null; event_id: string | null;
  };
  event: { id: string; seq: Generated<string>; type: string; trigger_kind: string; trigger_actor: string; operation: string; correlation_id: string; created_at: TsDef };
  event_recipient: {
    id: Generated<string>; event_id: string; recipient: string; channels: ColumnType<string[], string[], string[]>; channel_idx: Generated<number>; attempt: Generated<number>;
    status: Generated<string>; next_attempt_at: TsDef; locked_until: Ts | null;
  };
  delivery: {
    id: Generated<string>; event_id: string; event_type: string; correlation_id: string; trigger_kind: string; trigger_actor: string;
    recipient: string; channel: string; attempt: number; result: string; error: string | null; at: TsDef; idempotency_key: string;
  };
  cost_entry: {
    id: Generated<string>; at: TsDef; person_id: string; provider: string; trigger_kind: string; trigger_name: string;
    correlation_id: string; quantity: Json; amount_micro_eur: string;
  };
  session: { id: string; person_id: string; created_at: TsDef };
  oidc_state: { state: string; verifier: string; created_at: TsDef };
}

pg.types.setTypeParser(20, (v) => v); // bigint als Text

export function createDb(max = 10): Kysely<Database> {
  return new Kysely<Database>({ dialect: new PostgresDialect({ pool: new pg.Pool({ connectionString: config.databaseUrl, max }) }) });
}

const migrations: Record<string, Migration> = {
  "001_init": {
    async up(db) {
      for (const stmt of INIT_SQL) await sql.raw(stmt).execute(db);
    },
  },
};
const provider: MigrationProvider = { getMigrations: async () => migrations };
const LAST_MIGRATION = Object.keys(migrations).at(-1)!;

export async function migrate(db: Kysely<Database>): Promise<void> {
  const { error } = await new Migrator({ db, provider }).migrateToLatest();
  if (error) throw error;
}

/** Worker: wartet, bis das Web das Schema angelegt hat. */
export async function waitForSchema(db: Kysely<Database>, timeoutMs = 60_000): Promise<void> {
  const end = Date.now() + timeoutMs;
  for (;;) {
    try {
      const r = await sql<{ n: string }>`select count(*)::text as n from kysely_migration where name = ${LAST_MIGRATION}`.execute(db);
      if (r.rows[0]?.n === "1") return;
    } catch { /* Tabelle fehlt noch */ }
    if (Date.now() > end) throw new Error("Schema nicht verfügbar");
    await new Promise((r) => setTimeout(r, 500));
  }
}

const INIT_SQL = [
  `create table person (id text primary key, name text not null, email text, channels text[] not null default '{webpush,email}', created_at timestamptz not null default now())`,
  `create table push_subscription (id uuid primary key default gen_random_uuid(), person_id text not null references person(id), endpoint text not null, p256dh text not null, auth text not null, unique (person_id, endpoint))`,
  `create table team (id uuid primary key, name text not null, parent_id uuid references team(id))`,
  `create index on team (parent_id)`,
  `create table team_member (team_id uuid not null references team(id), person_id text not null references person(id), primary key (team_id, person_id))`,
  `create index on team_member (person_id)`,
  `create table appointment (id uuid primary key, team_id uuid not null references team(id), title text not null, starts_at timestamptz not null, ends_at timestamptz not null, timezone text not null, status text not null)`,
  `create index on appointment (team_id, starts_at, id)`,
  `create table series (id uuid primary key, team_id uuid not null references team(id), title text not null, rrule text not null, dtstart text not null, timezone text not null, duration_minutes int not null, exdates text[] not null default '{}', status text not null)`,
  `create table event (id uuid primary key, seq bigserial, type text not null, trigger_kind text not null, trigger_actor text not null, operation text not null, correlation_id text not null, created_at timestamptz not null default now())`,
  `create table history (id uuid primary key, seq bigserial, at timestamptz not null default now(), actor text not null, action text not null, object_type text not null, object_id uuid not null, team_id uuid not null,
     before jsonb, after jsonb, bundle_id uuid not null, correlation_id text not null, undone boolean not null default false, undo_of uuid, event_id uuid references event(id))`,
  `create index on history (object_id, seq desc)`,
  `create index on history (team_id, seq desc)`,
  `create table event_recipient (id bigserial primary key, event_id uuid not null references event(id), recipient text not null, channels text[] not null, channel_idx int not null default 0, attempt int not null default 0,
     status text not null default 'pending', next_attempt_at timestamptz not null default now(), locked_until timestamptz)`,
  `create index on event_recipient (next_attempt_at) where status = 'pending'`,
  `create index on event_recipient (event_id)`,
  `create table delivery (id bigserial primary key, event_id uuid not null, event_type text not null, correlation_id text not null, trigger_kind text not null, trigger_actor text not null,
     recipient text not null, channel text not null, attempt int not null, result text not null, error text, at timestamptz not null default now(), idempotency_key text not null)`,
  `create index on delivery (correlation_id)`,
  `create index on delivery (event_id)`,
  `create index on delivery (recipient)`,
  `create index on delivery (trigger_actor)`,
  `create table cost_entry (id bigserial primary key, at timestamptz not null default now(), person_id text not null, provider text not null, trigger_kind text not null, trigger_name text not null,
     correlation_id text not null, quantity jsonb not null, amount_micro_eur bigint not null)`,
  `create index on cost_entry (person_id, id desc)`,
  `create table session (id text primary key, person_id text not null references person(id), created_at timestamptz not null default now())`,
  `create table oidc_state (state text primary key, verifier text not null, created_at timestamptz not null default now())`,
];
