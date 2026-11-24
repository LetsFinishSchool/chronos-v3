---
id: ADR-013
title: Build, CI und Lieferkette: cargo-deny als harte Prüfung mit befristeten Ausnahmen
status: freigegeben   # entwurf | freigegeben | ersetzt
freigegeben-am: 2026-11-24
freigegeben-von: Product Owner
ersetzt-durch:
loest: [E-021]
quellen: [ADR-004 (Punkt 3, Folgen), ADR-009, ADR-012, RA-003, Entscheidung des Product Owners 2026-11-24 (Gespräch)]
---

# ADR-013: Build, CI und Lieferkette: cargo-deny als harte Prüfung mit befristeten Ausnahmen

**Hinweis:** Der Product Owner hat die Entscheidung am 2026-11-24 im Gespräch getroffen. Dieser Text wurde vom Product Owner am 2026-11-24 freigegeben. Die neue Nummer E-021 ist in Kapitel 9 ergänzt.

## Kontext
Rust bringt eine große Abhängigkeitsmenge (375 Crates), Sicherheitsmeldungen und schwachen Pflegestand einzelner Bibliotheken mit ([ADR-004](ADR-004-sprache-und-laufzeit.md)). Das Team ist eine Person ([RA-003](../../req42/12-risiken-annahmen/RA-003-betrieb-und-entwicklung-haengen-an-einer-person.md)). ADR-004 Punkt 3 verlangt die Prüfung der Sicherheitsmeldungen in der Pipeline; [ADR-012](ADR-012-zeitbibliothek.md) lässt `chrono` und `chrono-tz` an den Rändern als dokumentierte Ausnahme zu.

## Optionen
A `cargo-deny` als harte CI-Prüfung mit dokumentierten Ausnahmen; B nur `cargo audit` als Warnung; C A plus `cargo-vet`. Vor- und Nachteile der abgelehnten Optionen:

| Option | Vorteile | Nachteile |
|---|---|---|
| **B** Nur `cargo audit` als Warnung | Kein Blockieren | Meldungen werden übersehen (RA-003, eine Person) |
| **C** A + `cargo-vet` (geprüfte Crates) | Stärkste Lieferkettenkontrolle | Für eine Person mit 375 Crates kaum leistbar |


## Entscheidung (PO, 2026-11-24)
**Option A, mit Ablaufdatum für jede Ausnahme.**
1. `cargo-deny` läuft in CI als **harte Prüfung**: Advisories, Lizenzen, erlaubte Quellen und Bans. Ein Verstoß blockiert den Merge.
2. Jede **Ausnahme** steht in `deny.toml` mit Begründung **und Ablaufdatum**. Nach Ablauf schlägt die Prüfung wieder an, die Ausnahme muss neu bewertet und bei Bedarf neu begründet und befristet werden. Dies gilt auch für die dauerhaft gedachten Ausnahmen (z. B. `chrono-tz`, ADR-012).
3. Länge der Frist: **90 Tage** (bestätigt am 2026-11-24).
4. Die `bans`-Regeln ergänzen die Crate-Grenzen aus [ADR-009](ADR-009-teststrategie-und-architekturregeln.md) (verbotene Bibliotheken je Crate).

**Standard-Bausteine und Image:** siehe Abschnitt „Standard-Bausteine und Image“ (entschieden, `distroless/cc`).

## Folgen
**Leichter:** Ausnahmen sind sichtbar, begründet und werden regelmäßig neu bewertet; ADR-004 Punkt 3 ist umgesetzt; Lizenzen und Quellen werden mitgeprüft.

**Schwerer / Risiken:**
- Neue Sicherheitsmeldungen und auslaufende Ausnahmen blockieren Merges und verlangen kurzfristige Pflege (Aufwand für eine Person, RA-003). Gegen Zeitdruck hilft eine neu begründete, befristete Ausnahme.
- Pflege von `deny.toml` ist laufende Aufgabe; Erinnerung vor Ablauf (z. B. Warnung ab 14 Tagen vorher) ist bei der Umsetzung vorzusehen.

**Bindet:** [ADR-012](ADR-012-zeitbibliothek.md) (Ausnahmen für `chrono`/`chrono-tz`), [ADR-009](ADR-009-teststrategie-und-architekturregeln.md) (Bans), CI-Pipeline.

## Festgelegte Werte (PO, 2026-11-24)
- **Frist der Ausnahmen:** 90 Tage (bestätigt), Vorwarnung 14 Tage vorher.

## Standard-Bausteine und Image (PO, 2026-11-24)
Die zuvor als Vorschlag geführten Bausteine sind entschieden (der Absatz „Vorschlag, nicht entschieden“ in der Entscheidung gilt damit als erledigt):
- `rust-toolchain.toml` mit fester Toolchain; Build-Cache in GitHub Actions für `target` und Registry; `cargo-chef` im Dockerfile; Renovate oder Dependabot für Updates.
- **Image:** `distroless/cc` (glibc, CA-Zertifikate, `tzdata`), keine Shell und kein Paketmanager; Debugging über Ephemeral Container (`kubectl debug`). Statisches musl (`distroless/static`) bleibt eine spätere Option; der Allocator wäre dann zu prüfen.
- **Kein OpenSSL:** `rustls` überall, auch bei `lettre` (SMTP-TLS) und `sqlx` (TLS zur Datenbank); die Features sind bei der Umsetzung zu setzen, im Spike fehlen sie. `web-push-native` (ADR-004) hält OpenSSL aus dem Baum. Ein `bans`-Eintrag in `deny.toml` verbietet `openssl-sys` und `native-tls`, damit OpenSSL nicht zurückkehrt.

## Wann überprüfen?
- Die Zahl der Ausnahmen oder Blockaden wird für eine Person untragbar (dann Frist verlängern oder Option B als Übergang).
- Ein Auftraggeber verlangt höhere Lieferkettensicherheit (dann `cargo-vet`, Option C).
