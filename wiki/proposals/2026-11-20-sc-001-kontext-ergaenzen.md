---
title: SC-001 um KI-Anbieter und Ferien-API ergänzen
type: proposal
status: angenommen und übernommen
sources:
  - docs/req42/03-scope/SC-001-systemkontext.md
  - docs/req42/04-product-backlog/anforderungen/FA-015-ki-assistent.md
  - docs/req42/04-product-backlog/anforderungen/FA-014-serientermine.md
  - docs/req42/12-risiken-annahmen/RA-008-offene-fragen.md
confidence: hoch
last-verified: 2026-11-20
---

# Vorschlag: SC-001 ergänzen

**Befund (beim Befüllen von arc42 Kapitel 3):** Das Kontextdiagramm in SC-001 kennt zwei Nachbarsysteme nicht, die req42 an anderer Stelle voraussetzt:

1. **KI-Anbieter** (FA-015, RB-010, RA-010): anbieterneutral, Start mit Claude, erhält personenbezogene Daten.
2. **Öffentliche Ferien-API** (FA-014, RA-008 Runde 6): Schulferien mit Cache.

**Vorschlag:** Beide in `SC-001` (Diagramm und Tabelle) aufnehmen. arc42 Kapitel 3 führt sie bereits (Entwurf).

**Weitere Auffälligkeit:** `QA-008-leistung.md` bricht im Szenario mitten im Satz ab („…antworten Standardaktionen innerhalb des Ressourcenbudgets in eine Seite lädt in unter 1 s“). Formulierung durch den Product Owner klären.

Auf Anweisung des Nutzers in `SC-001` und `QA-008` übernommen (2026-11-20). QA-008 wurde sinngemäß als „lädt eine Seite in unter 1 s“ formuliert.
