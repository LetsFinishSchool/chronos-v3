---
title: CI und Lieferkettenprüfung
type: code
sources:
  - issue:#107
  - docs/arc42/09-entscheidungen/ADR-013-build-ci-lieferkette.md
  - .github/workflows/ci.yml
  - deny.toml
  - tools/check-deny-expiry.sh
confidence: hoch
last-verified: 2026-11-24
---

# CI und Lieferkettenprüfung

- `.github/workflows/ci.yml`: vier Jobs (Format, Clippy, Tests, Lieferkette) bei Pull Request und Push auf `main`. Actions auf Commit-Hash festgelegt (Version im Kommentar), Werkzeuge über `taiki-e/install-action` mit fester Version (`cargo-nextest@0.9.152`, `cargo-deny@0.22.1`). Beim Aktualisieren Hash per `gh api repos/<r>/commits/<tag>` holen.
- `deny.toml`: Ausnahmen mit `reason` und `bis JJJJ-MM-TT` (90 Tage). `tools/check-deny-expiry.sh` liest diese Daten (`DENY_TODAY=` für Tests): abgelaufen = Exit 1, ab 14 Tage vorher Warnung.
- **Stolpersteine:** Workspace-Pfadabhängigkeiten zählen als Wildcards (`allow-wildcard-paths = true`); Workspace-Crates ohne Lizenz brauchen `[licenses.private] ignore = true`; ein `wrappers`-Eintrag für ein noch nicht vorhandenes Crate ist nur eine Warnung.
- Gegenprobe: `native-tls` als Abhängigkeit zieht `openssl-sys` mit und lässt `cargo deny check bans` fehlschlagen.
- Ablaufskript: prüft jede einzeilige Ausnahme (`reason =` oder `RUSTSEC-`) und lässt eine ohne `bis JJJJ-MM-TT` fehlschlagen; die 90-Tage-Obergrenze ist nicht prüfbar (kein Eintragsdatum), das bleibt Review-Sache. Ausnahmen müssen einzeilig stehen. Ausgabe als `::error::`/`::warning::`.
- CI läuft zusätzlich täglich per `schedule` (nur Lieferkette), damit neue Advisories und die 14-Tage-Warnung ohne PR auffallen. Doctests laufen separat (`cargo test --doc`), weil nextest sie nicht ausführt.
- **Werkzeugversionen** (`cargo-nextest`, `cargo-deny` im `tool:`-Input) aktualisiert Dependabot nicht; von Hand anheben (`gh api repos/<r>/releases/latest`).
- Seit #100: Job `test` hat einen PostgreSQL-Service (`tools/db/init-roles.sql` per `psql`), `SQLX_OFFLINE=true` auf Workflow-Ebene, Job `sqlx-offline` prüft `.sqlx` gegen frisch migrierte Datenbank. `sqlx-cli` (`cargo install … --version 0.9.1`) wie `cargo-nextest`/`cargo-deny` von Hand aktuell halten. Details: `datenbank-und-migrationen.md`.
- Dependabot: `cargo` und `github-actions`, wöchentlich, je eine Gruppe.
- Seit #101: Job `test` installiert zusätzlich `cargo-insta@1.49.0` (von Hand aktuell halten) und führt `cargo insta test --check --workspace` aus; offene Snapshots lassen den Job fehlschlagen. Details: `operationsrahmen.md`.
