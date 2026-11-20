---
id: QA-004
title: Zuverlässige Benachrichtigung
status: entwurf
typ: qualitaetsanforderung
quellen: [Gespräch mit dem Product Owner 2026-11-20]
verknuepft: [Z-002]
---

# QA-004: Zuverlässige Benachrichtigung

**Qualitätsmerkmal (ISO 25010):** Zuverlässigkeit (Fehlertoleranz)

## Szenario
Ein ausgelöstes Ereignis geht auch bei Neustart oder Fehlern eines Kanals nicht verloren und führt je Empfänger und Kanal zu höchstens einer Zustellung. Fehlgeschlagene Zustellungen werden mit Begrenzung wiederholt und auf einen Ersatzkanal (E-Mail) abgebildet.

## Messbar durch
Tests mit Neustart während des Versands; Zustellquote je Kanal im Protokoll ([Z-002](../01-ziele/Z-002-zuverlaessig-und-nachvollziehbar-benachrichtigen.md)).
