---
id: QA-010
title: Benachrichtigungsbudget
status: freigegeben
freigegeben-am: 2026-11-24
freigegeben-von: Product Owner
typ: qualitaetsanforderung
quellen: [Gespräch mit dem Product Owner 2026-11-20]
verknuepft: [Z-009, Z-010]
---

# QA-010: Benachrichtigungsbudget

**Qualitätsmerkmal (ISO 25010):** Benutzbarkeit (Benutzerfehlerschutz, Vermeidung von Überlastung)

## Szenario
In der Standardeinstellung erhält eine Person je Woche höchstens doppelt so viele Benachrichtigungen (Push und E-Mail, alle Arten) wie sie Termine in dieser Woche hat. Das System plant Erinnerungen und Sammelmeldungen so, dass diese Grenze im Normalfall eingehalten wird; es gibt keine Laufzeitsperre. Eine Person kann mehr Benachrichtigungen einstellen.

## Messbar durch
Auswertung des Zustellprotokolls je Person und Woche (Anzahl Benachrichtigungen / Anzahl Termine).
