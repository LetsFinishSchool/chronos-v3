---
title: Datenbankanbindung und Migrationen
type: code
sources:
  - issue:#100
  - docs/arc42/09-entscheidungen/ADR-011-migrationswerkzeug.md
  - crates/core/src/db.rs
  - crates/chronos/src/main.rs
  - crates/chronos/tests/database.rs
  - compose.yaml
  - tools/db/init-roles.sql
confidence: hoch
last-verified: 2026-11-25
---

# Datenbankanbindung und Migrationen

- **Pool und Schemaprüfung:** `chronos-core::db` (`connect`, `connect_lazy`, `wait_for_schema`). Migrationen liegen in `crates/chronos/migrations/` und werden in `chronos` per `sqlx::migrate!()` eingebettet (`build.rs` für `rerun-if-changed`).
- **Umgebung:** `DATABASE_URL` (Migrationsbenutzer, nur `migrate`), `DATABASE_URL_APP` (Anwendungsbenutzer, `serve`/`worker`), `CHRONOS_SCHEMA_WAIT_SECS` (Standard 60), `CHRONOS_MIGRATE_ON_START` (nur lokal).
- **Exit-Codes:** 75 = Schema nach Wartezeit zu alt; 1 = Konfiguration, Verbindung, Migration; 69 wird seit #102 nicht mehr vergeben (früher „not implemented yet“); 2 gehört clap. Eine Datenbank, die *weiter* ist als das Binary, ist erlaubt.
- **Rollen:** `tools/db/init-roles.sql`. Die erste Migration gibt `chronos_app` `SELECT` auf `_sqlx_migrations` (sqlx legt sie vor Migration 1 an, Default-Privilegien greifen dort nicht) und setzt `ALTER DEFAULT PRIVILEGES` für spätere Tabellen.
- **Tests:** `crates/chronos/tests/database.rs` mit `#[sqlx::test]`; sie brauchen `DATABASE_URL` und `DATABASE_URL_APP`. `cli.rs` migriert die gemeinsame Datenbank selbst (idempotent). `.sqlx` entsteht mit `cargo sqlx prepare --workspace -- --all-targets`; mindestens eine `query!` (`applied_version`) hält die Prüfung aussagekräftig.

## Stolpersteine
- **Healthcheck:** `pg_isready` ohne `-h 127.0.0.1` meldet schon am Unix-Socket des Init-Servers „gesund“, bevor `init-roles.sql` lief; `docker compose up --wait` kehrte dann zu früh zurück.
- **`webpki-roots`** (über `tls-rustls-ring-webpki`) hat die Lizenz `CDLA-Permissive-2.0`; in `deny.toml` unter `allow` ergänzt.
- **`taiki-e/install-action` kennt `sqlx-cli` nicht:** in CI `cargo install sqlx-cli --version 0.9.1 --locked …`, Version von Hand anheben.
- **Rootless Docker mit pasta:** veröffentlichte Host-Ports (auch `busybox`) waren im Agenten-Setup nicht erreichbar. Notlösung zum Testen: Postgres-Container mit gemountetem Socket-Verzeichnis (`-v DIR:/var/run/postgresql`) und `DATABASE_URL=postgres://…@localhost/chronos?host=DIR`. `compose.yaml` selbst wurde dort nicht per TCP geprüft.
- **Socket-Pfad:** Unix-Socket-Pfade sind auf 107 Bytes begrenzt; das Scratchpad-Verzeichnis ist zu lang. Socket-Verzeichnis kurz wählen (z. B. `/tmp/c101pg`, `chmod 777`), Rollen mit `tools/db/init-roles.sql` per `psql` anlegen (#101).
- `git checkout <datei>` zur Gegenprobe verwirft auch nicht committete Änderungen derselben Datei; Gegenproben mit `git stash`-freiem Rücksetzen per `sed` umkehren.
