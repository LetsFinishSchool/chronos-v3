---
id: QA-002
title: Nachvollziehbarkeit (Analysierbarkeit)
status: freigegeben
freigegeben-am: 2026-11-24
freigegeben-von: Product Owner
typ: qualitaetsanforderung
quellen: [Gespräch mit dem Product Owner 2026-11-20]
verknuepft: [Z-002, Z-005]
---

# QA-002: Nachvollziehbarkeit (Analysierbarkeit)

**Qualitätsmerkmal (ISO 25010):** Wartbarkeit (Analysierbarkeit)

## Szenario
Zu jeder Benachrichtigung ist ihr Auslöser ermittelbar, und der Weg eines Datums durch das System ist anhand von Logs und Protokoll in Minuten nachvollziehbar. Ereignisse und Datenfluss sind explizit, nicht implizit über Nebenwirkungen.

## Messbar durch
Stichprobe: ein beliebiger Push/E-Mail lässt sich auf Auslöser (Ereignis, Akteur, Zeitpunkt) zurückführen; Korrelations-ID durchgängig.
