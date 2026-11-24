---
id: QA-009
title: Kostentransparenz
status: freigegeben
freigegeben-am: 2026-11-24
freigegeben-von: Product Owner
typ: qualitaetsanforderung
quellen: [Gespräch mit dem Product Owner 2026-11-20]
verknuepft: [Z-002]
---

# QA-009: Kostentransparenz

**Qualitätsmerkmal (ISO 25010):** Funktionale Eignung / Analysierbarkeit

## Szenario
Zu jedem kostenverursachenden Aufruf (E-Mail, Messenger, KI) existiert ein Posten mit Benutzer (ersatzweise Team), Auslöser, Anbieter, Zeitpunkt und Betrag. Die Summe je Benutzer/Team lässt sich in Einzelposten aufschlüsseln und auf die auslösende Aktion zurückführen.

## Messbar durch
Stichprobe: Für zehn zufällige Posten einer Anbieterabrechnung ist der Auslöser auffindbar; Summe der Posten = Anbieterrechnung ([RB-010](../07-randbedingungen/RB-010-kostenzuordnung.md)).
