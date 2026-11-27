---
title: Operationsrahmen (Minimalstand)
type: code
sources:
  - issue:#101
  - docs/arc42/09-entscheidungen/ADR-005-operationsschicht.md
  - docs/arc42/08-konzepte/K-006-operationsschicht-und-assistent.md
  - docs/arc42/05-bausteine/02-crate-zuschnitt.md
  - crates/core/src/frame.rs
  - crates/core/src/operation.rs
  - crates/core/src/context.rs
  - crates/chronos/tests/operationsrahmen/main.rs
  - crates/chronos/tests/architecture.rs
confidence: hoch
last-verified: 2026-11-27
---

# Operationsrahmen (Minimalstand)

Verbindlich ist ADR-005 (V2: der Rahmen trägt den Querschnitt). Diese Seite ist die Landkarte des Codes in `crates/core` (Stand #101).

## Bausteine
- **`Operation`** (Trait, `operation.rs`): `NAME` (`bereich.verb`), `DESCRIPTION` (Englisch), `MODE` (`Read`/`Write`), `Params`/`Output` mit Schema, `scope(&params)`, `run(ctx, params)`. Registrierung mit `register_operation!(Typ)` (über `inventory`, `Registration::of::<O>()` ist `const fn`).
- **`Frame`** (`frame.rs`): `execute(principal, name, params, correlation_id, Run::Apply | Run::DryRun)`. Reihenfolge: Operation suchen → Geltungsbereich prüfen (**vor** dem ersten Datenbankzugriff) → Transaktion (lesend `SET TRANSACTION READ ONLY`) → `run` → bei `Apply`: Verlauf und Outbox schreiben, committen; bei `DryRun`: zurückrollen. Jeder Fehler vor dem Commit rollt alles zurück (Drop der Transaktion).
- **`Context`** (`context.rs`): Konstruktor `pub(crate)`, ein `compile_fail,E0624`-Doctest belegt, dass Fremdcode ihn nicht bauen kann. Gibt `db()` (`&mut PgConnection` der Transaktion), `record_change`, `emit`. In lesenden Operationen liefern `record_change`/`emit` `read_only`.
- **Akteure:** `Principal` (private Felder, Konstruktoren `person`/`guest` nur `pub(crate)`: sonst könnte beliebiger Code Akteure erzeugen und die Sperre des Test-Principals umgehen; `compile_fail`-Doctest belegt es), `ActorKind`, `PersonId`. Tabelle `person (id, kind, created_at)`, `kind` ist `person` oder `guest`.
- **Geltungsbereich:** `Scope::{Public, Authenticated, Person(id)}`. Eine Ablehnung ist `ErrorCode::NotFound`, also **dasselbe** wie ein fehlendes Objekt (Test `out_of_scope_looks_like_a_missing_object`).
- **Fehler:** `Error { code, params }`, nur Codes (`not_found`, `unknown_operation`, `invalid_params`, `read_only`, `test_principal_forbidden`, `database` mit `sqlstate`, `internal` für Fehler im Rahmen selbst). `From<sqlx::Error>` bildet SQLSTATE `25006` auf `read_only` ab.
- **Schemaquelle:** gekapselt in `chronos_core::schema` (Re-Export von `schemars`). Fachcode leitet mit `#[schemars(crate = "chronos_core::schema::schemars")]` ab. `schemars` gegen `utoipa` ist weiter offen (E-005a, Product Owner).
- **Test-Principal:** `Frame::test_principal()` und `Frame::test_actor(kind)` (weitere Akteure, etwa Fremde oder Gäste, für Tests) legen die Person mit fester Kennung (`Uuid::from_u128(1)`) an. `Environment::Production` lehnt ab (`test_principal_forbidden`). `Environment::from_env()` liest `CHRONOS_ENV`; **ohne Angabe gilt Produktion**, unbekannte Werte sind ein Fehler. Verdrahtung in `serve`/`worker` folgt mit deren Umsetzung.
- **Tabellen** (Migration `20261125010000_operation_frame.sql`, alle Namen englisch nach `docs/README.md` Regel 4): `person`, `history` (`actor`, `occurred_at`, `action`, `object_kind`, `object_id`, `previous_state`, `correlation_id`, `bundle_id` bleibt `NULL`), `outbox` (`event`, `payload`, `actor`, `correlation_id`, `created_at`, `processed_at`). `history` und `outbox` haben einen Fremdschlüssel auf `person`: Ein Akteur ohne Zeile lässt den Aufruf scheitern und alles zurückrollen.

## Namen
Code-Namen und Fehlermeldungen sind englisch (`docs/README.md` Regel 4, Glossar); deutsch bleiben Kommentare, Doc-Kommentare außerhalb von Schema-Typen und die Hilfetexte von `clap` (nicht übersetzt). Das Ticket #101 wurde am 2026-11-27 auf englische Namen umgestellt (`actor`, `occurred_at`, `action`, `object`, `previous_state`, `correlation_id`, `bundle_id`). Abweichung: `object` ist als `object_kind` und `object_id` umgesetzt. Rust-Felder von `Change`: `previous_state`, `new_state`. Beispiel-Tabelle im Test: `example_note`.

## Tests
- `crates/chronos/tests/operationsrahmen/` (`main.rs`, `beispiel.rs`; Dateiname deutsch, Inhalt englisch): Beispieloperationen im Test, `#[sqlx::test]`; Snapshot mit `insta` in `snapshots/`. Gezielt: `cargo nextest run -E 'test(operationsrahmen)'`.
- `architecture.rs`: `domain_does_not_reach_adapters` (Kanten) und `domain_gets_no_database_connection_without_the_frame` (sucht in `crates/domain/src` Bausteine wie `PgPool`, `.begin(`, `chronos_core::db`, `Context::new`; reine Textsuche, ein Kommentar mit diesen Wörtern schlägt auch an).
- Gegenprobe in #101: absichtlich `PgPool` in `domain` und eine Kante zu `chronos-adapters` eingebaut, beide Tests schlugen fehl.
- Schemaänderung bewusst übernehmen: `cargo insta review` (oder `INSTA_UPDATE=always`). CI: `cargo insta test --check --workspace`.

## Stolpersteine
- **`sqlx` 0.9 verlangt `&'static str`** für `query`/`query_scalar` (Fehler „dynamic SQL strings should be audited“). Dynamische Tabellennamen in Tests über ein `match` auf Literale lösen.
- **`cargo insta test` kennt kein `--locked`;** Argumente nach `--` gehen an den Testrunner, nicht an Cargo.
- Jede neue Abhängigkeit eines Crates ändert `Cargo.lock`; erst einmal ohne `--locked` bauen, dann einchecken.
- Die Feature-Liste von `sqlx` braucht `uuid` und `json` für `Uuid` und `serde_json::Value` in Bindings.
- Doc-Kommentare auf Typen, die das Schema ableiten, landen im Schema (und damit beim Assistenten): Englisch schreiben.
- **Messwerte (Spike-Erweiterung E-005a):** Rahmen in `crates/core` ohne `db.rs` und Unit-Tests 467 Codezeilen (649 physische Zeilen, ohne Leer- und Kommentarzeilen gezählt, `tokei` fehlte); Operation `notes.create` 21 Codezeilen, alle fünf Beispieloperationen 149. ADR-005 schätzte 200 bis 400 Zeilen für den Rahmen.

## Verhalten im Detail
- **Probelauf** schreibt `history` und `outbox` mit und rollt erst dann zurück, damit er dieselben Fehler zeigt wie `Apply` (etwa einen Akteur ohne `person`-Zeile, SQLSTATE `23503`).
- **Doppelte Operationsnamen** lässt `Frame::new` per Panic am Start auffallen (`Registration::find` nähme sonst den ersten Treffer).
- **Architekturtest:** Kommentare werden vor der Textsuche entfernt; `Pool` deckt `PgPool`, `PoolConnection` und `Pool<Postgres>` ab. Bleibt Textsuche und kein Beweis; den Rest sichert der nicht öffentliche `Context`-Konstruktor.
- **CI:** `cargo insta test --check --workspace --unreferenced=reject` meldet auch verwaiste Snapshots. Die Suite läuft dabei ein zweites Mal (bewusst, Form aus dem Ticket).

## Offen
Wie Gäste ihre `person`-Zeile bekommen (Gast-Feature, E-008): Der Rahmen legt sie nicht an, ohne Zeile scheitert jeder schreibende Aufruf am Fremdschlüssel. Freigabe-Beleg und Stapel (F-015), Verlaufsanzeige und Wiederherstellung (F-017), voller Verlaufsmechanismus mit Architekturtest (#34), Bündel-ID-Vergabe, Schemaquelle `schemars`/`utoipa` (E-005a).
