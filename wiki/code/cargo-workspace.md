---
title: Cargo-Workspace und Architekturtest
type: code
sources:
  - issue:#99
  - docs/arc42/05-bausteine/02-crate-zuschnitt.md
  - docs/arc42/09-entscheidungen/ADR-009-teststrategie-und-architekturregeln.md
  - Cargo.toml@380e69f
  - crates/chronos/tests/architecture.rs@380e69f
  - crates/chronos/src/main.rs@380e69f
  - rust-toolchain.toml@1c961a8
  - crates/chronos/tests/cli.rs@19720ed
confidence: hoch
last-verified: 2026-11-24
---

# Cargo-Workspace und Architekturtest

Verbindlich ist der [Crate-Zuschnitt](../../docs/arc42/05-bausteine/02-crate-zuschnitt.md); diese Seite ist die Landkarte des Codes dazu (Stand #99).

## Aufbau
- Wurzel-`Cargo.toml`: `resolver = "3"`, `edition = "2024"`, `[workspace.package]` (Version, `publish = false`), `[workspace.dependencies]` für **alle** Abhängigkeiten (Workspace-Crates per `path`, fremde mit Version), `[workspace.lints]` (`unsafe_code = "forbid"`, `clippy::all = warn`). Jedes Crate erbt mit `x.workspace = true` und `[lints] workspace = true`.
- `rust-toolchain.toml`: 1.100.0 mit `rustfmt`, `clippy`; `rust-version` im Workspace gleich. Vorgabe des Product Owners in #99 (ursprünglich 1.95.0 im Ticket). Lokal fehlende Version: `rustup toolchain install 1.100.0 --profile minimal --component rustfmt --component clippy`.
- **Ungenutzte Abhängigkeiten:** Cargo ab 1.100 warnt bei Abhängigkeiten, die der Code nicht nutzt (Manifest-Warnung, `clippy -D warnings` fängt sie **nicht**, nur ein Blick auf `cargo build`). Leere Crates binden ihre erlaubten Kanten deshalb mit `use <crate> as _;` ein. Sobald echter Code die Kante nutzt, kann die Zeile weg.
- Crates unter `crates/<kurz>`, Paketname `chronos-<kurz>`, Bibliotheksname `chronos_<kurz>`. Das Binary heißt `chronos` (`crates/chronos/src/main.rs`).
- Modulkommentar jeder `lib.rs`/`main.rs`: ein Satz zum Zweck plus Verweis auf Kapitel 5. Die Listen „Zuständig / Nicht zuständig“ stehen bewusst nur in `docs/`, damit keine zweite, ungeprüfte Fassung driftet.

## Binary
- `chronos serve` gibt „not implemented yet“ auf stderr aus, Exit-Code **69** (`EX_UNAVAILABLE` aus `sysexits.h`), Konstante `EXIT_NOT_IMPLEMENTED` in `main.rs` (`crates/chronos/tests/cli.rs`). `chronos worker` ist seit #102 implementiert (`code/worker-und-outbox.md`).
- Ursprünglich verlangte #99 Exit-Code 2. Der Product Owner hat auf 69 umgestellt, weil clap bei Bedienfehlern (unbekannter Unterbefehl, falsches Argument, kein Unterbefehl) **ebenfalls** mit 2 endet und der Aufrufer beides nicht unterscheiden konnte. Ein Test sichert, dass Bedienfehler weiter mit 2 enden. Für eigene Exit-Codes nie 2 verwenden.
- `use chronos_domain as _;` in `main.rs` bleibt stehen, auch wenn es ungenutzt aussieht: Es linkt die Operationen (später über `inventory`).

## Architekturtest (`crates/chronos/tests/architecture.rs`)
- Die Positivliste steht als Konstante `ALLOWED` im Test und muss der Tabelle in Kapitel 5 gleichen. Neues Crate = Eintrag in `ALLOWED` **und** Freigabe des Zuschnitts durch den Product Owner.
- Liest `cargo metadata --no-deps`; zählt jede Kante zwischen Workspace-Crates, auch Dev- und Build-Abhängigkeiten.
- Prüft: Crates und Positivliste deckungsgleich, keine Kante außerhalb der Liste, keine Zyklen. Die Prüffunktionen haben eigene Tests an gebauten Graphen.
- **Zyklen:** Bei normalen Abhängigkeiten lehnt Cargo selbst ab (`error: cyclic package dependency`), der Test kommt gar nicht zum Laufen. Über **Dev-Abhängigkeiten** erlaubt Cargo Zyklen; die fängt erst der Test (`workspace_has_no_cycles`). Gegenprobe in #99: `chronos-core` mit Dev-Abhängigkeit auf `chronos-domain`.

## Prüfbefehle
```
cargo build --workspace --locked
cargo fmt --all --check
cargo clippy --workspace --all-targets --locked -- -D warnings
cargo nextest run --workspace --locked
```
`cargo-nextest` ist nicht vorinstalliert: `cargo install --locked cargo-nextest` (dauert einige Minuten). Gezielt einen Test: `cargo nextest run -E 'test(workspace_has_only_allowed_edges)'`.
