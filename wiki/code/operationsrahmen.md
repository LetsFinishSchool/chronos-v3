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
last-verified: 2026-11-25
---

# Operationsrahmen (Minimalstand)

Verbindlich ist ADR-005 (V2: der Rahmen trägt den Querschnitt). Diese Seite ist die Landkarte des Codes in `crates/core` (Stand #101).

## Bausteine
- **`Operation`** (Trait, `operation.rs`): `NAME` (`bereich.verb`), `DESCRIPTION` (Englisch), `MODE` (`Read`/`Write`), `Params`/`Output` mit Schema, `scope(&params)`, `run(ctx, params)`. Registrierung mit `register_operation!(Typ)` (über `inventory`, `Registration::of::<O>()` ist `const fn`).
- **`Frame`** (`frame.rs`): `execute(principal, name, params, korrelations_id, Run::Apply | Run::DryRun)`. Reihenfolge: Operation suchen → Geltungsbereich prüfen (**vor** dem ersten Datenbankzugriff) → Transaktion (lesend `SET TRANSACTION READ ONLY`) → `run` → bei `Apply`: Verlauf und Outbox schreiben, committen; bei `DryRun`: zurückrollen. Jeder Fehler vor dem Commit rollt alles zurück (Drop der Transaktion).
- **`Context`** (`context.rs`): Konstruktor `pub(crate)`, ein `compile_fail,E0624`-Doctest belegt, dass Fremdcode ihn nicht bauen kann. Gibt `db()` (`&mut PgConnection` der Transaktion), `record_change`, `emit`. In lesenden Operationen liefern `record_change`/`emit` `read_only`.
- **Akteure:** `Principal` (privates Feld, Konstruktoren `person`/`guest`), `ActorKind`, `PersonId`. Tabelle `person (id, art)`.
- **Geltungsbereich:** `Scope::{Public, Authenticated, Person(id)}`. Eine Ablehnung ist `ErrorCode::NotFound`, also **dasselbe** wie ein fehlendes Objekt (Test `out_of_scope_looks_like_a_missing_object`).
- **Fehler:** `Error { code, params }`, nur Codes (`not_found`, `unknown_operation`, `invalid_params`, `read_only`, `test_principal_forbidden`, `database` mit `sqlstate`). `From<sqlx::Error>` bildet SQLSTATE `25006` auf `read_only` ab.
- **Schemaquelle:** gekapselt in `chronos_core::schema` (Re-Export von `schemars`). Fachcode leitet mit `#[schemars(crate = "chronos_core::schema::schemars")]` ab. `schemars` gegen `utoipa` ist weiter offen (E-005a, Product Owner).
- **Test-Principal:** `Frame::test_principal()` legt die Person mit fester Kennung (`Uuid::from_u128(1)`) an. `Environment::Production` lehnt ab (`test_principal_forbidden`). `Environment::from_env()` liest `CHRONOS_ENV`; **ohne Angabe gilt Produktion**, unbekannte Werte sind ein Fehler. Verdrahtung in `serve`/`worker` folgt mit deren Umsetzung.
- **Tabellen** (Migration `20261125010000_operationsrahmen.sql`): `person`, `verlauf` (Akteur, Zeitpunkt, Aktion, Objekt, `vorher`, Korrelations-ID, `buendel_id` bleibt `NULL`), `outbox` (Ereignis, Nutzdaten, Auslöser, Korrelations-ID, `verarbeitet_am`). Verlauf und Outbox haben einen Fremdschlüssel auf `person`: Ein Akteur ohne Zeile lässt den Aufruf scheitern und alles zurückrollen.

## Tests
- `crates/chronos/tests/operationsrahmen/` (`main.rs`, `beispiel.rs`): Beispieloperationen im Test, `#[sqlx::test]`; Snapshot mit `insta` in `snapshots/`. Gezielt: `cargo nextest run -E 'test(operationsrahmen)'`.
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

## Offen
Freigabe-Beleg und Stapel (F-015), Verlaufsanzeige und Wiederherstellung (F-017), voller Verlaufsmechanismus mit Architekturtest (#34), Bündel-ID-Vergabe, Schemaquelle `schemars`/`utoipa` (E-005a).
