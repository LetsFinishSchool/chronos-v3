---
title: sqlx und das rsa-Advisory
type: concept
sources:
  - issue:#100
  - deny.toml
confidence: mittel
last-verified: 2026-11-25
---

# sqlx und das rsa-Advisory

- Probe in einem Wegwerf-Crate (`default-features = false`, Features `runtime-tokio`, `tls-rustls-ring-webpki`, `postgres`, `migrate`, `macros`): **sqlx 0.8.6** schreibt `sqlx-mysql` und `rsa` in die `Cargo.lock`, obwohl `rsa` nicht gebaut wird (`cargo tree -i rsa` meldet „nothing to print“). `cargo deny` liest die Lockdatei und kann deshalb RUSTSEC-2023-0071 melden.
- **sqlx 0.9.1**: kein `rsa` in der `Cargo.lock`; `cargo deny check advisories bans` ohne Befund. `sqlx-mysql` und `sqlx-sqlite` stehen weiter in der Lockdatei, auch ohne `macros`; das ist harmlos.
- Entscheidung in #100: sqlx 0.9. Nicht geprüft: Verhalten von `cargo deny licenses` und der Ausnahmen in der echten `deny.toml` des Projekts; das zeigt der Task.
