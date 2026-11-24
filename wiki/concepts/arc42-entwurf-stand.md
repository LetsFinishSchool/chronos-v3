---
title: arc42-Stand 2026-11-24
type: concept
sources:
  - docs/arc42/09-entscheidungen/01-offene-entscheidungen.md
  - docs/arc42/
confidence: hoch
last-verified: 2026-11-24
---

# arc42-Stand 2026-11-24

arc42 ist freigegeben. E-000 bis E-021 sind entschieden (ADR-001 bis ADR-013); nur **E-017 (Datenübernahme)** ist teilweise entschieden (Altschema gegen chronos-root prüfen, M-005/RA-005). Der Entwurfsstand vom 2026-11-20 ist überholt. Am 2026-11-24 wurden auf Anweisung des Product Owners die Pflegeänderungen in README, Kapitel 3 bis 8 und Glossar direkt in `docs/` nachgezogen (veraltete „offen“/„Entwurf“-Hinweise).

## Noch offen (Umsetzungsdetails)

- ADR-004: Abschnitt „Offen nach der Freigabe“; ADR-005: Spike E-005a (`schemars`, Stapel-Obergrenze nach Messung); ADR-006: Prüfkatalog, Standardmodell, KI-Anteil am Budget; ADR-008: Obergrenze für Keycloak-Ausfall; ADR-013: 90 Tage Ausnahmefrist nur Vorschlag.
- K-003: Wiederholung, Idempotenzschlüssel, Budgetplanung; K-008: Löschkonzept bei Weggang, Auskunftsrecht, Protokoll-Aufbewahrung, Backup-Schlüsselrotation; K-009: Aufbewahrung, Alarmierung; K-011: Serienhorizont, Ausfall Ferien-API.
- Kapitel 5/7: Zuordnung von Backup und Ferien-Abruf zu Prozessen.

Weiterführend: `concepts/e-002-spike-ergebnisse.md`, `concepts/e-002-folgeentscheidungen-rust.md`.
